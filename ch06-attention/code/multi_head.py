"""
ch06 · 示例 4:多头注意力(multi-head)—— 多个视角一起看
=====================================================
单头注意力只有一套 Wq/Wk/Wv,只能学会「一种关注方式」。
可一句话里,词与词的关系是多种多样的:
    · 有的头可能专门盯「主语—谓语」          (我 ← 吃)
    · 有的头可能专门盯「动词—宾语」          (吃 → 苹果)
    · 有的头可能盯「相邻词」「指代」……

与其逼一套矩阵学会所有关系,不如准备好几套(几个「头」),各看各的,
最后把每个头的结果拼接(concat)起来,再过一个输出矩阵融合。这就是多头注意力。

要点:总维度 d_model 被「切」给各头。比如 d_model=4、2 个头,
每个头分到 d_k = 2 维。所以多头不是更贵,而是把同样的维度「分工」使用。
"""
import numpy as np

np.set_printoptions(precision=3, suppress=True)
rng = np.random.default_rng(42)

WORDS = ["我", "吃", "苹果", "了"]
X = np.array([
    [1.0, 0.0, 0.2, 0.1],
    [0.2, 1.0, 0.1, 0.0],
    [0.3, 0.8, 0.9, 0.2],
    [0.0, 0.1, 0.0, 1.0],
])
n, d_model = X.shape
H = 2                    # 头数
d_k = d_model // H       # 每个头分到的维度 = 4 // 2 = 2

def softmax_rows(M):
    e = np.exp(M - M.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)

def one_head(X, Wq, Wk, Wv, mask=None):
    """一个头的因果自注意力。"""
    Q, K, V = X @ Wq, X @ Wk, X @ Wv
    scores = (Q @ K.T) / np.sqrt(Q.shape[1])
    if mask is not None:
        scores = np.where(mask, scores, -np.inf)
    W = softmax_rows(scores)
    return W @ V, W

mask = np.tril(np.ones((n, n), dtype=bool))   # 仍带因果掩码

# ---------- 为每个头各造一套 Wq/Wk/Wv,每套把 4 维投到 2 维 ----------
heads_out, heads_w = [], []
for h in range(H):
    Wq = rng.standard_normal((d_model, d_k))
    Wk = rng.standard_normal((d_model, d_k))
    Wv = rng.standard_normal((d_model, d_k))
    out, W = one_head(X, Wq, Wk, Wv, mask)
    heads_out.append(out)
    heads_w.append(W)
    print(f"第 {h} 个头的注意力权重 W{h}(各看各的):\n", W, "\n")

# ---------- 拼接各头输出:(n, d_k) × H -> (n, d_model) ----------
concat = np.concatenate(heads_out, axis=1)
print("拼接后 concat 形状:", concat.shape, "(回到 d_model =", d_model, ")")
print(concat)

# ---------- 再过一个输出投影 Wo,融合各头信息 ----------
Wo = rng.standard_normal((d_model, d_model))
Y = concat @ Wo
print("\n多头注意力最终输出 Y = concat · Wo:\n", Y)

# ---------- 对比:两个头「关注点」确实不同 ----------
i = WORDS.index("苹果")
print(f"\n『苹果』在两个头里的关注分配(看,它们不一样):")
for h in range(H):
    row = " ".join(f"{WORDS[j]}={heads_w[h][i][j]:.2f}" for j in range(n))
    print(f"  头{h}: {row}")

print(f"""
小结:
  · 多头 = 准备 H 套独立的 Wq/Wk/Wv,各自做一遍(带掩码的)自注意力。
  · 维度分工:d_model={d_model} 切成 H={H} 份,每头 d_k={d_k}。多头≈同样开销、多种视角。
  · 各头输出拼接回 d_model,再过输出矩阵 Wo 融合 -> 最终结果。
  · 上面两个头对『苹果』给出的权重明显不同,说明它们确实学到了不同的关注模式。
  · 这就是 Transformer 的核心积木。下一章把它和「位置编码 + 残差 + LayerNorm + FFN」
    拼成一个完整的 Transformer Block。
""")
