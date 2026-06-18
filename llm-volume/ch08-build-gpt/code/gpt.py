"""
ch08 · 一个完整的、能跑的 GPT
==============================
前两章我们造好了积木:注意力(ch06)、Transformer Block(ch07)。
这一章把它们和「词嵌入 + 位置嵌入 + 输出头」串起来,搭出一个**完整的 GPT**。

数据在 GPT 里走过的全程(一句话的旅程):

   输入: 一串 token 编号  (B, T)
     │
     ├─ 词嵌入   token → 含义向量      (查 ch05 那张表)
     ├─ 位置嵌入 位置   → 座位号向量    (可学习版位置编码,ch07)
     │   两者相加 → x  (B, T, C)
     │
     ├─ N 个 Transformer Block 依次加工  (ch07 的积木,堆 N 层)
     │
     ├─ 末尾再来一次 LayerNorm
     │
     └─ 输出头(Linear → 词表大小)
         得到 logits (B, T, vocab):每个位置,对"下一个字是谁"的打分

本文件就是把这条流水线用 PyTorch 写出来,并:
  1) 跑一次前向,确认形状对、能算 loss;
  2) 用未训练的模型生成几个字(只验证「管道通」,内容当然是乱的)。
"""
import torch
import torch.nn as nn
import torch.nn.functional as F

torch.manual_seed(0)


# ============ ch06/ch07 的积木(原样搬过来,自成一体) ============
class CausalSelfAttention(nn.Module):
    def __init__(self, d_model, n_head):
        super().__init__()
        self.n_head = n_head
        self.d_k = d_model // n_head
        self.qkv = nn.Linear(d_model, 3 * d_model, bias=False)
        self.proj = nn.Linear(d_model, d_model, bias=False)

    def forward(self, x):
        B, T, C = x.shape
        q, k, v = self.qkv(x).split(C, dim=2)
        q = q.view(B, T, self.n_head, self.d_k).transpose(1, 2)
        k = k.view(B, T, self.n_head, self.d_k).transpose(1, 2)
        v = v.view(B, T, self.n_head, self.d_k).transpose(1, 2)
        att = (q @ k.transpose(-2, -1)) / (self.d_k ** 0.5)
        mask = torch.tril(torch.ones(T, T, dtype=torch.bool, device=x.device))
        att = att.masked_fill(~mask, float("-inf")).softmax(dim=-1)
        y = (att @ v).transpose(1, 2).contiguous().view(B, T, C)
        return self.proj(y)


class Block(nn.Module):
    def __init__(self, d_model, n_head):
        super().__init__()
        self.ln1 = nn.LayerNorm(d_model)
        self.attn = CausalSelfAttention(d_model, n_head)
        self.ln2 = nn.LayerNorm(d_model)
        self.ff = nn.Sequential(
            nn.Linear(d_model, 4 * d_model), nn.GELU(),
            nn.Linear(4 * d_model, d_model),
        )

    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.ff(self.ln2(x))
        return x


# ============ 完整的 GPT ============
class GPT(nn.Module):
    def __init__(self, vocab_size, block_size, d_model=64, n_head=4, n_layer=3):
        super().__init__()
        self.block_size = block_size                       # 一次最多看多少个词
        self.tok_emb = nn.Embedding(vocab_size, d_model)   # 词嵌入表
        self.pos_emb = nn.Embedding(block_size, d_model)   # 位置嵌入表(可学习)
        self.blocks = nn.ModuleList([Block(d_model, n_head) for _ in range(n_layer)])
        self.ln_f = nn.LayerNorm(d_model)                  # 末尾 LayerNorm
        self.head = nn.Linear(d_model, vocab_size, bias=False)  # 输出头 -> 词表打分

    def forward(self, idx, targets=None):
        B, T = idx.shape
        assert T <= self.block_size, "序列长度超过 block_size"
        pos = torch.arange(T, device=idx.device)
        x = self.tok_emb(idx) + self.pos_emb(pos)          # (B,T,C):词义 + 位置
        for blk in self.blocks:
            x = blk(x)
        x = self.ln_f(x)
        logits = self.head(x)                              # (B,T,vocab):下一字打分
        loss = None
        if targets is not None:
            # 把 (B,T,vocab) 摊平成 (B*T, vocab),和标签算交叉熵
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)),
                                   targets.view(-1))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens):
        """自回归生成:每次拿最后一步的 logits 采样一个字,接到末尾,再喂回去。"""
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.block_size:]           # 只保留最近 block_size 个
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :]                      # 只要最后一个位置 (B,vocab)
            probs = F.softmax(logits, dim=-1)
            nxt = torch.multinomial(probs, num_samples=1)  # 按概率采样下一个字
            idx = torch.cat([idx, nxt], dim=1)
        return idx


if __name__ == "__main__":
    # ---------- 配一个小 GPT ----------
    vocab_size, block_size = 65, 16
    model = GPT(vocab_size, block_size, d_model=64, n_head=4, n_layer=3)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"模型配置: vocab={vocab_size} block_size={block_size} d_model=64 head=4 layer=3")
    print(f"总参数量: {n_params:,}")

    # ---------- 前向一次:看形状、看 loss ----------
    B, T = 2, 16
    idx = torch.randint(0, vocab_size, (B, T))
    targets = torch.randint(0, vocab_size, (B, T))
    logits, loss = model(idx, targets)
    print(f"\n输入  idx 形状: {tuple(idx.shape)}")
    print(f"输出  logits 形状: {tuple(logits.shape)} = (批量, 词数, 词表大小)")
    print(f"初始 loss: {loss.item():.3f}")
    print(f"理论参考 ln(vocab) = ln({vocab_size}) = {torch.log(torch.tensor(float(vocab_size))).item():.3f}")
    print("-> 未训练时,模型是「瞎猜」,loss 应接近 ln(词表大小)。两者接近 = 管道没问题。")

    # ---------- 生成几个字(未训练,内容必然是乱的)----------
    start = torch.zeros((1, 1), dtype=torch.long)   # 从编号 0 这个字起头
    out = model.generate(start, max_new_tokens=12)
    print(f"\n从未训练模型生成 12 个 token 编号(只验证管道,内容是乱的):")
    print(out[0].tolist())

    print("""
小结:
  · 完整 GPT = 词嵌入 + 位置嵌入 → N×Block → 末尾 LayerNorm → 输出头(到词表)。
  · 前向输出 logits (B,T,vocab):每个位置对「下一个字是谁」的打分。
  · 训练目标:logits 和「真正的下一个字」算交叉熵 loss。未训练时 loss≈ln(vocab),正是瞎猜水平。
  · generate:自回归——每步采一个字、接回末尾、再喂进去,如此滚动生成。
  · 现在「能跑」但「不会说话」(参数随机)。下一章就用真实语料训练它,让 loss 降下去。
""")
