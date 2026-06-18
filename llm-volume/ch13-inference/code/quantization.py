"""
ch13 · 示例 2:int8 量化 —— 用「小格子」存权重,模型瘦一圈
============================================================
KV cache 省的是「计算」(示例 1)。这里省的是「存储和带宽」:量化(quantization)。

大模型的权重通常用 float32(每个数 4 字节)存。一个 70 亿参数的模型,
光权重就要 70 亿 × 4 = 28 GB。能不能用更少的位数存每个数?

int8 量化:把原本 float32 的权重,用 8 位整数(int8,只能表示 -128~127)来存,
**每个数从 4 字节压到 1 字节,体积直接缩到 1/4**。

代价是精度:float 是连续的,int8 只有 256 个台阶,势必有「四舍五入」的误差。
关键技巧是**缩放(scale)**:先找出这批权重里绝对值最大的数,把它映射到 127,
其余按比例缩放取整。用的时候再乘回 scale 还原。本示例手写这套「压缩-还原」,
亲眼看体积缩了 4 倍、误差有多小,以及它对模型输出的实际影响。
"""
import numpy as np

np.set_printoptions(precision=4, suppress=True)
rng = np.random.default_rng(0)


# ---------- 1. 量化:float32 -> int8 + 一个 scale ----------
def quantize_int8(w):
    """把 float 权重压成 int8。返回 (int8 数组, scale)。"""
    scale = np.abs(w).max() / 127.0        # 最大绝对值映射到 127
    q = np.round(w / scale).astype(np.int8)  # 按比例缩放,四舍五入到整数台阶
    return q, scale


def dequantize(q, scale):
    """还原:int8 乘回 scale,变回近似的 float。"""
    return q.astype(np.float32) * scale


# ---------- 2. 拿一个权重矩阵试试 ----------
W = rng.standard_normal((256, 256)).astype(np.float32)
q, scale = quantize_int8(W)
W_hat = dequantize(q, scale)               # 压缩再还原,得到近似权重

print("===== 体积对比 =====")
print(f"  原始 float32: {W.nbytes:>8,} 字节  (每个数 4 字节)")
print(f"  量化 int8   : {q.nbytes:>8,} 字节  (每个数 1 字节) + 1 个 scale")
print(f"  压缩到原来的: {q.nbytes / W.nbytes * 100:.1f}%  <- 缩了 4 倍")

print("\n===== 精度损失(还原后和原始差多少)=====")
rel_err = np.linalg.norm(W - W_hat) / np.linalg.norm(W)
print(f"  权重相对误差: {rel_err:.4f}  <- int8 只有 256 个台阶,有小幅四舍五入误差")
print(f"  单个权重示例: 原始 {W[0,0]:+.4f}  ->  还原 {W_hat[0,0]:+.4f}")

# ---------- 3. 看对「实际输出」的影响:拿同一个输入过一遍 ----------
x = rng.standard_normal((1, 256)).astype(np.float32)
y_full = x @ W                              # 用原始权重
y_quant = x @ W_hat                         # 用量化还原后的权重
out_err = np.linalg.norm(y_full - y_quant) / np.linalg.norm(y_full)
print("\n===== 对输出的影响 =====")
print(f"  输出相对误差: {out_err:.4f}  <- 误差很小,模型行为基本不变")

print("""
小结:
  · 量化 = 用更少的位数存权重。int8 把每个数从 4 字节压到 1 字节,体积缩到 1/4。
  · 关键是 scale:把这批数里最大的绝对值映射到 127,其余按比例缩放取整;用时再乘回来。
  · 代价是精度:int8 只有 256 个台阶,会有小幅四舍五入误差——但对最终输出影响很小。
  · 好处:模型更小、更省显存、加载和搬运更快,手机/边缘设备也跑得动。
  · 真实做法更精细(分组量化、4-bit、对激活也量化等),但「缩放+取整」的内核就是这个。
""")
