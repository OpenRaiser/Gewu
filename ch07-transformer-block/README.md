# 第七章 · Transformer Block

> 上一章我们打磨出了 GPT 的心脏——**因果多头自注意力**。但光有注意力还不够:
> 它看不出词的**顺序**,本身也只是**线性**的加权平均,而且很多层直接叠起来会**训不动**。
>
> 这一章补齐三块拼图——**位置编码、残差连接 + LayerNorm、前馈网络(FFN)**——
> 然后把它们和注意力组装成一块标准的 **Transformer Block**。这块积木叠 N 层,就是 GPT 的主干。

---

## 1. 位置编码:给词标上「座位号」

注意力有个容易被忽略的「特性」:**它看不出词的顺序**。

回想第六章的打分 `scores = Q·Kᵀ`。如果把句子里的词打乱,每一对词的点积还是那个值,
加权汇总也只是跟着换了顺序。也就是说,「我吃苹果」和「苹果吃我」,在纯注意力眼里几乎一样!
可顺序明明很重要。

解法:给每个**位置**一个独有的「座位号向量」,加到词向量上。原版 Transformer 用一组
**sin / cos 波形**(不同维度用不同频率)——无需学习、任意长度可生成、不同位置各不相同。

```python
def positional_encoding(seq_len, d_model):
    pe = np.zeros((seq_len, d_model))
    pos = np.arange(seq_len)[:, None]
    i = np.arange(0, d_model, 2)
    div = np.power(10000.0, i / d_model)
    pe[:, 0::2] = np.sin(pos / div)   # 偶数维放 sin
    pe[:, 1::2] = np.cos(pos / div)   # 奇数维放 cos
    return pe
```

> 代码见 [`code/positional_encoding.py`](code/positional_encoding.py)

跑出来,位置离得越远,编码差别一般越大:

```text
第 0 位 与 第 1 位 的编码距离: 0.964
第 0 位 与 第 5 位 的编码距离: 1.296
-> 位置离得越远,编码差别一般越大,模型能据此分辨先后。
```

用法极简:`词向量 + 位置编码`(逐元素相加),形状不变,再送进 Transformer。从此同一个词
出现在不同位置,送进注意力的向量就不一样了。

> 另有一种「**可学习位置编码**」:把位置向量当成参数训练。GPT 系列多用这种,下一章会用到。

---

## 2. 残差连接 + LayerNorm:让深网络 train 得动

把很多层直接叠起来,会遇到两个老大难:

1. **越深越难训**:梯度回传层层相乘,容易消失或爆炸,前面的层学不动。
2. **数值分布乱飘**:每层输出有时很大有时很小,训练不稳定。

两件法宝对症下药:

**残差连接(residual)**:`输出 = x + 子层(x)`。给梯度留一条直接绕过子层的「高速公路」,
深层也能稳稳回传;而且子层只需学「在 x 基础上改动多少」(增量),比从零学整个映射容易。

**层归一化(LayerNorm)**:对每个词向量自己那一行,减均值、除标准差,拉回「均值 0、方差 1」,
再乘可学习的 γ、加可学习的 β。

```python
def layer_norm(x, gamma, beta, eps=1e-5):
    mu = x.mean(axis=-1, keepdims=True)
    var = x.var(axis=-1, keepdims=True)
    return gamma * (x - mu) / np.sqrt(var + eps) + beta
```

> 代码见 [`code/layernorm_residual.py`](code/layernorm_residual.py)

不管输入多乱,LayerNorm 都能把它拉回稳定分布:

```text
原始向量 x: [[10.  -3.   0.5  8.  -1.   2. ]]  均值=2.750 标准差=4.706
LayerNorm 后: [[ 1.541 -1.222 -0.478  1.116 -0.797 -0.159]]  均值=-0.000 标准差=1.000
```

现代 GPT 普遍用 **Pre-LN** 写法(先归一化,再进子层,最后加残差),训练更稳:

```text
x = x + sublayer( LayerNorm(x) )
```

---

## 3. 前馈网络(FFN):给每个词「单独深加工」

注意力做的是「加权平均」,本质是**线性**的——光靠它表达力不够。所以每块 Block 里还配一个
**前馈网络(FeedForward)**:一个「先放大、过激活、再缩回」的小 MLP,对**每个词**的向量
单独做非线性加工。常见放大倍数是 **4 倍**。

```python
class FeedForward(nn.Module):
    def __init__(self, d_model, mult=4):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, mult * d_model),   # 放大 4 倍
            nn.GELU(),                            # 非线性激活
            nn.Linear(mult * d_model, d_model),   # 缩回原维度
        )
    def forward(self, x):
        return self.net(x)
```

注意力负责「词与词之间交换信息」,FFN 负责「每个词自己消化吸收」——分工明确。

---

## 4. 组装:一块完整的 Transformer Block

材料齐了。一块 Block 里有两个子层,每个都用「Pre-LN + 残差」包起来:

```python
class TransformerBlock(nn.Module):
    def __init__(self, d_model, n_head):
        super().__init__()
        self.ln1 = nn.LayerNorm(d_model)
        self.attn = CausalSelfAttention(d_model, n_head)
        self.ln2 = nn.LayerNorm(d_model)
        self.ff = FeedForward(d_model)

    def forward(self, x):
        x = x + self.attn(self.ln1(x))   # 子层一:词间信息交换
        x = x + self.ff(self.ln2(x))     # 子层二:逐词非线性加工
        return x
```

> 代码见 [`code/transformer_block.py`](code/transformer_block.py)

跑一块,再叠 3 块,形状始终不变——这正是「能堆叠」的证据:

```text
输入  x 形状: (2, 5, 16)
输出  y 形状: (2, 5, 16) (与输入完全一致 -> 可以无限叠)
这一块 Block 的参数量: 3216

叠 3 块后输出形状: (2, 5, 16) (还是 (B,T,C),稳得很)
```

再验证残差的「保底」作用:把两个子层的输出都置零,整块 Block 应退化成**恒等映射**(输出≈输入):

```text
把两个子层输出都置零后,Block 是否≈恒等(输出≈输入): True
```

这说明:当子层「还没学会发力」时,残差通路保证信息能原样穿过去——深网络因此好训。

---

## 动手跑一跑

```bash
cd ch07-transformer-block/code

python3 positional_encoding.py    # 1. 位置编码:给词标座位号
python3 layernorm_residual.py     # 2. 残差 + LayerNorm
python3 transformer_block.py      # 3. 组装完整 Block,叠 3 层
```

第 1、2 个只依赖 numpy;第 3 个需要 PyTorch。

---

## 本章小结

- **位置编码**:纯注意力对词序不敏感,所以给每个位置一个独有向量加到词向量上。sin/cos 版无需训练、任意长度可生成。
- **残差连接** `x + f(x)`:给梯度一条高速公路,子层只学「增量」,深层也训得动。
- **LayerNorm**:对每个词向量归一化(均值 0、方差 1)再 γ/β 缩放,稳住数值分布。现代用 **Pre-LN**:`x = x + sublayer(LayerNorm(x))`。
- **前馈网络 FFN**:先放大 4 倍、过 GELU、再缩回,补上注意力缺的非线性。
- **Transformer Block** = 注意力子层 + FFN 子层,各用 Pre-LN + 残差包裹。输入输出同为 `(B,T,C)`,可叠 N 层。
- 残差让「子层不发力时 Block ≈ 恒等」,这是深 Transformer 能训得动的关键。

下一章,我们把 **词嵌入 + 位置编码 → N × TransformerBlock → 最后的 LayerNorm → 输出头**
串起来,搭出一个**完整的、能跑的 GPT**。

---

上一章 ← [第六章 · 注意力机制](../ch06-attention/README.md) ｜ 下一章 → [第八章 · 搭出完整 GPT](../ch08-build-gpt/README.md)
