"""
ch01 · softmax: 把"打分"变成"概率"
大模型输出的最后一步永远是 softmax。
运行: python3 softmax.py
"""

import numpy as np

def softmax(x):
    # 减去最大值是为了数值稳定(避免 exp 溢出),不影响最终结果
    e = np.exp(x - np.max(x))
    return e / e.sum()

# 模型对 3 个候选字的"打分"(logits)
scores = np.array([2.0, 1.0, 0.1])
probs = softmax(scores)

print("打分(logits):", scores)
print("概率(softmax):", np.round(probs, 3))
print("概率之和:", round(probs.sum(), 3), "(永远是 1)")
print()

# 直观理解: 打分差距越大,概率越"尖锐"(模型越自信)
print("打分差距变大后:")
print(np.round(softmax(np.array([5.0, 1.0, 0.1])), 3))
print("打分都差不多时(模型很犹豫):")
print(np.round(softmax(np.array([1.0, 1.0, 1.0])), 3))

# 试试看: 把 scores 改成 [10, 0, 0],看模型会多"自信"
