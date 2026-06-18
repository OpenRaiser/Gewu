"""
ch00 · 环境检查脚本
运行方式: python3 check_env.py
看到版本号和张量运算结果,就说明环境 OK。
"""

import torch
import numpy as np

print("Python 环境 OK")
print("PyTorch 版本:", torch.__version__)
print("NumPy 版本:", np.__version__)

# 做一个最简单的张量(tensor)运算
x = torch.tensor([1.0, 2.0, 3.0])
print("一个张量:", x)
print("它的平方:", x ** 2)

# 检查有没有 GPU(没有也完全没关系,本教程 CPU 足够)
if torch.cuda.is_available():
    print("检测到 NVIDIA GPU,可以加速")
elif torch.backends.mps.is_available():
    print("检测到 Apple 芯片 GPU(MPS),可以加速")
else:
    print("没有 GPU,用 CPU 跑就行,本教程足够了")
