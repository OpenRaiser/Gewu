"""
ch07 · 示例 2:残差连接 + 层归一化(LayerNorm)—— 让深网络train得动
==================================================================
把很多层(注意力、前馈……)直接叠起来,会遇到两个老大难问题:
  1) 越深越难训:梯度回传时层层相乘,容易消失或爆炸,前面的层学不动。
  2) 每层输出的数值「分布」乱飘:有时很大有时很小,训练不稳定。

Transformer 用两件法宝对症下药:

  · 残差连接(residual / skip connection):
      输出 = x + 子层(x)
    给梯度留一条「高速公路」直接绕过子层,深层也能稳稳回传。
    而且子层只需学「在 x 基础上改动多少」(增量),比从零学整个映射容易。

  · 层归一化(LayerNorm):
      对每个词向量自己的那一行,减均值、除标准差,拉回「均值0、方差1」,
      再乘可学习的 γ、加可学习的 β。让每层输入的数值分布保持稳定。
"""
import numpy as np

np.set_printoptions(precision=3, suppress=True)


def layer_norm(x, gamma, beta, eps=1e-5):
    """对最后一维(每个词的特征向量)做归一化。x: (..., d)。"""
    mu = x.mean(axis=-1, keepdims=True)
    var = x.var(axis=-1, keepdims=True)
    x_hat = (x - mu) / np.sqrt(var + eps)    # 标准化:均值0、方差1
    return gamma * x_hat + beta              # 再做可学习的缩放/平移


rng = np.random.default_rng(0)
d = 6
# 故意造一行「数值乱飘」的向量:有大有小
x = np.array([[10.0, -3.0, 0.5, 8.0, -1.0, 2.0]])
print("原始向量 x:", x, " 均值=%.3f 标准差=%.3f" % (x.mean(), x.std()))

gamma = np.ones(d)     # 先用 γ=1、β=0,看纯归一化效果
beta = np.zeros(d)
xn = layer_norm(x, gamma, beta)
print("LayerNorm 后:", xn, " 均值=%.3f 标准差=%.3f" % (xn.mean(), xn.std()))
print("-> 不管输入多乱,输出都被拉回 均值≈0、标准差≈1。")

# ---------- 残差连接:输出 = x + 子层(x) ----------
def some_sublayer(x):
    """假装是注意力或前馈,这里随便做个线性变换代表「子层」。"""
    W = rng.standard_normal((x.shape[-1], x.shape[-1])) * 0.1
    return x @ W

x_in = rng.standard_normal((1, d))
sub = some_sublayer(x_in)
out_no_res = sub                 # 没有残差:直接用子层输出
out_res = x_in + sub             # 有残差:把输入加回来
print("\n输入 x_in            :", x_in)
print("子层输出 sublayer(x) :", sub)
print("无残差(只有子层)    :", out_no_res)
print("有残差 x + 子层(x)   :", out_res)
print("-> 有残差时,输出 = 输入 + 一点改动;子层只需学「增量」,且梯度能直接走 x 这条路。")

# ---------- Transformer 里的标准用法:Pre-LN ----------
# 现代 GPT 普遍用「Pre-LN」写法:先归一化,再进子层,最后加残差:
#     x = x + sublayer(layer_norm(x))
def block_step(x, gamma, beta):
    return x + some_sublayer(layer_norm(x, gamma, beta))

y = block_step(x_in, gamma, beta)
print("\nPre-LN 一步 x = x + sublayer(LN(x)) 输出形状:", y.shape, "(与输入同形,可继续叠)")

print("""
小结:
  · 残差连接 output = x + f(x):给梯度一条高速公路,深层也能训得动;子层只学「增量」。
  · LayerNorm:对每个词向量自己归一化(均值0、方差1),再 γ/β 缩放平移,稳住数值分布。
  · 现代写法 Pre-LN:x = x + sublayer(LayerNorm(x)),训练更稳,GPT 就用这种。
  · 这两件法宝包在每个子层外面,正是 Transformer 能叠几十上百层还训得动的关键。
""")
