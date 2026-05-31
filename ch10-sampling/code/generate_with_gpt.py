"""
ch10 · 示例 2:把采样策略用在真 GPT 上
======================================
示例 1 在「固定打分」上讲清了原理。这里把同样的策略,装到第九章那个
真能背诗的小 GPT 上,看不同策略生成出来的**真实文字**有什么不同。

为自成一体,这里快速重训一个小 GPT(几秒),然后用同一个起头字,
分别以 greedy / 不同 temperature / top-k 各生成一段,直观对比"手感"。
"""
import torch
import torch.nn as nn
import torch.nn.functional as F

torch.manual_seed(1337)

TEXT = (
    "床前明月光，疑是地上霜。举头望明月，低头思故乡。\n"
    "春眠不觉晓，处处闻啼鸟。夜来风雨声，花落知多少。\n"
    "白日依山尽，黄河入海流。欲穷千里目，更上一层楼。\n"
    "锄禾日当午，汗滴禾下土。谁知盘中餐，粒粒皆辛苦。\n"
) * 4
chars = sorted(set(TEXT))
vocab_size = len(chars)
stoi = {c: i for i, c in enumerate(chars)}
itos = {i: c for i, c in enumerate(chars)}
data = torch.tensor([stoi[c] for c in TEXT], dtype=torch.long)
decode = lambda l: "".join(itos[i] for i in l)

block_size, batch_size = 32, 16
d_model, n_head, n_layer = 64, 4, 3


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
        return self.proj((att @ v).transpose(1, 2).contiguous().view(B, T, C))


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
    def __init__(self):
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
        loss = None if targets is None else F.cross_entropy(
            logits.view(-1, logits.size(-1)), targets.view(-1))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens, temperature=1.0, top_k=None, greedy=False):
        for _ in range(max_new_tokens):
            logits, _ = self(idx[:, -self.block_size:])
            logits = logits[:, -1, :]
            if greedy:
                nxt = logits.argmax(dim=-1, keepdim=True)        # 直接取最大
            else:
                logits = logits / temperature                    # 温度
                if top_k is not None:                            # top-k 截断
                    v, _ = torch.topk(logits, top_k)
                    logits[logits < v[:, [-1]]] = float("-inf")
                probs = F.softmax(logits, dim=-1)
                nxt = torch.multinomial(probs, num_samples=1)
            idx = torch.cat([idx, nxt], dim=1)
        return idx


# ---------- 快速训练 ----------
model = GPT()
opt = torch.optim.AdamW(model.parameters(), lr=3e-3)
for it in range(600):
    ix = torch.randint(0, len(data) - block_size - 1, (batch_size,))
    x = torch.stack([data[i:i + block_size] for i in ix])
    y = torch.stack([data[i + 1:i + 1 + block_size] for i in ix])
    _, loss = model(x, y)
    opt.zero_grad(); loss.backward(); opt.step()
print(f"训练完成,最终 loss = {loss.item():.3f}\n")

# ---------- 同一起头字,不同策略 ----------
seed = torch.tensor([[stoi["白"]]], dtype=torch.long)
N = 40
print("起头字「白」,各策略各生成 40 字:\n")
print("greedy(贪心,永远取最高分):")
print(" ", decode(model.generate(seed, N, greedy=True)[0].tolist()))
print("\ntemperature=0.3(低温,保守):")
print(" ", decode(model.generate(seed, N, temperature=0.3)[0].tolist()))
print("\ntemperature=1.0(原始分布):")
print(" ", decode(model.generate(seed, N, temperature=1.0)[0].tolist()))
print("\ntemperature=1.8(高温,放飞):")
print(" ", decode(model.generate(seed, N, temperature=1.8)[0].tolist()))
print("\ntop_k=5 + temperature=1.0(砍长尾):")
print(" ", decode(model.generate(seed, N, temperature=1.0, top_k=5)[0].tolist()))

print("""
小结:
  · greedy 和低温:几乎总能"背"出正确诗句,但毫无变化(这正是它确定的代价)。
  · 高温:开始出现串行、乱接别的诗句,甚至不通顺——给了冷门字太多机会。
  · top-k:砍掉长尾烂字后,即便配 T=1 也比纯高温稳得多。
  · 同一个训练好的模型,换采样策略就能在"严谨复述"和"自由发挥"之间滑动——
    这就是为什么 ChatGPT 这类产品会暴露 temperature / top-p 给你调。
""")
