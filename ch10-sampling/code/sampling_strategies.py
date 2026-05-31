"""
ch10 · 示例 1:采样策略 —— 从一堆打分里「挑下一个字」
====================================================
模型每一步吐出的是 logits:对词表里每个字的打分。
怎么把打分变成「选定的那一个字」?这一步叫**采样(sampling)**,
它不改变模型,却深刻影响生成的风格:是死板复读,还是灵动多样。

本示例用一个**固定的打分向量**(假装模型对 6 个候选字的打分),
把四种最常见的策略摊开看清楚:
    · greedy   :永远选分最高的(最保守,会复读)
    · temperature:调"胆量"——高温更随机,低温更稳
    · top-k    :只在分数最高的 k 个里挑
    · top-p    :只在"累计概率达到 p"的最小集合里挑(核采样)
"""
import numpy as np

np.set_printoptions(precision=3, suppress=True)

VOCAB = ["月", "光", "霜", "鸟", "风", "x"]   # 6 个候选字(x 代表生僻/不通顺)
logits = np.array([3.0, 2.5, 1.0, 0.5, 0.2, -2.0])   # 模型给的打分(假数据)


def softmax(z):
    e = np.exp(z - z.max())
    return e / e.sum()


def show(probs, title):
    print(f"\n{title}")
    for w, p in zip(VOCAB, probs):
        bar = "█" * int(p * 40)
        flag = "" if p > 0 else "  <- 被排除(概率=0)"
        print(f"  {w}  {p:.3f} {bar}{flag}")


# ---------- 0. 原始概率 ----------
base = softmax(logits)
show(base, "原始概率 softmax(logits):")

# ---------- 1. greedy:直接取最大 ----------
print("\ngreedy(贪心):argmax =", VOCAB[int(np.argmax(logits))],
      "-> 永远选它,完全确定,但容易陷入复读。")

# ---------- 2. temperature:除以温度再 softmax ----------
# logits / T:T<1 拉大差距(更尖锐、更保守);T>1 拉平(更随机、更冒险)。
for T in [0.5, 1.0, 1.5]:
    show(softmax(logits / T), f"temperature = {T}  (logits/T 再 softmax):")
print("\n-> 温度越低越尖(押注高分字);越高越平(给冷门字机会)。T=1 即原始分布。")

# ---------- 3. top-k:只保留分数最高的 k 个,其余清零 ----------
def top_k(logits, k):
    z = logits.copy()
    keep = np.argsort(z)[-k:]               # 分数最高的 k 个下标
    mask = np.ones_like(z, dtype=bool)
    mask[keep] = False
    z[mask] = -np.inf                       # 其余设 -inf -> softmax 后为 0
    return softmax(z)

show(top_k(logits, 3), "top-k = 3  (只在前 3 名里采样):")
print("-> 砍掉长尾,杜绝偶尔蹦出的离谱字;k 越小越保守。")

# ---------- 4. top-p(核采样):按概率从高到低累加,够 p 就停 ----------
def top_p(logits, p):
    probs = softmax(logits)
    order = np.argsort(probs)[::-1]         # 概率从高到低排序的下标
    csum = np.cumsum(probs[order])
    # 找到「累计刚好 >= p」的位置,保留到这里为止
    cut = np.searchsorted(csum, p) + 1
    keep = order[:cut]
    out = np.zeros_like(probs)
    out[keep] = probs[keep]
    return out / out.sum()                  # 重新归一

show(top_p(logits, 0.9), "top-p = 0.9  (累计概率达 0.9 的最小集合):")
print("-> 候选集大小随场景自适应:模型很确定时集合小,模型犹豫时集合大。")

# ---------- 实采样:同一分布连采 12 次,看差异 ----------
rng = np.random.default_rng(0)
def sample_n(probs, n=12):
    idx = rng.choice(len(VOCAB), size=n, p=probs)
    return "".join(VOCAB[i] for i in idx)

print("\n连采 12 次对比同一起点不同策略的'手感':")
print("  原始(T=1)   :", sample_n(base))
print("  低温 T=0.5    :", sample_n(softmax(logits / 0.5)))
print("  高温 T=1.5    :", sample_n(softmax(logits / 1.5)))
print("  top-k=3       :", sample_n(top_k(logits, 3)))
print("  top-p=0.9     :", sample_n(top_p(logits, 0.9)))

print("""
小结:
  · greedy:永远取最高分。确定但单调,长文本里极易复读、绕圈。
  · temperature:logits/T 调"胆量"。T<1 更稳更尖,T>1 更野更平,T=1 为原始。
  · top-k:只在前 k 名里采,砍掉长尾烂字。k 固定,不看分布形状。
  · top-p(核采样):保留"累计概率达 p"的最小集合,候选数随模型把握度自适应。
  · 实践常组合用:先 top-k / top-p 砍长尾,再配适中 temperature 调多样性。
""")
