"""
ch02 · 示例 2:自动求导(autograd)
====================================
ch01 里梯度是我们"手算"的(grad = 2*(x-3))。
PyTorch 能自动帮你算梯度——这是它最核心的魔法。
你只管写"正向计算",它负责"反向求导"。
"""
import torch

# 1. 想对哪个数求导,就让它 requires_grad=True
x = torch.tensor(0.0, requires_grad=True)

# 2. 写出正向计算:y = (x - 3)^2  (和 ch01 同一个函数)
y = (x - 3) ** 2

# 3. 反向传播:一句 .backward() 就把梯度算好了
y.backward()

# 4. 梯度存在 x.grad 里。手算答案:dy/dx = 2*(x-3) = 2*(0-3) = -6
print("x =", x.item(), " y =", y.item())
print("自动求出的梯度 x.grad =", x.grad.item(), " (手算应为 -6)")

print("-" * 40)

# 5. 用 autograd 重做 ch01 的梯度下降:不再手写 grad 公式!
x = torch.tensor(0.0, requires_grad=True)
lr = 0.1
for step in range(20):
    y = (x - 3) ** 2          # 正向
    y.backward()              # 反向,自动得到 x.grad

    with torch.no_grad():     # 更新参数时不要再记录计算图
        x -= lr * x.grad      # 朝下坡迈一步
    x.grad.zero_()            # 清空梯度,否则会累加

    if (step + 1) % 5 == 0:
        print(f"第{step+1:2d}步: x={x.item():.4f}")

print("最终 x ≈", round(x.item(), 4), " (目标是 3)")
print("\n看:我们再没手写过 2*(x-3),PyTorch 全程自己求导。")
