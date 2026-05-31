"""
ch03 · 示例 2:计数矩阵 + 采样生成新名字
==========================================
把上一节的"数数"做全:对每一对 (前字, 后字) 都统计,得到一张大表 N。
N[i, j] = 字 i 后面跟字 j 的次数。

有了概率,就能"采样":按概率掷骰子选下一个字,一个接一个,直到收尾符。
这样就能生成语料里没有、但风格相似的新名字——这就是"生成"。
"""
import numpy as np
from corpus import NAMES, bigrams, build_vocab, TOKEN

vocab, stoi, itos = build_vocab()
V = len(vocab)

# 1. 统计计数矩阵 N
N = np.zeros((V, V), dtype=np.int32)
for nm in NAMES:
    for a, b in bigrams(nm):
        N[stoi[a], stoi[b]] += 1

# 2. 每行归一化成概率(加 1 做平滑,避免出现 0 概率)
P = (N + 1).astype(np.float64)
P = P / P.sum(axis=1, keepdims=True)   # 每行加起来 = 1

# 3. 采样:从边界符出发,按概率一路抽字,直到再次抽到边界符
def generate(rng):
    idx = stoi[TOKEN]
    out = []
    while True:
        probs = P[idx]
        idx = rng.choice(V, p=probs)   # 按概率掷骰子
        ch = itos[idx]
        if ch == TOKEN:
            break
        out.append(ch)
        if len(out) >= 4:              # 防止偶尔停不下来
            break
    return "".join(out)

rng = np.random.default_rng(42)
print("用统计模型生成的新名字:")
for _ in range(12):
    print("  ", generate(rng))

print("\n它没背语料,而是学到了'字与字怎么搭'的统计规律,再据此造新词。")
