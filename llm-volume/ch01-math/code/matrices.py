"""
ch01 · 矩阵乘法当作"变换"
神经网络的参数大多是矩阵,前向计算的核心就是矩阵乘法。
运行: python3 matrices.py
"""

import numpy as np

# 3 个词,每个词是 2 维向量(每行一个词)
words = np.array([[1, 0],
                  [0, 1],
                  [1, 1]])
print("输入(3个词,每个2维):")
print(words)
print()

# 一个"变换矩阵": 把 x 放大 2 倍, y 放大 3 倍
W = np.array([[2, 0],
              [0, 3]])
print("变换矩阵 W:")
print(W)
print()

# @ 是矩阵乘法。每个词向量都被 W 变换一次
out = words @ W
print("输出 = words @ W:")
print(out)
print()
print("可以看到: 每个词的第1维被放大2倍,第2维被放大3倍")

# 试试看: 把 W 换成 [[0,1],[1,0]],它会把每个词的两个维度对调
