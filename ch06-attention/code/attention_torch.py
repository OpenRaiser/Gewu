"""
ch06 · 示例 5:用 PyTorch 把它写成一层 —— nn.Module 版多头自注意力
==============================================================
前面 4 个示例用 numpy 把原理拆开看清了。真实项目里,我们会把这套流程
封装成一个可训练的「层」(nn.Module),让 Wq/Wk/Wv/Wo 都成为可学习参数,
并且支持「批量(batch)」一次算多句话。

本示例做两件事:
  1) 手写一个 CausalSelfAttention 层(带因果掩码的多头自注意力);
  2) 用 PyTorch 内置的 F.scaled_dot_product_attention 复算,验证我们写得对。
"""
import torch
import torch.nn as nn
import torch.nn.functional as F

torch.manual_seed(0)


class CausalSelfAttention(nn.Module):
    """带因果掩码的多头自注意力。输入输出都是 (B, T, C)。"""
    def __init__(self, d_model, n_head):
        super().__init__()
        assert d_model % n_head == 0
        self.n_head = n_head
        self.d_k = d_model // n_head
        # 一次性把 Q、K、V 三个投影合成一个大矩阵(工程上更快),输出 3*d_model
        self.qkv = nn.Linear(d_model, 3 * d_model, bias=False)
        self.proj = nn.Linear(d_model, d_model, bias=False)   # 输出融合 Wo

    def forward(self, x):
        B, T, C = x.shape                      # 批量、序列长、通道(=d_model)
        q, k, v = self.qkv(x).split(C, dim=2)  # 各 (B, T, C)
        # 拆成多头:(B, T, C) -> (B, n_head, T, d_k)
        q = q.view(B, T, self.n_head, self.d_k).transpose(1, 2)
        k = k.view(B, T, self.n_head, self.d_k).transpose(1, 2)
        v = v.view(B, T, self.n_head, self.d_k).transpose(1, 2)

        # 打分 + 缩放:(B, n_head, T, T)
        att = (q @ k.transpose(-2, -1)) / (self.d_k ** 0.5)
        # 因果掩码:上三角(未来)置 -inf
        mask = torch.tril(torch.ones(T, T, dtype=torch.bool))
        att = att.masked_fill(~mask, float("-inf"))
        att = att.softmax(dim=-1)

        y = att @ v                            # (B, n_head, T, d_k)
        # 合并多头:-> (B, T, C)
        y = y.transpose(1, 2).contiguous().view(B, T, C)
        return self.proj(y), att


# ---------- 造一个小批量:1 句话、4 个词、每个词 8 维 ----------
B, T, C, H = 1, 4, 8, 2
x = torch.randn(B, T, C)

layer = CausalSelfAttention(C, H)
y, att = layer(x)
print("输入  x 形状:", tuple(x.shape))
print("输出  y 形状:", tuple(y.shape), "(和输入一致,可以一层层叠起来)")
print("注意力权重 att 形状:", tuple(att.shape), "= (批量, 头数, 词, 词)")

# ---------- 验证因果性:每一行的「未来」权重都应为 0 ----------
print("\n第 0 个头的注意力权重(应是下三角):\n", att[0, 0].detach().numpy().round(3))
upper = torch.triu(att[0, 0].detach(), diagonal=1)   # 严格上三角(未来部分)
print("未来部分(严格上三角)之和 =", float(upper.sum()), "-> 应为 0")

# ---------- 用 PyTorch 官方算子复算,核对我们写得对不对 ----------
# F.scaled_dot_product_attention 自带 is_causal,内部就是上面那套数学。
def manual_no_proj(x, layer):
    B, T, C = x.shape
    q, k, v = layer.qkv(x).split(C, dim=2)
    q = q.view(B, T, layer.n_head, layer.d_k).transpose(1, 2)
    k = k.view(B, T, layer.n_head, layer.d_k).transpose(1, 2)
    v = v.view(B, T, layer.n_head, layer.d_k).transpose(1, 2)
    att = (q @ k.transpose(-2, -1)) / (layer.d_k ** 0.5)
    mask = torch.tril(torch.ones(T, T, dtype=torch.bool))
    att = att.masked_fill(~mask, float("-inf")).softmax(dim=-1)
    return (att @ v)

with torch.no_grad():
    q, k, v = layer.qkv(x).split(C, dim=2)
    q = q.view(B, T, H, C // H).transpose(1, 2)
    k = k.view(B, T, H, C // H).transpose(1, 2)
    v = v.view(B, T, H, C // H).transpose(1, 2)
    official = F.scaled_dot_product_attention(q, k, v, is_causal=True)
    ours = manual_no_proj(x, layer)

print("\n我们的实现 与 PyTorch 官方 scaled_dot_product_attention 是否一致:",
      torch.allclose(ours, official, atol=1e-5))

print("""
小结:
  · 把注意力封装成 nn.Module:Wq/Wk/Wv 合成一个 qkv 线性层,Wo 是 proj 层,全可训练。
  · 输入输出都是 (B, T, C) 同形状,所以可以一层接一层地堆叠(下一章就这么干)。
  · 多头通过 view + transpose 实现「拆头 / 并头」,不需要写循环。
  · 因果掩码用 masked_fill(-inf) 实现;验证严格上三角和为 0,确认没偷看未来。
  · 我们手写的结果和 PyTorch 官方算子完全一致——说明原理吃透了,工程实现也对。
""")
