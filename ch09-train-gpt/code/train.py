"""
ch09 · 训练你的 GPT —— 让 loss 真的降下去
==========================================
上一章的 GPT「能跑但不会说话」(参数随机)。这一章给它喂真实文字,
用梯度下降反复调参,亲眼看着:
    · loss 从「瞎猜水平 ln(vocab)」一路下降;
    · 生成的文字从「乱码」逐渐变成「像那么回事」。

为了能在普通电脑上几十秒跑完,我们用一段**很小的中文语料**(几首古诗),
模型也很小。小数据 + 小模型,目标是让你**看清训练这件事本身**,
而不是训出一个真能用的模型。原理和训练 GPT-4 完全一样,只是规模差了上亿倍。
"""
import torch
import torch.nn as nn
import torch.nn.functional as F

torch.manual_seed(1337)

# ---------- 语料:几首耳熟能详的古诗(字符级)----------
TEXT = (
    "床前明月光，疑是地上霜。举头望明月，低头思故乡。\n"
    "春眠不觉晓，处处闻啼鸟。夜来风雨声，花落知多少。\n"
    "白日依山尽，黄河入海流。欲穷千里目，更上一层楼。\n"
    "锄禾日当午，汗滴禾下土。谁知盘中餐，粒粒皆辛苦。\n"
) * 4   # 重复几遍,让小模型有机会学会

# ---------- 字符级词表:每个不同的字 = 一个编号 ----------
chars = sorted(set(TEXT))
vocab_size = len(chars)
stoi = {c: i for i, c in enumerate(chars)}
itos = {i: c for i, c in enumerate(chars)}
encode = lambda s: [stoi[c] for c in s]
decode = lambda l: "".join(itos[i] for i in l)

data = torch.tensor(encode(TEXT), dtype=torch.long)
print(f"语料总字数: {len(TEXT)}  不同字数(词表): {vocab_size}")
print(f"前 24 个字: {TEXT[:24]}")

# ---------- 超参数 ----------
block_size = 32      # 上下文窗口
batch_size = 16
d_model, n_head, n_layer = 64, 4, 3
n_iters = 600
eval_every = 100


def get_batch():
    """随机切 batch_size 段长 block_size 的片段;y 是 x 右移一位(下一个字)。"""
    ix = torch.randint(0, len(data) - block_size - 1, (batch_size,))
    x = torch.stack([data[i:i + block_size] for i in ix])
    y = torch.stack([data[i + 1:i + 1 + block_size] for i in ix])
    return x, y


# ============ 模型(与 ch08 一致,精简内联) ============
class CausalSelfAttention(nn.Module):
    def __init__(self, d_model, n_head):
        super().__init__()
        self.n_head, self.d_k = n_head, d_model // n_head
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
        self.ff = nn.Sequential(nn.Linear(d_model, 4 * d_model), nn.GELU(),
                                nn.Linear(4 * d_model, d_model))

    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.ff(self.ln2(x))
        return x


class GPT(nn.Module):
    def __init__(self, vocab_size, block_size, d_model, n_head, n_layer):
        super().__init__()
        self.block_size = block_size
        self.tok_emb = nn.Embedding(vocab_size, d_model)
        self.pos_emb = nn.Embedding(block_size, d_model)
        self.blocks = nn.ModuleList([Block(d_model, n_head) for _ in range(n_layer)])
        self.ln_f = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, vocab_size, bias=False)

    def forward(self, idx, targets=None):
        B, T = idx.shape
        pos = torch.arange(T, device=idx.device)
        x = self.tok_emb(idx) + self.pos_emb(pos)
        for blk in self.blocks:
            x = blk(x)
        logits = self.head(self.ln_f(x))
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens):
        for _ in range(max_new_tokens):
            logits, _ = self(idx[:, -self.block_size:])
            probs = F.softmax(logits[:, -1, :], dim=-1)
            nxt = torch.multinomial(probs, num_samples=1)
            idx = torch.cat([idx, nxt], dim=1)
        return idx


model = GPT(vocab_size, block_size, d_model, n_head, n_layer)
opt = torch.optim.AdamW(model.parameters(), lr=3e-3)
print(f"参数量: {sum(p.numel() for p in model.parameters()):,}\n")

# ---------- 训练前先生成一段(必然是乱码)----------
seed = torch.tensor([[stoi["床"]]], dtype=torch.long)
print("【训练前】生成:", decode(model.generate(seed, 40)[0].tolist()))
print()

# ============ 训练循环 ============
print("开始训练(看 loss 往下走):")
for it in range(1, n_iters + 1):
    x, y = get_batch()
    _, loss = model(x, y)
    opt.zero_grad()
    loss.backward()
    opt.step()
    if it % eval_every == 0 or it == 1:
        print(f"  第 {it:>4} 步  loss = {loss.item():.3f}")

# ---------- 训练后再生成,对比 ----------
print("\n【训练后】从『床』字续写:")
print(" ", decode(model.generate(seed, 48)[0].tolist()))
print("\n【训练后】从『春』字续写:")
seed2 = torch.tensor([[stoi["春"]]], dtype=torch.long)
print(" ", decode(model.generate(seed2, 48)[0].tolist()))

print("""
小结:
  · 训练 = 反复 (取 batch → 前向算 loss → 反向求梯度 → 优化器挪一步)。
  · 数据构造:x 是一段文字,y 是它右移一位(每个位置的标签 = 下一个字)。
  · loss 从 ln(vocab) 附近一路下降,说明模型从「瞎猜」逐渐学会了语料的规律。
  · 生成对比最直观:训练前是乱码,训练后能背出诗句(小数据下偏「记住」)。
  · 真实大模型:同样的循环,只是数据是整个互联网、参数上千亿、训练几个月。原理一模一样。
""")
