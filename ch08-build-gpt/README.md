# 第八章 · 搭出完整的 GPT

> 积木都齐了:注意力(第六章)、Transformer Block(第七章)。这一章把它们和
> **词嵌入 + 位置嵌入 + 输出头** 串起来,搭出一个**完整的、能跑的 GPT**。
>
> 这一章结束时,你会有一个真正的 GPT 类:能前向、能算 loss、能生成。只差「训练」——
> 那是下一章的事。现在它「能跑」但还「不会说话」(参数是随机的)。

---

## 1. 一句话在 GPT 里的全程旅程

先看数据怎么从「一串编号」变成「对下一个字的打分」:

```text
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
      得到 logits (B, T, vocab):每个位置,对「下一个字是谁」的打分
```

整个 GPT,本质上就是这条流水线。下面逐段看代码。

---

## 2. 输入端:词嵌入 + 位置嵌入

GPT 的第一步,把 token 编号变成向量,并掺入位置信息。注意这里位置用的是**可学习**的
`nn.Embedding`(而非第七章的 sin/cos 固定版)——GPT 系列都这么做。

```python
self.tok_emb = nn.Embedding(vocab_size, d_model)   # 词嵌入表
self.pos_emb = nn.Embedding(block_size, d_model)   # 位置嵌入表(可学习)
...
pos = torch.arange(T, device=idx.device)
x = self.tok_emb(idx) + self.pos_emb(pos)          # (B,T,C):词义 + 位置
```

`block_size` 是模型一次最多能看的词数(上下文窗口)。位置嵌入表只有 `block_size` 行,
所以输入长度不能超过它。

---

## 3. 主干:N 层 Transformer Block + 输出头

中间叠 N 块第七章的 Block,末尾做一次 LayerNorm,再用一个线性层把每个位置的向量
投影到「词表大小」维——这就是对**下一个字**的打分(logits)。

```python
class GPT(nn.Module):
    def __init__(self, vocab_size, block_size, d_model=64, n_head=4, n_layer=3):
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
        x = self.ln_f(x)
        logits = self.head(x)                       # (B,T,vocab)
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)),
                                   targets.view(-1))
        return logits, loss
```

> 代码见 [`code/gpt.py`](code/gpt.py)(注意力和 Block 的实现也在同一文件里,自成一体)

**怎么算 loss?** 每个位置都该预测「它后面那个真实的字」。把 logits 摊平成 `(B*T, vocab)`,
和真实标签做**交叉熵**就行——这和第三章 bigram 的训练目标是一脉相承的,只是模型强大多了。

---

## 4. 生成:自回归(autoregressive)

GPT 怎么写字?**一次一个字,滚动着来**:拿当前序列算 logits,只取最后一个位置的打分,
按概率采样出下一个字,接到末尾,再把新序列喂回去。如此往复。

```python
@torch.no_grad()
def generate(self, idx, max_new_tokens):
    for _ in range(max_new_tokens):
        idx_cond = idx[:, -self.block_size:]   # 只保留最近 block_size 个
        logits, _ = self(idx_cond)
        logits = logits[:, -1, :]              # 只要最后一个位置
        probs = F.softmax(logits, dim=-1)
        nxt = torch.multinomial(probs, num_samples=1)
        idx = torch.cat([idx, nxt], dim=1)
    return idx
```

注意 `idx[:, -self.block_size:]`:序列再长,也只把最近 `block_size` 个字喂进去——
因为位置嵌入表就那么大。

---

## 5. 跑一次:确认「管道通了」

配一个小 GPT(`d_model=64, head=4, layer=3`),前向一次,再用未训练的模型生成几个字:

```text
模型配置: vocab=65 block_size=16 d_model=64 head=4 layer=3
总参数量: 158,656

输入  idx 形状: (2, 16)
输出  logits 形状: (2, 16, 65) = (批量, 词数, 词表大小)
初始 loss: 4.429
理论参考 ln(vocab) = ln(65) = 4.174
-> 未训练时,模型是「瞎猜」,loss 应接近 ln(词表大小)。两者接近 = 管道没问题。

从未训练模型生成 12 个 token 编号(只验证管道,内容是乱的):
[0, 23, 21, 53, 45, 64, 43, 1, 50, 13, 23, 9, 11]
```

**为什么初始 loss ≈ ln(vocab)?** 没训练的模型对 65 个字毫无偏好,等于均匀瞎猜,
交叉熵正好是 `ln(65) ≈ 4.174`。我们实测 4.429,非常接近——说明前向、loss、形状全都对。
生成的编号当然是乱的(参数随机),但**整条流水线已经跑通了**。

---

## 动手跑一跑

```bash
cd ch08-build-gpt/code
python3 gpt.py     # 配置模型 → 前向看形状/loss → 生成验证管道
```

需要 PyTorch。`gpt.py` 里的 `GPT` 类下一章会直接拿来训练。

---

## 本章小结

- **完整 GPT** = 词嵌入 + 位置嵌入 → `N × TransformerBlock` → 末尾 LayerNorm → 输出头(投影到词表)。
- **位置嵌入**用可学习的 `nn.Embedding`(GPT 风格),`block_size` 决定上下文窗口大小。
- **输出 logits** `(B,T,vocab)`:每个位置对「下一个字是谁」的打分;和真实下一字算**交叉熵**即得 loss。
- **未训练时 loss ≈ ln(vocab)**,正是均匀瞎猜的水平——可用它快速判断「管道是否搭对」。
- **生成是自回归的**:每步采一个字、接回末尾、再喂进去,滚动产出;输入永远截到最近 `block_size` 个。
- 现在模型「能跑」但「不会说话」。下一章用真实语料训练,让 loss 降下去,看它**学会写字**。

---

上一章 ← [第七章 · Transformer Block](../ch07-transformer-block/README.md) ｜ 下一章 → [第九章 · 训练你的 GPT](../ch09-train-gpt/README.md)
