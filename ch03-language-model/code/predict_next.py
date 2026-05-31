"""
ch03 · 示例 1:语言模型到底在干什么?
=====================================
一句话:语言模型 = 看着前面的字,给出「下一个字的概率分布」。

最简单的版本:统计。我们数一数语料里,"天" 后面都跟过哪些字、各多少次,
把次数变成概率,就得到了 "天" 的下一字分布。这就是一个(超迷你)语言模型。
"""
from collections import Counter
from corpus import NAMES, bigrams

# 数一数:每个字后面,各个字分别出现了多少次
after = {}   # after[前字] = Counter({后字: 次数})
for nm in NAMES:
    for a, b in bigrams(nm):
        after.setdefault(a, Counter())[b] += 1

# 看看 "天" 后面跟过什么
print("语料里 '天' 后面出现过:")
for ch, cnt in after["天"].most_common():
    print(f"   天 -> {ch}   {cnt} 次")

# 把次数变成概率(除以总数)
total = sum(after["天"].values())
print("\n于是模型认为 '天' 的下一个字概率是:")
for ch, cnt in after["天"].most_common():
    print(f"   P(下一个字 = {ch} | 当前 = 天) = {cnt}/{total} = {cnt/total:.2f}")

print("\n这就是一个语言模型:输入一个字,输出下一个字的概率分布。")
print("ChatGPT 本质做的是同一件事,只是'前文'更长、分布更聪明而已。")
