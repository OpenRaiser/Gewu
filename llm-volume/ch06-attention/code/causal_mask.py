"""
ch06 · 示例 3:因果掩码(causal mask)—— 不许偷看未来
==================================================
语言模型在做一件事:看着前面的词,猜下一个词。
那训练 / 生成时就有一条铁律:第 i 个词只能看 第 0..i 个词,
绝不能看到它「后面」的词——否则就是抄答案(标签泄露)。

可上一节的注意力是「每个词看所有词」,包括后面的。怎么挡住未来?
办法极简单:打分之后、softmax 之前,把「未来位置」的分数设成 -∞。
e^(-∞) = 0,softmax 后这些位置权重正好为 0,等于没看见。

这一步加上去,self-attention 就变成了 GPT 用的「带因果掩码的自注意力」。
"""
import numpy as np

np.set_printoptions(precision=3, suppress=True)
rng = np.random.default_rng(0)

WORDS = ["我", "吃", "苹果", "了"]
X = np.array([
    [1.0, 0.0, 0.2, 0.1],
    [0.2, 1.0, 0.1, 0.0],
    [0.3, 0.8, 0.9, 0.2],
    [0.0, 0.1, 0.0, 1.0],
])
n, d_model = X.shape
d_k = 3
Wq = rng.standard_normal((d_model, d_k))
Wk = rng.standard_normal((d_model, d_k))
Wv = rng.standard_normal((d_model, d_k))

def softmax(v):
    e = np.exp(v - v.max())
    return e / e.sum()

Q, K, V = X @ Wq, X @ Wk, X @ Wv
scores = (Q @ K.T) / np.sqrt(d_k)
print("打分(未掩码)scores:\n", scores)

# ---------- 造一张「下三角」掩码 ----------
# mask[i,j] = True 表示「第 i 词可以看第 j 词」,只允许 j <= i(看自己和前面)。
mask = np.tril(np.ones((n, n), dtype=bool))
print("\n因果掩码 mask(True=可看;下三角):\n", mask)

# ---------- 把未来位置(mask=False)的分数设成 -∞ ----------
masked = np.where(mask, scores, -np.inf)
print("\n掩码后的分数(未来位置 = -inf):\n", masked)

# ---------- softmax:-inf 自动变 0 权重 ----------
weights = np.array([softmax(row) for row in masked])
print("\n掩码后的注意力权重(上三角全为 0):\n", weights)

Y = weights @ V
print("\n输出 Y = weights · V:\n", Y)

# ---------- 逐词看「它能看到谁」 ----------
print("\n每个词的注意力分配(0 = 看不见):")
for i, w in enumerate(WORDS):
    row = " ".join(f"{WORDS[j]}={weights[i][j]:.2f}" for j in range(n))
    print(f"  第{i}词 {w:<3} -> {row}")

print(f"""
小结:
  · 因果掩码 = 一张下三角布尔表:第 i 词只许看 0..i,看不到未来。
  · 实现:打分后把未来位置设 -∞,softmax 后这些位置权重恰为 0。
  · 看权重矩阵:右上三角全是 0.00,说明「偷看未来」被彻底堵死。
  · 第 0 个词『{WORDS[0]}』只能看自己(权重 1.0);越往后能看的越多。
  · 有了它,模型才能在「不知道答案」的前提下学习猜下一个词——这正是 GPT 的训练方式。
""")
