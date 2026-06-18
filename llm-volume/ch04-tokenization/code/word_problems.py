"""
ch04 · 示例 2:字符级 vs 词级 —— 两头都不讨好
================================================
既然要切块,为什么不干脆按「词」切?一个词一个 token,多自然。
这一节用数字说清楚:字符级和词级各自的硬伤,从而引出折中方案 BPE。

两个关键指标:
  1. 序列长度:同一句话被切成多少个 token?(越短,模型算得越快)
  2. 词表大小:一共有多少种 token?(太大,模型输出层会爆炸)
  3. OOV:遇到没见过的词怎么办?(out-of-vocabulary,词级的老大难)
"""

CORPUS = [
    "我 爱 自然 语言 处理",
    "我 爱 机器 学习",
    "自然 语言 处理 很 有趣",
]
SENTENCE = "我爱自然语言处理"

# ---------- 字符级 ----------
char_vocab = sorted(set("".join(c.replace(" ", "") for c in CORPUS)))
char_tokens = list(SENTENCE)
print("【字符级】一个字一个 token")
print(f"  '{SENTENCE}' 切成 {len(char_tokens)} 个 token:{char_tokens}")
print(f"  词表大小:{len(char_vocab)}(只需存所有单字)")
print(f"  会遇到不认识的词吗?几乎不会 —— 单字就那么多,组合再新也能拼出来。")

# ---------- 词级 ----------
# 词表 = 训练语料里出现过的所有「词」(这里假设已用空格分好)
word_vocab = sorted(set(w for line in CORPUS for w in line.split()))
print("\n【词级】一个词一个 token")
print(f"  词表(仅来自训练语料):{word_vocab}")
print(f"  词表大小:{len(word_vocab)}")

# 词级编码:逐词查表;查不到就是 OOV
word2id = {w: i for i, w in enumerate(word_vocab)}
test_words = ["我", "爱", "深度", "学习"]   # “深度”没在训练语料里出现过
print(f"\n  试编码 {test_words}:")
for w in test_words:
    if w in word2id:
        print(f"     '{w}' -> {word2id[w]}")
    else:
        print(f"     '{w}' -> ❌ OOV(词表里没有,模型直接抓瞎)")

print("""
两难:
  · 字符级:词表小、无 OOV,但序列长 —— 同样一句话切出更多 token,
            模型要处理的步数多,还得自己从零学「哪几个字组成一个词」。
  · 词级  :序列短、语义完整,但词表会爆炸(汉语几十万词),
            而且永远防不住新词 / 错别字 / 生僻组合(OOV)。

理想方案:常见的词整块保留,生僻的词拆成更小的片。
这正是 GPT 用的 **BPE(Byte Pair Encoding,字节对编码)** —— 下一个示例从零实现它。
""")
