"""
ch03 · 示例 4:统计模型的天花板(为什么需要神经网络)
========================================================
我们的 bigram 模型只看「前一个字」就猜下一个。这有个硬伤:健忘。

它永远只记得上一个字,不管再前面是什么。
- 想让它记住前 2 个字 -> 要存 V×V×V 张表
- 前 10 个字 -> V^11 张表,天文数字,根本存不下

这就是统计模型的天花板:**上下文一长,表就爆炸**。
解决之道:不用"查表",而用"一个会算的函数"(神经网络)来估计概率。
这正是后面所有章节(Embedding、注意力、Transformer)要做的事。
"""
import numpy as np
from corpus import NAMES, bigrams, build_vocab, TOKEN

vocab, stoi, itos = build_vocab()
V = len(vocab)

print(f"词表大小 V = {V}")
print("如果想看更长的上下文,统计表要存多少个数字:")
for ctx in [1, 2, 3, 5, 10]:
    cells = V ** (ctx + 1)
    print(f"  看前 {ctx:2d} 个字:V^{ctx+1} = {cells:,.0f} 个格子")

print()
print("看前 10 个字就已是天文数字——而且绝大多数格子是 0(从没出现过)。")
print("这叫'维度灾难'。神经网络的办法是:不存表,而是学一个函数去'算'概率,")
print("于是参数量只随上下文长度温和增长,还能在没见过的组合上合理泛化。")

# 直观演示"健忘":只看前一个字,模型分不清不同的前文
print("\n演示健忘:不论'天'前面是什么,模型给出的下一字分布都一样——")
N = np.zeros((V, V))
for nm in NAMES:
    for a, b in bigrams(nm):
        N[stoi[a], stoi[b]] += 1
P = (N + 1) / (N + 1).sum(axis=1, keepdims=True)
row = P[stoi["天"]]
top3 = np.argsort(row)[::-1][:3]
print("  P(下一字 | 当前='天') 前三:", [(itos[i], round(float(row[i]), 2)) for i in top3])
print("  无论'天'出现在'天明'还是'春天'里,这个分布都不变。这就是局限。")
