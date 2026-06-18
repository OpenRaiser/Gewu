"""
ch04 · 示例 1:最简单的分词器 —— 字符级(char-level)
=====================================================
上一章的统计模型,我们已经在偷偷做一件事:把「字」变成「编号」。
这一章把它正式拎出来讲:**文字怎么变成数字?**

神经网络只认数字,不认汉字、不认字母。所以喂给模型之前,
必须先把一段文字「切成一个个小块(token)」,再给每个块一个编号。
这一步就叫 **tokenization(分词 / 词元化)**。

最朴素的切法:**一个字符就是一个 token**。
"""

# 一小段语料(中英混合,故意的:好看出两种语言的差别)
TEXT = "床前明月光 the moon"

# 1. 建词表:收集所有出现过的字符,排序后给编号
chars = sorted(set(TEXT))
stoi = {c: i for i, c in enumerate(chars)}   # 字符 -> 编号 (string to int)
itos = {i: c for c, i in stoi.items()}       # 编号 -> 字符 (int to string)
vocab_size = len(chars)

print("原文:", repr(TEXT))
print(f"\n词表大小 = {vocab_size} 个不同字符")
print("字符 -> 编号:")
for c in chars:
    shown = "' '(空格)" if c == " " else repr(c)
    print(f"   {shown:>9} -> {stoi[c]}")


# 2. 编码 / 解码:文字 <-> 数字,互为逆操作
def encode(s):
    """把一段文字切成字符,再换成编号列表。"""
    return [stoi[c] for c in s]


def decode(ids):
    """把编号列表还原回文字。"""
    return "".join(itos[i] for i in ids)


ids = encode(TEXT)
print("\n编码后(喂给模型的就是这串数字):")
print("  ", ids)

print("\n解码回来(模型吐出数字后,我们这样变回文字):")
print("  ", repr(decode(ids)))

# 3. 验证:编码再解码,必须一字不差
assert decode(encode(TEXT)) == TEXT
print("\n✓ encode 和 decode 互逆:解码(编码(x)) == x")

print("""
小结:分词器 = 一张「字 <-> 编号」的对照表 + encode/decode 两个函数。
字符级最简单:词表小、绝不会遇到「不认识的字」。
但它也有代价 —— 下一个示例就来看它的短板。
""")
