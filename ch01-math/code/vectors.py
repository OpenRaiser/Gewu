"""
ch01 · 向量与点积
点积越大 => 两个向量越相似。这是后面"注意力机制"的基础。
运行: python3 vectors.py
"""

import numpy as np

a = np.array([1, 0, 1])   # 想象成"猫"的特征向量
b = np.array([1, 0, 1])   # 另一只"猫"
c = np.array([0, 1, 0])   # "汽车"

print("向量 a (猫):", a)
print("向量 b (猫):", b)
print("向量 c (车):", c)
print()

# 点积 = 对应位置相乘再相加
print("猫 · 猫 =", np.dot(a, b), " -> 数值大,很相似")
print("猫 · 车 =", np.dot(a, c), " -> 数值小,不相似")
print()

# 余弦相似度: 把点积归一化到 [-1, 1],更公平地比较"方向"
def cosine(x, y):
    return np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y))

print("cos(猫, 猫) =", round(cosine(a, b), 3))
print("cos(猫, 车) =", round(cosine(a, c), 3))

# 试试看: 自己改一改 a / b / c 的数字,观察相似度怎么变
