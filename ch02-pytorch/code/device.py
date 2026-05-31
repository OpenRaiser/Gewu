"""
ch02 · 示例 4:把计算搬到 GPU(device)
==========================================
大模型训练慢,很大原因是算力。把 tensor 放到 GPU 上能快很多。
- NVIDIA 显卡 -> "cuda"
- 苹果 M 系芯片 -> "mps"
- 都没有 -> "cpu"(也能跑,只是慢)

后面训练 GPT 时,我们会用同样的写法把模型和数据搬到加速设备上。
"""
import torch

# 1. 自动挑一个可用的最快设备
if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"
print("本机使用的设备:", device)

# 2. 把 tensor 放上去:.to(device)
a = torch.randn(3, 3).to(device)
b = torch.randn(3, 3).to(device)
print("a 所在设备:", a.device)

# 3. 在该设备上做运算(同设备的 tensor 才能一起算)
c = a @ b
print("矩阵乘结果所在设备:", c.device)

# 4. 取回 CPU 才能转成 numpy / 打印细节
c_cpu = c.cpu()
print("搬回 CPU:", c_cpu.device)

# 5. 简单测一下速度差异(矩阵越大,加速越明显)
import time
size = 2000
x_cpu = torch.randn(size, size)
t0 = time.time()
_ = x_cpu @ x_cpu
print(f"\nCPU 上 {size}x{size} 矩阵乘耗时:{time.time()-t0:.3f}s")

if device != "cpu":
    x_dev = x_cpu.to(device)
    # 预热一次(首次有启动开销)
    _ = x_dev @ x_dev
    if device == "cuda":
        torch.cuda.synchronize()
    t0 = time.time()
    _ = x_dev @ x_dev
    if device == "cuda":
        torch.cuda.synchronize()
    print(f"{device.upper()} 上同样运算耗时:{time.time()-t0:.3f}s")
