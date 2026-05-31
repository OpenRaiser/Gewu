"""
ch02 · 示例 3:训练第一个最小神经网络
========================================
任务:让模型自己发现 y = 2x + 1 这条直线。
我们只给它一堆 (x, y) 数据,不告诉它"2"和"1",看它能不能学出来。

这是你的第一个"会学习"的程序,五个步骤后面每章都会复用:
  1. 准备数据  2. 定义模型  3. 选损失与优化器  4. 训练循环  5. 看结果
"""
import torch
import torch.nn as nn

torch.manual_seed(0)

# 1. 准备数据:真实规律是 y = 2x + 1,再加一点噪声让它像真实数据
x = torch.linspace(-3, 3, 100).unsqueeze(1)   # 形状 (100, 1)
y = 2 * x + 1 + 0.3 * torch.randn_like(x)     # 带噪声的真实输出

# 2. 定义模型:一个最简单的线性层 y = w*x + b(w、b 由它自己学)
model = nn.Linear(in_features=1, out_features=1)

# 3. 损失函数(衡量错多少)+ 优化器(负责按梯度更新参数)
loss_fn = nn.MSELoss()                                  # 均方误差
optimizer = torch.optim.SGD(model.parameters(), lr=0.05)  # 随机梯度下降

# 4. 训练循环:正向 -> 算损失 -> 反向 -> 更新,重复多次
for epoch in range(200):
    pred = model(x)              # 正向:模型当前的预测
    loss = loss_fn(pred, y)      # 错了多少

    optimizer.zero_grad()        # 清空上一轮的梯度
    loss.backward()              # 反向:自动求所有参数的梯度
    optimizer.step()             # 按梯度迈一步

    if (epoch + 1) % 40 == 0:
        print(f"第{epoch+1:3d}轮  损失={loss.item():.4f}")

# 5. 看它学到了什么:w 应接近 2,b 应接近 1
w = model.weight.item()
b = model.bias.item()
print("-" * 40)
print(f"模型学到的:  y = {w:.3f} * x + {b:.3f}")
print(f"真实规律是:  y = 2.000 * x + 1.000")
print("\n它从没被告知 2 和 1,却靠梯度下降自己逼近了。这就是'训练'。")
