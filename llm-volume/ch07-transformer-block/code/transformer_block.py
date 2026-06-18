"""
ch07 · 示例 3:组装一个完整的 Transformer Block
================================================
材料都备齐了,现在把它们拼成 GPT 的标准积木——一个 Transformer Block。
一块 Block 里有两个子层,每个都用「Pre-LN + 残差」包起来:

    x = x + 注意力( LayerNorm(x) )       # 子层一:词之间互相看(混合信息)
    x = x + 前馈网络( LayerNorm(x) )      # 子层二:每个词各自深加工

  · 注意力(上一章那块):负责让词与词之间交换信息。
  · 前馈网络 FFN:一个「先放大、过激活、再缩回」的小 MLP,
    对每个词的向量单独做非线性加工(注意力只是加权平均,本身是线性的,
    需要 FFN 来提供非线性表达力)。常见放大倍数是 4 倍。

输入输出都是 (B, T, C) 同形状 —— 所以 Block 可以一个接一个叠 N 层,
叠出来的就是 GPT 的主干。下一章我们就这么干。
"""
import torch
import torch.nn as nn

torch.manual_seed(0)


class CausalSelfAttention(nn.Module):
    """带因果掩码的多头自注意力(与第六章一致)。"""
    def __init__(self, d_model, n_head):
        super().__init__()
        assert d_model % n_head == 0
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


class FeedForward(nn.Module):
    """逐词的前馈网络:先放大 4 倍、过 GELU、再缩回。提供非线性。"""
    def __init__(self, d_model, mult=4):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, mult * d_model),
            nn.GELU(),
            nn.Linear(mult * d_model, d_model),
        )

    def forward(self, x):
        return self.net(x)


class TransformerBlock(nn.Module):
    """一块标准 Block:Pre-LN + 残差,包住「注意力」和「前馈」两个子层。"""
    def __init__(self, d_model, n_head):
        super().__init__()
        self.ln1 = nn.LayerNorm(d_model)
        self.attn = CausalSelfAttention(d_model, n_head)
        self.ln2 = nn.LayerNorm(d_model)
        self.ff = FeedForward(d_model)

    def forward(self, x):
        x = x + self.attn(self.ln1(x))   # 子层一:词间信息交换
        x = x + self.ff(self.ln2(x))     # 子层二:逐词非线性加工
        return x


# ---------- 跑一块 Block 看形状 ----------
B, T, C, H = 2, 5, 16, 4     # 2 句话、每句 5 词、每词 16 维、4 个头
x = torch.randn(B, T, C)
block = TransformerBlock(C, H)
y = block(x)

print("输入  x 形状:", tuple(x.shape))
print("输出  y 形状:", tuple(y.shape), "(与输入完全一致 -> 可以无限叠)")
n_params = sum(p.numel() for p in block.parameters())
print("这一块 Block 的参数量:", n_params)

# ---------- 叠 3 块:证明它真能堆叠 ----------
stack = nn.Sequential(*[TransformerBlock(C, H) for _ in range(3)])
y3 = stack(x)
print("\n叠 3 块后输出形状:", tuple(y3.shape), "(还是 (B,T,C),稳得很)")

# ---------- 验证残差确实「保底」:把子层权重清零,Block 应近似恒等 ----------
with torch.no_grad():
    for p in block.parameters():
        p.zero_()
    # LayerNorm 的 γ 被清零会把信号也清掉,这里只看「残差通路」存在性:
    # 当两个子层输出都为 0 时,x = x + 0 + 0 = x
y_identity = block(x)
print("\n把两个子层输出都置零后,Block 是否≈恒等(输出≈输入):",
      torch.allclose(y_identity, x, atol=1e-4))

print("""
小结:
  · Transformer Block = 两个子层:① 因果多头注意力(词间交换信息)② 前馈网络(逐词非线性)。
  · 每个子层都用 Pre-LN + 残差包裹:x = x + sublayer(LayerNorm(x))。
  · FFN 先放大 4 倍再缩回,补上注意力缺的非线性表达力。
  · 输入输出同为 (B,T,C),所以 Block 能一层层叠 —— 叠 N 层就是 GPT 主干。
  · 残差让「子层不发力时 Block≈恒等」,深网络因此好训:上面置零实验印证了这一点。
""")
