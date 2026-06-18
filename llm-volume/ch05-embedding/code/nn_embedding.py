"""
ch05 · 示例 4:nn.Embedding —— 可学习的查表层(并亲眼看它学出含义)
=====================================================================
前面那张「含义向量表」的数字是我手填的。真实模型里,这些向量是**训练出来的参数**:
一开始是随机的,模型在完成任务(比如猜下一个字)的过程中,用梯度下降把它们慢慢调好。

PyTorch 把这张可学习的表封装成一层:**nn.Embedding(词表大小, 向量维度)**。
  · 它内部就是一个 (V, D) 的矩阵,且 requires_grad=True(能被训练)。
  · 前向就是「按编号查行」——和示例 2 的 E[i] 一模一样,只是能自动求导。

本节做两件事:
  1. 看清 nn.Embedding 就是一张能求导的查找表;
  2. 用一个极小的任务,**亲手训练**它,让随机初始化的向量真的学出「同类词相近」。
"""
import torch
import torch.nn as nn

torch.manual_seed(0)

VOCAB = ["猫", "狗", "桌子", "椅子"]
stoi = {w: i for i, w in enumerate(VOCAB)}
V, D = len(VOCAB), 2  # 用 2 维,方便直观打印坐标

# ---------- 1. nn.Embedding 就是可求导的查表 ----------
emb = nn.Embedding(V, D)
print("nn.Embedding(4, 2) 内部的权重矩阵(初始为随机):")
print(emb.weight.data)

ids = torch.tensor([stoi["猫"], stoi["桌子"]])
print(f"\n查表:输入编号 {ids.tolist()} -> 取出对应行")
print(emb(ids))
print(f"权重可训练吗?requires_grad = {emb.weight.requires_grad}")

# ---------- 2. 真的训练它:让「同类词」向量靠近 ----------
# 任务设计得极简:告诉模型「猫~狗 是一类,桌子~椅子 是一类」,
# 让同类词的向量余弦相似度趋近 1,异类趋近 0。看随机向量能否自己挪到位。
SAME = [("猫", "狗"), ("桌子", "椅子")]        # 希望相似(目标 1)
DIFF = [("猫", "桌子"), ("狗", "椅子")]        # 希望不相似(目标 0)


def cos(a, b):
    a = a / a.norm()
    b = b / b.norm()
    return (a * b).sum()


def avg_cos(pairs):
    vals = [cos(emb.weight[stoi[a]], emb.weight[stoi[b]]) for a, b in pairs]
    return torch.stack(vals).mean()


opt = torch.optim.SGD(emb.parameters(), lr=0.5)
print("\n开始训练(目标:同类相似度→1,异类→0):")
print(f"  训练前:同类平均 cos = {avg_cos(SAME):.3f}，异类平均 cos = {avg_cos(DIFF):.3f}")

for step in range(301):
    # loss = 同类离 1 的差 + 异类离 0 的差(都用平方惩罚)
    loss = (1 - avg_cos(SAME)) ** 2 + (avg_cos(DIFF)) ** 2
    opt.zero_grad()
    loss.backward()
    opt.step()
    if step % 100 == 0:
        print(f"  step {step:>3}: loss={loss.item():.4f}  "
              f"同类 cos={avg_cos(SAME).item():.3f}  异类 cos={avg_cos(DIFF).item():.3f}")

print(f"  训练后:同类平均 cos = {avg_cos(SAME):.3f}，异类平均 cos = {avg_cos(DIFF):.3f}")

# ---------- 训练后看每个词学到的 2 维坐标 ----------
print("\n训练后,每个词学到的向量(随机初始化 → 梯度下降挪到位):")
for w in VOCAB:
    v = emb.weight[stoi[w]].data
    print(f"  {w}: [{v[0]:+.2f}, {v[1]:+.2f}]")

print(f"\n验证:cos(猫, 狗) = {cos(emb.weight[stoi['猫']], emb.weight[stoi['狗']]):.3f}"
      f"，cos(猫, 桌子) = {cos(emb.weight[stoi['猫']], emb.weight[stoi['桌子']]):.3f}")

print("""
小结:
  · nn.Embedding(V, D) = 一张 (V, D) 的【可学习】查找表,前向就是「按编号查行」。
  · 它的每个数字都是模型参数,靠梯度下降训练——随机起步,也能学出「同类相近」。
  · 真实 GPT 里没有「告诉它谁是同类」这种监督;它只是在反复猜下一个字,
    这些含义向量是【顺带】学出来的副产品——但效果惊人地好。

到这里,「文字 -> 编号 -> 含义向量」的链条就打通了:
  ch04 把文字切成编号,ch05 把编号查成向量。
下一步(ch06 注意力):让这些向量之间「互相看一看」,理解上下文——这才是 Transformer 的心脏。
""")
