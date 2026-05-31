# ch02 · PyTorch 入门

上一章我们用 NumPy 建立了数学直觉。这一章换上**真正的工具:PyTorch**。

为什么不继续用 NumPy?因为训练大模型需要两件 NumPy 给不了的事:

1. **自动求导** —— ch01 里梯度是我们手算的(`grad = 2*(x-3)`)。模型有几十亿个参数时,手算梯度是不可能的。PyTorch 能自动算。
2. **GPU 加速** —— 把成千上万次矩阵乘法丢给显卡并行计算,快几十上百倍。

> 一句话总结本章:**PyTorch = 会自动求导、能跑在 GPU 上的 NumPy。** 学会它,你就有了从零搭 GPT 的全部工具。

---

## 1. Tensor:升级版的数字容器

PyTorch 里一切数据都是 **Tensor(张量)**。你完全可以先把它当成 ch01 的 NumPy 数组——用法几乎一样:

```python
import torch

a = torch.tensor([1.0, 2.0, 3.0])
b = torch.tensor([10.0, 20.0, 30.0])

print(a + b)        # tensor([11., 22., 33.])
print(a * b)        # tensor([10., 40., 90.])
print(a.mean())     # tensor(2.)
```

最重要的属性是 **shape(形状)**,后面你会天天盯着它看——大部分 bug 都是形状对不上:

```python
m = torch.tensor([[1.0, 2.0, 3.0],
                  [4.0, 5.0, 6.0]])
print(m.shape)   # torch.Size([2, 3])  →  2 行 3 列
```

矩阵乘法还是那个 `@`(和 ch01 一样)。`(2,3) @ (3,2)` 得到 `(2,2)`:

```python
W = torch.tensor([[1.0, 0.0],
                  [0.0, 1.0],
                  [1.0, 1.0]])   # 3 行 2 列
print(m @ W)
# tensor([[ 4.,  5.],
#         [10., 11.]])
```

> **形状速记**:`(a, b) @ (b, c) = (a, c)`。中间的 `b` 必须相等,否则报错。这是你接下来最常遇到的检查。

完整代码见 `code/tensors.py`(还演示了 `zeros / ones / randn`、固定随机种子、以及和 NumPy 的无缝互转)。

---

## 2. 自动求导(autograd):PyTorch 的核心魔法

这是 PyTorch 区别于 NumPy 的关键。你只写**正向计算**,它自动帮你算**梯度**。

还记得 ch01 那个 `y = (x-3)²` 吗?当时梯度是我们手推的。现在让 PyTorch 来:

```python
import torch

x = torch.tensor(0.0, requires_grad=True)   # 标记:我要对 x 求导
y = (x - 3) ** 2                             # 正向计算
y.backward()                                 # 反向:一句话算好梯度

print(x.grad)   # tensor(-6.)  ←  手算 2*(x-3)=2*(0-3)=-6,完全一致
```

`requires_grad=True` 告诉 PyTorch:"请记录所有用到 `x` 的运算"。`.backward()` 就沿着这条记录倒着把梯度求出来,存进 `x.grad`。

**用 autograd 重写 ch01 的梯度下降**——注意我们再也没手写过梯度公式:

```python
x = torch.tensor(0.0, requires_grad=True)
lr = 0.1
for step in range(20):
    y = (x - 3) ** 2          # 正向
    y.backward()              # 反向,自动得到 x.grad

    with torch.no_grad():     # 更新参数时,不要把这步也记进计算图
        x -= lr * x.grad
    x.grad.zero_()            # 清空梯度,否则会一轮轮累加
```

跑出来 `x` 从 0 一路逼近 3(最终 ≈ 2.965),和 ch01 手算版结果一致。

> 两个**新手必踩的坑**,现在记住:
> - **`x.grad.zero_()` 不能漏**:PyTorch 默认把每次 `.backward()` 的梯度**累加**,不清零结果就错了。
> - **`with torch.no_grad():`**:更新参数这步不是"计算",不该被求导,要把它框起来。
>
> 这两条在下一节会被优化器自动处理掉,但理解它们为什么存在很重要。

完整代码见 `code/autograd_intro.py`。

---

## 3. 训练第一个神经网络

现在把零件拼起来,让模型**自己发现规律**。

任务:我们心里想着 `y = 2x + 1`,生成一堆带噪声的 `(x, y)` 数据,但**不告诉模型 2 和 1**。看它能不能靠梯度下降把这两个数学出来。

这套五步流程,**后面每一章训练都会复用**,值得现在就记牢:

```python
import torch
import torch.nn as nn

# 1. 准备数据(真实规律 y=2x+1,加噪声)
x = torch.linspace(-3, 3, 100).unsqueeze(1)
y = 2 * x + 1 + 0.3 * torch.randn_like(x)

# 2. 定义模型:一个线性层 y = w*x + b,w/b 待学
model = nn.Linear(1, 1)

# 3. 损失函数 + 优化器
loss_fn = nn.MSELoss()                                    # 错多少
optimizer = torch.optim.SGD(model.parameters(), lr=0.05)  # 怎么调

# 4. 训练循环
for epoch in range(200):
    pred = model(x)            # 正向
    loss = loss_fn(pred, y)    # 算损失
    optimizer.zero_grad()      # 清空梯度(替你做了 zero_)
    loss.backward()            # 反向求所有参数的梯度
    optimizer.step()           # 按梯度更新(替你做了 no_grad 更新)
```

训练 200 轮后:

```text
模型学到的:  y = 2.000 * x + 1.011
真实规律是:  y = 2.000 * x + 1.000
```

它从没被告知 2 和 1,却逼近出来了。**这就是"训练"的全部本质。**

对照上一节,注意 `optimizer` 帮我们把两个坑都填了:`optimizer.zero_grad()` 替代手动清零,`optimizer.step()` 替代 `with torch.no_grad()` 里的更新。这就是为什么实战中我们用优化器,而不是手写更新。

> **关键认知**:从这个只有 2 个参数的小模型,到有几十亿参数的 GPT,**训练流程一模一样**——准备数据、正向、算损失、反向、更新。区别只是模型更大、数据更多。你现在已经会训练了。

完整代码见 `code/first_network.py`。

---

## 4. 用上 GPU(device)

最后一块拼图:让计算跑在加速硬件上。写法就一个 `.to(device)`:

```python
import torch

# 自动挑最快的可用设备
if torch.cuda.is_available():
    device = "cuda"        # NVIDIA 显卡
elif torch.backends.mps.is_available():
    device = "mps"         # 苹果 M 系芯片
else:
    device = "cpu"         # 都没有也能跑,只是慢

a = torch.randn(3, 3).to(device)   # 把数据搬上去
b = torch.randn(3, 3).to(device)
c = a @ b                          # 在该设备上运算
print(c.device)                    # 比如 mps:0 或 cuda:0
```

> **铁律**:一起运算的 tensor 必须在**同一个设备**上,否则报错。训练时我们会把**模型和数据都 `.to(device)`**。
> 要打印细节或转成 NumPy,得先 `.cpu()` 搬回来。

矩阵越大,GPU 优势越明显——`code/device.py` 里跑了个 `2000×2000` 矩阵乘的对比,你可以在自己机器上看差距(本教程作者的 Mac 上 MPS 明显快于 CPU)。

---

## 动手跑一跑

```bash
cd ch02-pytorch/code
python3 tensors.py          # Tensor 基本操作
python3 autograd_intro.py   # 自动求导 + 梯度下降
python3 first_network.py    # 训练第一个网络
python3 device.py           # GPU/MPS 加速
```

**建议练习**:

1. 在 `first_network.py` 里把 `lr` 改成 `0.5` 和 `0.001`,看损失下降的快慢——呼应 ch01 学习率的直觉。
2. 把真实规律改成 `y = -3x + 5`,重新训练,看模型能不能学出 `-3` 和 `5`。
3. 在 `autograd_intro.py` 里故意删掉 `x.grad.zero_()`,看看结果怎么崩——亲身体会那个坑。

---

## 本章小结

- **Tensor** = 会自动求导、能上 GPU 的 NumPy 数组;最关键属性是 **shape**
- **autograd**:写正向,`.backward()` 自动求梯度;记住清零 + `no_grad` 更新两个坑
- **训练五步**:数据 → 模型 → 损失/优化器 → 训练循环 → 看结果(这套流程贯穿全书)
- **device**:`.to(device)` 搬到 GPU/MPS;同设备才能一起算

你已经掌握了从零造 GPT 的**全部工具**。接下来不再讲工具,开始讲**语言模型本身**:它到底在干什么?

上一章 ← [ch01 数学直觉](../ch01-math/) ｜ 下一章 → [ch03 语言模型的本质](../ch03-language-model/)
