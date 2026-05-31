"""
ch06 · 示例 2:自注意力(self-attention)的真身 —— Q / K / V
========================================================
上一节的缺陷:相关度直接用「原始向量点积」,每个词只能用「原本的样子」去匹配。
可一个词其实身兼数职:
    · 作为「提问的人」:我在找什么样的上下文?      —— 这叫 Query(查询)
    · 作为「被查的人」:我能提供什么样的标签?      —— 这叫 Key(键)
    · 真要取用时,我交出什么内容?                 —— 这叫 Value(值)

把同一个词向量,分别乘上三张不同的权重矩阵 Wq / Wk / Wv,
就得到它的 Q、K、V 三副面孔。注意力据此分工:
    用我的 Q 去和别人的 K 点积  ->  算出该关注谁(打分)
    再拿这些分数,加权汇总别人的 V  ->  得到我的新表示

这就是 Transformer 里那行著名公式:
    Attention(Q,K,V) = softmax( Q·Kᵀ / √d_k ) · V
"""
import numpy as np

np.set_printoptions(precision=3, suppress=True)
rng = np.random.default_rng(0)   # 固定随机种子,保证每次结果一致

WORDS = ["我", "吃", "苹果", "了"]
# 原始词向量(d_model = 4 维),仍假装是查表得到的
X = np.array([
    [1.0, 0.0, 0.2, 0.1],   # 我
    [0.2, 1.0, 0.1, 0.0],   # 吃
    [0.3, 0.8, 0.9, 0.2],   # 苹果
    [0.0, 0.1, 0.0, 1.0],   # 了
])
n, d_model = X.shape
d_k = 3   # Q/K/V 的维度(可以和 d_model 不同)

# ---------- 第 1 步:造出三张投影矩阵 Wq / Wk / Wv ----------
# 真实模型里这三张是「学出来的参数」,这里先用随机数代替,看清流程即可。
Wq = rng.standard_normal((d_model, d_k))
Wk = rng.standard_normal((d_model, d_k))
Wv = rng.standard_normal((d_model, d_k))

# ---------- 第 2 步:把每个词投影出 Q、K、V 三副面孔 ----------
Q = X @ Wq    # (4, 3):每个词「我在找什么」
K = X @ Wk    # (4, 3):每个词「我能提供什么标签」
V = X @ Wv    # (4, 3):每个词「真要取用时交出的内容」
print("Q(查询,每行一个词):\n", Q)
print("\nK(键):\n", K)
print("\nV(值):\n", V)

# ---------- 第 3 步:打分 = Q · Kᵀ ----------
scores = Q @ K.T   # (4,4):scores[i,j] = 第 i 词的 Q 与 第 j 词的 K 的契合度
print("\n原始打分 scores = Q·Kᵀ:\n", scores)

# ---------- 第 4 步:缩放(scaled)----------
# d_k 越大,点积的数值越容易变大,softmax 会变得「非0即1」太极端。
# 除以 √d_k 把数值拉回温和区间,梯度才稳。这就是「scaled」的由来。
scaled = scores / np.sqrt(d_k)
print(f"\n缩放后 scores / √{d_k}:\n", scaled)

# ---------- 第 5 步:softmax 成权重 ----------
def softmax(v):
    e = np.exp(v - v.max())
    return e / e.sum()

weights = np.array([softmax(row) for row in scaled])
print("\n注意力权重 weights(每行 softmax,和为 1):\n", weights)

# ---------- 第 6 步:加权汇总 V,得到新表示 ----------
Y = weights @ V    # (4, 3)
print("\n输出 Y = weights · V(每个词的带上下文新表示):\n", Y)

# ---------- 把整套流程打包成一个函数 ----------
def attention(X, Wq, Wk, Wv):
    Q, K, V = X @ Wq, X @ Wk, X @ Wv
    d_k = Q.shape[1]
    scores = (Q @ K.T) / np.sqrt(d_k)
    W = np.array([softmax(r) for r in scores])
    return W @ V

Y2 = attention(X, Wq, Wk, Wv)
print("\n用打包函数复算,结果一致:", np.allclose(Y, Y2))

# ---------- 看『苹果』这一行的注意力分配 ----------
i = WORDS.index("苹果")
print(f"\n『苹果』的注意力权重(用它的 Q 去问每个词的 K):")
for w, p in zip(WORDS, weights[i]):
    bar = "█" * int(p * 30)
    print(f"  {w:<3} {p:.3f} {bar}")

print("""
小结:
  · Q/K/V = 同一个词向量,过三张不同矩阵,得到三副面孔(查询/键/值)。
  · 打分用 Q·Kᵀ:我的「问」去碰你的「答」,比直接点积更灵活——
    因为 Wq、Wk 不同,词可以「用一种样子去问、用另一种样子被查」。
  · √d_k 缩放:防止维度一大,点积数值爆炸、softmax 过度极端。
  · softmax 归一 -> 加权汇总 V -> 新表示。这就是 self-attention 的全部。
  · 这里 Wq/Wk/Wv 是随机的;真实模型里它们由训练学出,自动学会「该关注谁」。
""")
