"""
ch11 · 示例 2:手写一个最小 LoRA 层,并真的训练它
==================================================
示例 1 讲清了思想。这里动手做一个能跑的最小 LoRA:
  · 有一个「预训练好的」线性层 base(我们冻结它,假装它是大模型的一部分);
  · 给它挂上一个 LoRA 适配器(两个瘦矩阵 A、B);
  · 只训练 A、B(base 一根毫毛都不动),让整体去拟合一个新任务。

看两件事:
  1) 训练时,只有 LoRA 的参数在更新,base 的参数纹丝不动;
  2) 只靠这一点点新参数,模型就能学会新任务,loss 照样降下去。
"""
import torch
import torch.nn as nn
import torch.nn.functional as F

torch.manual_seed(0)

D_IN, D_OUT, R = 32, 32, 4


class LoRALinear(nn.Module):
    """y = base(x) + (alpha/r) * B(A(x))。base 冻结,只训练 A、B。"""
    def __init__(self, d_in, d_out, r, alpha=8):
        super().__init__()
        self.base = nn.Linear(d_in, d_out, bias=False)
        self.base.weight.requires_grad = False          # 冻结预训练权重

        self.A = nn.Linear(d_in, r, bias=False)          # 降维:d_in -> r
        self.B = nn.Linear(r, d_out, bias=False)         # 升维:r -> d_out
        nn.init.zeros_(self.B.weight)                    # B 初始化为 0
        # -> 训练开始时 B·A = 0,整层等于原模型,不破坏已有能力(LoRA 的关键技巧)
        self.scale = alpha / r

    def forward(self, x):
        return self.base(x) + self.scale * self.B(self.A(x))


# ---------- 造一个「新任务」----------
# 关键设定:新任务的目标 = base 再加上一个「低秩改动量」(秩 = R)。
# 这正是 LoRA 的用武之地——示例 1 已证明:只要 r 覆盖改动量的秩,低秩近似几乎无损。
layer = LoRALinear(D_IN, D_OUT, R)

target = nn.Linear(D_IN, D_OUT, bias=False)
for p in target.parameters():
    p.requires_grad = False
with torch.no_grad():
    B_true = torch.randn(D_OUT, R)
    A_true = torch.randn(R, D_IN)
    delta = (B_true @ A_true) * 0.5             # 一个秩为 R 的真实改动量
    target.weight.copy_(layer.base.weight + delta)

# ---------- 数一数:谁在训练,谁被冻结 ----------
trainable = sum(p.numel() for p in layer.parameters() if p.requires_grad)
frozen = sum(p.numel() for p in layer.parameters() if not p.requires_grad)
print("===== 参数账本 =====")
print(f"  冻结(base 权重)    : {frozen:,} 个  <- 不训练")
print(f"  可训练(LoRA 的 A+B): {trainable:,} 个  <- 只训这些")
print(f"  可训练占比          : {trainable/(trainable+frozen)*100:.1f}%")

# ---------- 记下 base 权重的「指纹」,训练后核对它没被动过 ----------
base_fingerprint = layer.base.weight.detach().clone()

# ---------- 训练:只有 LoRA 在学 ----------
opt = torch.optim.Adam([p for p in layer.parameters() if p.requires_grad], lr=0.01)
print("\n===== 训练(只更新 LoRA)=====")
for step in range(1, 401):
    x = torch.randn(64, D_IN)
    y_target = target(x)
    y_pred = layer(x)
    loss = F.mse_loss(y_pred, y_target)
    opt.zero_grad(); loss.backward(); opt.step()
    if step == 1 or step % 100 == 0:
        print(f"  第 {step:>3} 步  loss = {loss.item():.4f}")

# ---------- 训练后核对:base 真的没动 ----------
unchanged = torch.allclose(layer.base.weight, base_fingerprint)
print(f"\nbase 权重训练后是否完全没变: {unchanged}  <- 冻结生效")
print(f"LoRA 的 B 是否已从 0 学出了内容: {not torch.allclose(layer.B.weight, torch.zeros_like(layer.B.weight))}")

print("""
小结:
  · LoRALinear = 冻结的 base + 可训练的低秩旁路 (alpha/r)·B·A。
  · B 初始化为 0:训练起点处旁路输出为 0,整层 == 原模型,不破坏已有能力。
  · 训练时只有 A、B 收到梯度;上面核对了 base 权重一个数都没变。
  · 仅用约百分之十几(本例 D 很小;真实大模型里是 <1%)的新参数,loss 照样降。
  · 部署时把 B·A 合并回 W 即可零额外开销;不合并则可随时插拔、按任务切换适配器。
""")
