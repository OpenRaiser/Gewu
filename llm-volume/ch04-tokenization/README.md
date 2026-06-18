# ch04 · Tokenization:文字怎么变成数字

上一章我们做出了一个会"猜下一个字"的迷你语言模型。但有件事我们一直在偷偷做、还没正式讲清楚:

> **神经网络只认数字,不认汉字、不认字母。** 那一段文字,到底是怎么变成一串数字喂进去的?

这一步就叫 **tokenization(分词 / 词元化)**:把一段文字**切成一个个小块(token)**,再给每个块一个编号。它是每个大模型的"第一关"——你对 ChatGPT 说的每句话,进门第一件事就是被切成 token。

本章从最朴素的切法出发,一步步推到**真实 GPT 正在用的分词器**。

---

## 1. 最朴素的切法:一个字符一个 token

最简单的想法:**一个字符就是一个 token**。收集语料里所有出现过的字符,排个序、编上号,就得到一张"字 ↔ 编号"的对照表:

```python
TEXT = "床前明月光 the moon"

chars = sorted(set(TEXT))                     # 所有不同字符
stoi = {c: i for i, c in enumerate(chars)}    # 字符 -> 编号 (string to int)
itos = {i: c for c, i in stoi.items()}        # 编号 -> 字符 (int to string)
```

编码就是查表把字换成号,解码就是反过来:

```python
def encode(s):
    return [stoi[c] for c in s]          # 文字 -> 数字

def decode(ids):
    return "".join(itos[i] for i in ids) # 数字 -> 文字
```

跑出来:

```text
原文: '床前明月光 the moon'

词表大小 = 12 个不同字符
编码后(喂给模型的就是这串数字):
   [9, 8, 10, 11, 7, 0, 6, 2, 1, 0, 3, 5, 5, 4]

解码回来(模型吐出数字后,我们这样变回文字):
   '床前明月光 the moon'

✓ encode 和 decode 互逆:解码(编码(x)) == x
```

**一个分词器,本质就是这么两样东西:一张对照表 + encode/decode 两个互逆函数。** 字符级最简单,词表小、还绝不会遇到"不认识的字"。但它也有代价——这就要引出下一节。

> 代码见 `code/char_tokenizer.py`。

---

## 2. 字符级 vs 词级:两头都不讨好

既然要切块,为什么不干脆按**词**切?一个词一个 token,多自然。我们用三个指标来比较切法的好坏:

- **序列长度**:同一句话切成多少个 token?(越短,模型算得越快)
- **词表大小**:一共有多少种 token?(太大,模型的输出层会爆炸)
- **OOV**:遇到没见过的词怎么办?(out-of-vocabulary,词级的老大难)

字符级和词级,正好各踩一个坑:

```text
【字符级】一个字一个 token
  '我爱自然语言处理' 切成 8 个 token
  词表大小:小(只需存所有单字)
  会遇到不认识的词吗?几乎不会 —— 单字就那么多,组合再新也能拼出来。

【词级】一个词一个 token
  词表(仅来自训练语料):['处理','学习','很','我','有趣','机器','爱','自然','语言']
  试编码 ['我','爱','深度','学习']:
     '我' -> 3
     '爱' -> 6
     '深度' -> ❌ OOV(词表里没有,模型直接抓瞎)
     '学习' -> 1
```

两难一目了然:

- **字符级**:词表小、无 OOV,但**序列长**——同一句话切出更多 token,模型要处理的步数多,还得自己从零学"哪几个字组成一个词"。
- **词级**:序列短、语义完整,但**词表会爆炸**(汉语几十万词),而且永远防不住**新词 / 错别字 / 生僻组合(OOV)**。

理想方案呼之欲出:

> **常见的词整块保留,生僻的词拆成更小的片。**

这正是 GPT 用的 **BPE(Byte Pair Encoding,字节对编码)**。

> 代码见 `code/word_problems.py`。

---

## 3. BPE:从零实现"高频对反复合并"

BPE 的思想,一句话就能说清:

> **反复把"最常一起出现的相邻一对"合并成一个新 token。**

从最小的单位(字符 / 字节)出发,统计哪一对相邻 token 最高频,就把这一对合并成一个新符号、加进词表。重复 N 次,就"长"出了一批子词。核心只要两个小函数:

```python
from collections import Counter

def get_stats(ids):
    """统计每一对相邻 token 出现的次数。"""
    counts = Counter()
    for a, b in zip(ids, ids[1:]):
        counts[(a, b)] += 1
    return counts

def merge(ids, pair, new_id):
    """把 ids 里所有的 pair=(a,b) 替换成单个 new_id。"""
    out, i = [], 0
    while i < len(ids):
        if i < len(ids) - 1 and ids[i] == pair[0] and ids[i+1] == pair[1]:
            out.append(new_id); i += 2     # 跳过被合并的两个
        else:
            out.append(ids[i]); i += 1
    return out
```

训练就是一个循环:每轮挑出当前最高频的相邻对,合并它。拿"低头思故乡 低头思故乡 举头望明月 低头思故乡"当语料,做 5 次合并:

```text
初始:23 个 token,词表 10 个

开始合并(每次挑当前最高频的相邻对):
  第1次:把 '低头' (出现 3 次) 合并为新 token #10  ->  序列剩 20 个
  第2次:把 '思故' (出现 3 次) 合并为新 token #11  ->  序列剩 17 个
  第3次:把 '低头思故' (出现 3 次) 合并为新 token #12  ->  序列剩 14 个
  第4次:把 '低头思故乡' (出现 3 次) 合并为新 token #13  ->  序列剩 11 个
  第5次:把 ' 低头思故乡' (出现 2 次) 合并为新 token #14  ->  序列剩 9 个

训练完:序列从 23 压到 9 个 token,词表长到 15 个。
```

看到了吗?高频的"低头""思故"先被合并,接着这俩又被合并成"低头思故",最后整句"低头思故乡"长成了**一个** token。用学到的规则去编码这句诗:

```text
用学到的分词器编码 '低头思故乡':
   token id:[13]
   每块对应:['低头思故乡']
   5 个字 -> 1 个 token(常见词被合并了)
   ✓ decode(encode(x)) == x
```

5 个字压成 1 个 token。**BPE 没有任何"语言知识",它只是在数频次、合并高频对。** 跑得够多次,常用词就自然"长"成整块,生僻字仍能拆成小片——字符级和词级两头的好处都占了。这正是 GPT-2/3/4 分词器的核心算法。

> 编码时要按训练时学到的合并顺序复现:在"当前能合并的对"里,总是先用**最早学会**的那条规则。代码见 `code/bpe.py`。

---

## 4. 真实 GPT 的分词器:tiktoken

我们手写的 BPE,和真正的 GPT 用的是同一个思路,只是真实版本:

- 在**海量文本**上合并了几万次,词表约 **5 万~10 万**;
- 在**字节**而非字符上做合并,所以任何字符都能编码,**绝不 OOV**。

OpenAI 开源了它的分词器 `tiktoken`,我们直接拿来看 GPT 在怎么切文字(先 `pip install tiktoken`):

```python
import tiktoken
enc = tiktoken.get_encoding("cl100k_base")   # GPT-3.5/4 同款

ids = enc.encode("tokenization")
pieces = [enc.decode([i]) for i in ids]
```

跑出来,有几个很值得玩味的现象:

```text
GPT-2  词表大小:50257
GPT-4  词表大小:100277(cl100k_base)

英文:常见词整块,词缀拆开
  'tokenization'        -> 2 个 token:['token', 'ization']
  'ChatGPT is amazing!' -> 6 个 token:['Chat', 'G', 'PT', ' is', ' amazing', '!']

空格也算进 token(GPT 的小细节)
  'hello'  -> [15339]
  ' hello' -> [24748]   前导空格让它变成另一个 token
```

`tokenization` 被拆成 `token` + `ization`——常见词根整块、词缀单独成块,这正是 BPE 训练出来的效果。注意 `hello` 和 ` hello`(带前导空格)是**两个不同的 token**:GPT 把空格也编进了 token,这样它才能准确还原"词与词之间的空格"。

中文则普遍更"费" token:

```text
中文:多数一字一 token,偶有合并
  '自然语言处理' -> 5 个 token:['自', '然', '语', '言', '处理']

同一句话,中文比英文更「费」token
  英文 'Natural language processing' -> 3 个 token
  中文 '自然语言处理'                -> 5 个 token
```

同样的意思,中文吃掉的 token 比英文多。**这就是为什么同样长度的中文,调 API 往往更贵、更占上下文窗口**——计费和上下文长度都是按 token 算的。

最后,字节级让它能编码**任何**字符,永不 OOV:

```text
字节级:任何字符都能编码,绝不 OOV
  '🦙' -> 3 个 token:[9468, 99, 247]
  decode 回来:'🦙'(由多个字节 token 拼出)
```

一个 emoji 由 3 个字节 token 拼出来。哪怕是训练时从没见过的生僻字、表情,也能拆到字节兜底,再拼回原样。

> 代码见 `code/tiktoken_demo.py`。想直观感受,也可以打开 OpenAI 的 [Tokenizer 网页](https://platform.openai.com/tokenizer),把你的句子粘进去看它怎么被切。

---

## 动手跑一跑

```bash
cd ch04-tokenization/code
python3 char_tokenizer.py   # 最朴素的字符级分词器
python3 word_problems.py    # 字符级 vs 词级:两头都不讨好
python3 bpe.py              # 从零实现 BPE
pip install tiktoken        # 跑示例 4 前先装这个
python3 tiktoken_demo.py    # 真实 GPT 的分词器
```

**建议练习**:

1. 在 `bpe.py` 里把 `NUM_MERGES` 从 5 调大到 20,看更多合并怎么把序列压得更短。
2. 在 `bpe.py` 的 `TEXT` 里换成你自己的一段话,观察它先合并出哪些"词"。
3. 在 `tiktoken_demo.py` 里加几句你常对 ChatGPT 说的话,数数中英文各占多少 token——以后写 prompt 心里就有数了。

---

## 本章小结

- **Tokenization = 把文字切成 token,再给每个 token 编号**,这是大模型的第一关
- **字符级**词表小、无 OOV,但序列长;**词级**序列短,但词表爆炸、躲不开 OOV
- **BPE 是折中**:反复合并高频相邻对——常见词整块、生僻词拆片,两头好处都占
- **真实 GPT 用的就是字节级 BPE**:词表 5 万~10 万,永不 OOV;中文比英文更费 token

文字已经变成了一串编号。但编号本身只是"身份证号",彼此之间没有任何含义上的远近——编号 5 和 6 并不比 5 和 500 更相似。

下一步:怎么让每个 token 带上**含义**,让"猫"和"狗"在数字世界里离得更近?

上一章 ← [ch03 语言模型的本质](../ch03-language-model/) ｜ 下一章 → [ch05 Embedding](../ch05-embedding/)
