"""
ch02 · 示例 1:Tensor 是什么
================================
Tensor(张量)= 会算数的 NumPy 数组,还能跑在 GPU 上、自动求导。
先把它当成"升级版的数字容器"来认识。
"""
import torch

# 1. 造一个 tensor:和写 list 一样自然
a = torch.tensor([1.0, 2.0, 3.0])
b = torch.tensor([10.0, 20.0, 30.0])
print("a =", a)
print("b =", b)

# 2. 逐元素四则运算(和 NumPy 几乎一模一样)
print("a + b =", a + b)
print("a * b =", a * b)
print("a 的平均 =", a.mean())

# 3. 形状(shape):tensor 最重要的属性,后面天天看
m = torch.tensor([[1.0, 2.0, 3.0],
                  [4.0, 5.0, 6.0]])
print("矩阵 m =\n", m)
print("m 的形状 shape =", m.shape)   # torch.Size([2, 3]) 即 2 行 3 列
print("m 的维数 ndim =", m.ndim)     # 2 维

# 4. 矩阵乘法:还是那个 @,和 ch01 一样
W = torch.tensor([[1.0, 0.0],
                  [0.0, 1.0],
                  [1.0, 1.0]])   # 3 行 2 列
print("m @ W =\n", m @ W)        # (2,3) @ (3,2) -> (2,2)

# 5. 常用造数:全 0 / 全 1 / 随机
print("zeros:\n", torch.zeros(2, 2))
print("ones:\n", torch.ones(2, 2))
torch.manual_seed(0)             # 固定随机种子,保证每次结果一样
print("随机:\n", torch.randn(2, 2))

# 6. 和 NumPy 互转(无缝)
import numpy as np
np_arr = np.array([1, 2, 3])
t = torch.from_numpy(np_arr)     # numpy -> tensor
back = t.numpy()                 # tensor -> numpy
print("从 numpy 来:", t, " 再变回去:", back)
