# ch00 · 环境准备 + 这门教程怎么用

欢迎!这一章不讲大模型,只做一件事:**把环境装好,确认你能跑代码**。
把这一步走通,后面才能安心学原理。

---

## 1. 你需要什么

- 一台电脑(Windows / Mac / Linux 都行),普通笔记本即可,**不需要显卡**
- Python 3.10 或更高版本
- 一点点耐心 🙂

> 教程里所有代码都设计成"CPU 也能在几分钟内跑完"。等你学到训练大一点的模型时,再考虑用 GPU(或免费的 Google Colab)。

---

## 2. 安装 Python

打开终端(Windows 叫"命令提示符"或 PowerShell,Mac 叫"终端"),输入:

```bash
python3 --version
```

如果显示 `Python 3.10.x` 或更高,说明已经装好了,跳到第 3 步。

如果提示"找不到命令",去 [python.org/downloads](https://www.python.org/downloads/) 下载安装即可(安装时记得勾选 "Add Python to PATH")。

---

## 3. 安装本教程需要的库

我们主要用 **PyTorch**(深度学习框架)和 **numpy**(数值计算)。在终端里运行:

```bash
pip3 install torch numpy matplotlib
```

- `torch`:本教程的主角,用来搭建和训练神经网络
- `numpy`:做向量、矩阵运算
- `matplotlib`:画图,帮助我们"看见"数据

安装可能要几分钟,耐心等待。

---

## 4. 验证环境

新建一个文件 `check_env.py`(或直接用本章 `code/check_env.py`),内容如下:

```python
import torch
import numpy as np

print("Python 环境 OK")
print("PyTorch 版本:", torch.__version__)
print("NumPy 版本:", np.__version__)

# 做一个最简单的张量运算
x = torch.tensor([1.0, 2.0, 3.0])
print("一个张量:", x)
print("它的平方:", x ** 2)

# 检查有没有 GPU(没有也完全没关系)
if torch.cuda.is_available():
    print("检测到 NVIDIA GPU,可以加速")
elif torch.backends.mps.is_available():
    print("检测到 Apple 芯片 GPU(MPS),可以加速")
else:
    print("没有 GPU,用 CPU 跑就行,本教程足够了")
```

运行它:

```bash
python3 check_env.py
```

如果你看到版本号和张量运算结果,**恭喜,环境就绪!**

---

## 5. 教程怎么用

每一章是一个文件夹,里面有:

```
chXX-名字/
├── README.md     ← 图文讲解(先读这个)
└── code/         ← 可运行的代码(再跑这个)
```

学习节奏建议:

1. **先读 README**,理解这一章在讲什么、为什么重要
2. **跑一遍 code**,看看输出,对照讲解理解
3. **动手改**:改个数字、删一行、换个输入,看结果怎么变 —— 这是学得最快的方式
4. **卡住了**:看[附录](../appendix/)的报错排查,或回上一章复习

---

## 6. 一个心态提醒

大模型听起来高大上,但它的核心思想出乎意料地简单:

> **根据前面的文字,猜下一个最可能出现的字。**

就这么一句话,我们会用整套教程把它一步步拆开、实现、训练出来。
你不需要天才般的数学,只需要跟着跑、跟着改、保持好奇。

---

## 本章小结

- ✅ 装好了 Python + PyTorch + numpy
- ✅ 跑通了第一段代码
- ✅ 知道了教程的使用方式

下一章我们补一点**数学直觉** —— 别怕,我们用代码代替公式。

下一章 → [ch01 数学直觉](../ch01-math/)
