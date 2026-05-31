"""
ch01 · 梯度下降: 亲眼看着 x 滑向谷底
目标: 找到让 y=(x-3)^2 最小的 x (答案显然是 x=3)。
这就是训练所有神经网络的核心思想。
运行: python3 gradient_descent.py
"""

x = 0.0      # 随便从一个起点出发
lr = 0.1     # 学习率: 每一步迈多大

history = [x]
print("目标: 让 y=(x-3)^2 最小,即找到 x=3")
print(f"起点 x = {x}")
print()

for step in range(20):
    grad = 2 * (x - 3)      # y 对 x 的梯度(斜率)
    x = x - lr * grad       # 朝"下坡"方向迈一步
    history.append(x)
    print(f"第{step+1:2d}步: 梯度={grad:+.3f}  ->  x={x:.4f}")

print()
print(f"最终 x ≈ {x:.4f} (成功逼近 3)")

# 可选: 如果装了 matplotlib,把 x 的变化画出来
try:
    import matplotlib.pyplot as plt
    plt.plot(history, marker="o")
    plt.axhline(y=3, color="r", linestyle="--", label="目标 x=3")
    plt.xlabel("step"); plt.ylabel("x"); plt.legend()
    plt.title("Gradient Descent: x sliding to the valley")
    plt.savefig("gradient_descent.png", dpi=120)
    print("已保存图像: gradient_descent.png")
except ImportError:
    print("(没装 matplotlib,跳过画图;装了的话会生成一张曲线图)")

# 试试看: 把 lr 改成 0.01(学得很慢)或 1.1(直接发散飞走),体会学习率的作用
