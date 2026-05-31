# 第六章 · 注意力机制(Attention)

> 上一章我们把每个词查成了一个「含义向量」。可这些向量是**孤立**的:
> 「苹果」永远是同一串数字,不管它出现在「我吃了一个**苹果**」还是「**苹果**发布了新手机」。
> 同一个词,在不同上下文里意思天差地别——光看词本身的向量,模型分不清。
>
> 怎么办?让每个词**看一看句子里的其他词**,根据上下文调整自己的表示。
> 这就是**注意力(attention)**。它是整个 Transformer、也是整个 GPT 的心脏。

本章从「为什么需要它」一路讲到「PyTorch 里它长什么样」,全程用 4 个词的小句子
`["我", "吃", "苹果", "了"]` 把每一步的数字都摊开给你看。

---

## 1. 为什么需要注意力:让词「看见」上下文

最朴素的想法:一个词的新表示 = 它和上下文里每个词的**相关度**,作为权重,加权汇总所有词。

三步走:

1. **算相关度**:最简单的相关度就是两个词向量的**点积**(越像,点积越大)。
2. **变权重**:对每一行做 softmax,把相关度归一成「和为 1」的注意力权重。
3. **加权汇总**:用权重对所有词向量加权平均,得到「带上下文」的新表示。

```python
scores = X @ X.T                       # (4,4) 每个词和所有词的点积
weights = np.array([softmax(r) for r in scores])   # 每行归一成权重
Y = weights @ X                        # 新表示 = 所有词的加权平均
```

> 代码见 [`code/why_attention.py`](code/why_attention.py)

跑出来,`苹果`这一行的注意力权重是:

```text
『苹果』对各词的注意力权重:
  我   0.162 ████
  吃   0.260 ███████
  苹果  0.469 ██████████████
  了   0.109 ███
```

`苹果`给了`吃`不低的权重,于是它的新向量更偏「食物」义。如果句子换成「苹果发布手机」,
它就会更关注「发布 / 手机」,偏「公司」义。**同一个词,在不同句子里能有不同含义**——
这正是注意力带来的本事。

但这种写法有个缺陷:相关度直接拿「原始向量点积」,每个词只能用**原本的样子**去匹配,
没法分别表达「我想找什么」和「我能提供什么」。下一节就用 Q/K/V 解决它。

---

## 2. 自注意力的真身:Q / K / V

一个词其实身兼三职:

- 作为**提问的人**:我在找什么样的上下文? —— 这叫 **Query(查询,Q)**
- 作为**被查的人**:我能提供什么样的标签? —— 这叫 **Key(键,K)**
- 真要取用时,我交出什么内容? —— 这叫 **Value(值,V)**

做法:把同一个词向量,分别乘上三张**不同**的权重矩阵 `Wq / Wk / Wv`,得到它的 Q、K、V 三副面孔。

```python
Q = X @ Wq    # 每个词「我在找什么」
K = X @ Wk    # 每个词「我能提供什么标签」
V = X @ Wv    # 每个词「真要取用时交出的内容」

scores = Q @ K.T            # 用我的 Q 去碰别人的 K,算出该关注谁
scaled = scores / np.sqrt(d_k)             # 缩放(见下)
weights = np.array([softmax(r) for r in scaled])
Y = weights @ V             # 加权汇总别人的 V
```

> 代码见 [`code/self_attention.py`](code/self_attention.py)

这就是 Transformer 里那行著名公式:

```text
Attention(Q, K, V) = softmax( Q · Kᵀ / √d_k ) · V
```

**为什么要除以 √d_k(缩放)?** 维度 `d_k` 越大,点积的数值越容易变大,softmax 会变得「非 0 即 1」太极端,
梯度也会变小变不稳。除以 √d_k 把数值拉回温和区间。这就是「**scaled** dot-product attention」里 scaled 的由来。

跑出来(`Wq/Wk/Wv` 用固定随机种子生成),`苹果`的注意力分配是:

```text
『苹果』的注意力权重(用它的 Q 去问每个词的 K):
  我   0.089 ██
  吃   0.141 ████
  苹果  0.218 ██████
  了   0.551 ████████████████
```

和第 1 节相比,关注的对象变了——因为现在用的是「Q 去问 K」,而不是「原始向量互相点积」。
`Wq`、`Wk` 不同,词就能**用一种样子去问、用另一种样子被查**,表达力强得多。
(这里矩阵是随机的;真实模型里它们由训练学出,自动学会「该关注谁」。)

---

## 3. 因果掩码:不许偷看未来

语言模型干的事是:看着前面的词,猜下一个词。于是有一条铁律:

> 第 `i` 个词只能看 第 `0..i` 个词,**绝不能看到它后面的词**——否则就是抄答案(标签泄露)。

可第 2 节的注意力是「每个词看所有词」,包括后面的。怎么挡住未来?办法极简单:
**打分之后、softmax 之前,把「未来位置」的分数设成 −∞**。因为 e^(−∞) = 0,
softmax 后这些位置权重正好为 0,等于没看见。

```python
mask = np.tril(np.ones((n, n), dtype=bool))   # 下三角 = 可看的位置
masked = np.where(mask, scores, -np.inf)       # 未来位置设 -inf
weights = np.array([softmax(r) for r in masked])
```

> 代码见 [`code/causal_mask.py`](code/causal_mask.py)

掩码后的权重矩阵,右上三角整片为 0:

```text
掩码后的注意力权重(上三角全为 0):
 [[1.    0.    0.    0.   ]
 [0.398 0.602 0.    0.   ]
 [0.199 0.314 0.486 0.   ]
 [0.493 0.299 0.15  0.058]]
```

逐词看「它能看到谁」:

```text
  第0词 我   -> 我=1.00 吃=0.00 苹果=0.00 了=0.00
  第1词 吃   -> 我=0.40 吃=0.60 苹果=0.00 了=0.00
  第2词 苹果  -> 我=0.20 吃=0.31 苹果=0.49 了=0.00
  第3词 了   -> 我=0.49 吃=0.30 苹果=0.15 了=0.06
```

第 0 个词`我`只能看自己(权重 1.0);越往后,能看的越多。**偷看未来被彻底堵死**——
有了它,模型才能在「不知道答案」的前提下学习猜下一个词,这正是 GPT 的训练方式。

---

## 4. 多头注意力:多个视角一起看

单头只有一套 `Wq/Wk/Wv`,只能学会「一种关注方式」。可一句话里词与词的关系是多种多样的:

- 有的头可能专门盯「主语—谓语」
- 有的头可能专门盯「动词—宾语」
- 有的头可能盯「相邻词」「指代」……

与其逼一套矩阵学会所有关系,不如准备好几套(几个「**头**」),各看各的,
最后把每个头的结果**拼接(concat)**起来,再过一个输出矩阵 `Wo` 融合。

关键点:总维度 `d_model` 被「切」给各头。比如 `d_model=4`、`H=2` 个头,每个头分到 `d_k = 2` 维。
所以多头**不是更贵**,而是把同样的维度「分工」使用。

```python
H = 2
d_k = d_model // H            # 每个头分到 4 // 2 = 2 维
heads_out = [one_head(X, Wq_h, Wk_h, Wv_h, mask) for h in range(H)]
concat = np.concatenate(heads_out, axis=1)   # 拼回 d_model
Y = concat @ Wo                              # 输出矩阵融合各头
```

> 代码见 [`code/multi_head.py`](code/multi_head.py)

跑出来,两个头对`苹果`给出的关注分配**明显不同**:

```text
『苹果』在两个头里的关注分配(看,它们不一样):
  头0: 我=0.70 吃=0.17 苹果=0.13 了=0.00
  头1: 我=0.13 吃=0.57 苹果=0.30 了=0.00
```

头 0 最关注`我`,头 1 最关注`吃`——它们确实学到了不同的关注模式。
这就是 Transformer 的核心积木。

---

## 5. 用 PyTorch 写成一层(nn.Module)

前面 4 个示例用 numpy 把原理拆开看清了。真实项目里,我们会把这套流程封装成一个
**可训练的层**:`Wq/Wk/Wv` 合成一个 `qkv` 线性层、`Wo` 是 `proj` 层,全部是可学习参数,
并且支持**批量(batch)**一次算多句话。输入输出都是 `(B, T, C)` 同形状,所以能一层层叠起来。

```python
class CausalSelfAttention(nn.Module):
    def __init__(self, d_model, n_head):
        super().__init__()
        self.n_head = n_head
        self.d_k = d_model // n_head
        self.qkv = nn.Linear(d_model, 3 * d_model, bias=False)
        self.proj = nn.Linear(d_model, d_model, bias=False)

    def forward(self, x):
        B, T, C = x.shape
        q, k, v = self.qkv(x).split(C, dim=2)
        q = q.view(B, T, self.n_head, self.d_k).transpose(1, 2)
        k = k.view(B, T, self.n_head, self.d_k).transpose(1, 2)
        v = v.view(B, T, self.n_head, self.d_k).transpose(1, 2)
        att = (q @ k.transpose(-2, -1)) / (self.d_k ** 0.5)
        mask = torch.tril(torch.ones(T, T, dtype=torch.bool))
        att = att.masked_fill(~mask, float("-inf")).softmax(dim=-1)
        y = (att @ v).transpose(1, 2).contiguous().view(B, T, C)
        return self.proj(y), att
```

> 代码见 [`code/attention_torch.py`](code/attention_torch.py)

怎么确认写对了?拿 PyTorch 官方算子 `F.scaled_dot_product_attention(..., is_causal=True)` 复算一遍对比:

```text
输入  x 形状: (1, 4, 8)
输出  y 形状: (1, 4, 8) (和输入一致,可以一层层叠起来)
注意力权重 att 形状: (1, 2, 4, 4) = (批量, 头数, 词, 词)
未来部分(严格上三角)之和 = 0.0 -> 应为 0
我们的实现 与 PyTorch 官方 scaled_dot_product_attention 是否一致: True
```

手写结果和官方算子**完全一致**,未来部分权重和为 0——原理吃透了,工程实现也对。

---

## 动手跑一跑

```bash
cd ch06-attention/code

python3 why_attention.py      # 1. 为什么需要注意力(无 Q/K/V)
python3 self_attention.py     # 2. Q/K/V + 缩放点积注意力
python3 causal_mask.py        # 3. 因果掩码:不许偷看未来
python3 multi_head.py         # 4. 多头注意力
python3 attention_torch.py    # 5. PyTorch nn.Module 版,对拍官方算子
```

前 4 个只依赖 numpy;第 5 个需要 PyTorch。

---

## 本章小结

- **注意力的核心动作**:每个词看所有词 → 算相关度 → softmax 归一成权重 → 加权汇总。这样每个词的新表示就**带上了上下文**。
- **Q / K / V**:同一个词向量过三张不同矩阵,得到「查询 / 键 / 值」三副面孔。用 Q·Kᵀ 打分,比直接点积灵活得多。
- **缩放 √d_k**:防止维度一大、点积数值爆炸、softmax 过度极端。完整公式 `softmax(Q·Kᵀ/√d_k)·V`。
- **因果掩码**:打分后把未来位置设 −∞,softmax 后权重为 0。让模型在「不知道答案」的前提下学猜下一个词。
- **多头**:准备 H 套独立 Q/K/V,各看各的,拼接后用 Wo 融合。维度分工,多种视角,几乎不增加开销。
- **工程实现**:封装成 `nn.Module`,输入输出同形状 `(B,T,C)` 可堆叠;手写结果与 PyTorch 官方算子完全一致。

下一章,我们把这块注意力积木和**位置编码 + 残差连接 + LayerNorm + 前馈网络(FFN)**拼在一起,
组成一个完整的 **Transformer Block**——GPT 就是把它叠 N 层堆出来的。

---

上一章 ← [第五章 · 词嵌入](../ch05-embedding/README.md) ｜ 下一章 → [第七章 · Transformer Block](../ch07-transformer-block/README.md)
