"""
ch03 · 示例 3:模型好不好?用 loss 打分
=========================================
怎么衡量一个语言模型的好坏?看它对真实数据"有多不意外"。

对真实出现的每一对 (前字->后字),模型给的概率越高越好。
把这些概率取对数、求平均、取负,就是大名鼎鼎的 **负对数似然(NLL)**,
也就是我们后面训练 GPT 时用的 **交叉熵损失(cross-entropy loss)**。

  loss 越小 = 模型越"懂"这批数据。完美模型 loss=0(概率全为1)。
"""
import numpy as np
from corpus import NAMES, bigrams, build_vocab, TOKEN

vocab, stoi, itos = build_vocab()
V = len(vocab)

N = np.zeros((V, V), dtype=np.float64)
for nm in NAMES:
    for a, b in bigrams(nm):
        N[stoi[a], stoi[b]] += 1
P = (N + 1) / (N + 1).sum(axis=1, keepdims=True)

def avg_loss(prob_matrix):
    """对语料里每个真实字对,累加 -log(模型给它的概率),再求平均。"""
    total, n = 0.0, 0
    for nm in NAMES:
        for a, b in bigrams(nm):
            p = prob_matrix[stoi[a], stoi[b]]
            total += -np.log(p)
            n += 1
    return total / n

# 1. 我们的统计模型
loss_model = avg_loss(P)

# 2. 对照组:完全瞎猜(每个字概率都是 1/V)
uniform = np.full((V, V), 1.0 / V)
loss_uniform = avg_loss(uniform)

print(f"统计模型的平均 loss = {loss_model:.4f}")
print(f"瞎猜基线的平均 loss = {loss_uniform:.4f}   (= ln V = ln{V})")
print()
print("解读:")
print(f"  - 瞎猜时,模型对每个字的'惊讶程度'相当于在 {V} 个字里抓阄。")
print(f"  - 我们的模型 loss 明显更低,说明它确实学到了规律。")
print(f"  - 把 loss 还原成'有效候选数' e^loss:")
print(f"      瞎猜 ≈ {np.exp(loss_uniform):.0f} 选 1   我们的模型 ≈ {np.exp(loss_model):.1f} 选 1")
print()
print("训练 GPT,就是想尽办法把这个 loss 压得更低。")
