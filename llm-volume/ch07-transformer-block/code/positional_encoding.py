"""
ch07 · 示例 1:位置编码(positional encoding)—— 给词标上「座位号」
=================================================================
注意力有个被忽略的「特性」:它**看不出词的顺序**。
回想第六章的打分 scores = Q·Kᵀ,如果把句子里的词打乱,
每一对词的点积还是那个值,加权汇总也只是跟着换了顺序——
也就是说,「我吃苹果」和「苹果吃我」,在纯注意力眼里几乎一样!

可顺序明明很重要。于是要给每个位置一个独有的「座位号向量」,
加到词向量上,让模型能区分「第 0 个位置的词」和「第 3 个位置的词」。
这就是位置编码。

原版 Transformer 用的是一组 sin / cos 波形(不同频率),好处:
  · 不用学习,直接算出来;
  · 任意长度都能生成;
  · 不同位置的编码两两不同,且能体现「相对距离」。
"""
import numpy as np

np.set_printoptions(precision=3, suppress=True)


def positional_encoding(seq_len, d_model):
    """返回 (seq_len, d_model):第 pos 行就是第 pos 个位置的座位号向量。"""
    pe = np.zeros((seq_len, d_model))
    pos = np.arange(seq_len)[:, None]                 # (seq_len, 1)
    i = np.arange(0, d_model, 2)                      # 偶数维下标 0,2,4...
    # 频率:维度越靠后,波长越长(变化越慢)
    div = np.power(10000.0, i / d_model)
    pe[:, 0::2] = np.sin(pos / div)                   # 偶数维放 sin
    pe[:, 1::2] = np.cos(pos / div)                   # 奇数维放 cos
    return pe


seq_len, d_model = 6, 8
pe = positional_encoding(seq_len, d_model)
print(f"位置编码矩阵 PE,形状 {pe.shape}(每行一个位置):")
print(pe)

# ---------- 关键性质 1:每个位置的编码都不同 ----------
print("\n第 0 位 与 第 1 位 的编码距离:",
      round(float(np.linalg.norm(pe[0] - pe[1])), 3))
print("第 0 位 与 第 5 位 的编码距离:",
      round(float(np.linalg.norm(pe[0] - pe[5])), 3))
print("-> 位置离得越远,编码差别一般越大,模型能据此分辨先后。")

# ---------- 关键性质 2:用法就是「加」到词向量上 ----------
rng = np.random.default_rng(0)
X = rng.standard_normal((seq_len, d_model))   # 假装是查表得到的词向量
X_with_pos = X + pe                            # 直接相加,注入位置信息
print("\n词向量 + 位置编码(逐元素相加)后,形状不变:", X_with_pos.shape)
print("从此,同一个词出现在不同位置,送进注意力的向量就不一样了。")

print("""
小结:
  · 纯注意力对「词的顺序」不敏感(打乱词,两两点积不变)。
  · 位置编码 = 给每个位置一个独有向量,加到词向量上,把顺序信息「掺」进去。
  · sin/cos 版本:无需训练、任意长度可生成、不同位置各不相同。
  · 用法极简:embedding(词) + PE(位置),形状不变,再送进 Transformer。
  · (也有「可学习位置编码」:把 PE 当成参数训练。GPT 系列多用这种,下一章会用到。)
""")
