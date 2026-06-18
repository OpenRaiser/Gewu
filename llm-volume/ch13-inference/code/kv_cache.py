"""
ch13 · 示例 1:KV cache —— 别再重算了,把算过的 K、V 存起来
==============================================================
模型训好、对齐好了,真要拿来用,就得**一个字一个字地生成**(自回归)。
这里藏着一个巨大的浪费。

回忆第六章:注意力要算 Q、K、V。生成第 t 个字时,模型要看前面所有字:
  · 第 1 步:处理 "白"        -> 算 1 个字的 K、V
  · 第 2 步:处理 "白日"      -> 又把 "白" 的 K、V 从头算了一遍,加上 "日"
  · 第 3 步:处理 "白日依"    -> "白日" 的 K、V 第三次重算...
每多生成一个字,前面所有字的 K、V 就被**整个重算一遍**。越往后越慢,纯属浪费。

KV cache 的主意特别朴素:**K、V 算过一次就存起来(缓存)**,下一步只算新字那一个,
把它的 K、V 追加进缓存就行。本示例手写一个最小注意力,对比「每步重算」和「用缓存」,
核对两者结果完全一致,再看省了多少计算。
"""
import numpy as np

np.set_printoptions(precision=3, suppress=True)
rng = np.random.default_rng(0)

d_model = 8
Wq = rng.standard_normal((d_model, d_model)) * 0.5
Wk = rng.standard_normal((d_model, d_model)) * 0.5
Wv = rng.standard_normal((d_model, d_model)) * 0.5


def softmax(z):
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


# ---------- 方式 A:没有缓存,每生成一步都把整个序列从头算 ----------
def attention_no_cache(seq):
    """seq: (T, d_model)。返回最后一个位置的注意力输出。每步都重算全部 K、V。"""
    Q = seq @ Wq                       # (T, d) —— 其实只需要最后一行,但这里全算了
    K = seq @ Wk                       # (T, d) —— 整段重算
    V = seq @ Wv                       # (T, d) —— 整段重算
    q_last = Q[-1]                     # 只有最后一个字要预测下一个
    scores = q_last @ K.T / np.sqrt(d_model)   # 它和前面所有字的相关度
    return softmax(scores) @ V         # 加权汇总


# ---------- 方式 B:带 KV cache,只算新字,把 K、V 追加进缓存 ----------
class KVCache:
    def __init__(self):
        self.K = None                  # 缓存:已经算过的所有 K
        self.V = None                  # 缓存:已经算过的所有 V

    def step(self, new_token):
        """只接收新来的那一个字 (d_model,),只算它的 q/k/v,复用缓存里的旧 K、V。"""
        q = new_token @ Wq
        k = new_token @ Wk             # 只算新字这一个 k
        v = new_token @ Wv             # 只算新字这一个 v
        self.K = k[None, :] if self.K is None else np.vstack([self.K, k])  # 追加,不重算
        self.V = v[None, :] if self.V is None else np.vstack([self.V, v])
        scores = q @ self.K.T / np.sqrt(d_model)
        return softmax(scores) @ self.V


# ---------- 模拟逐字生成,两种方式核对结果是否一致 ----------
T = 6
tokens = rng.standard_normal((T, d_model))     # 假装这是逐步生成出来的 6 个字的向量
cache = KVCache()
print("逐字生成,核对「每步重算」vs「用缓存」的输出是否一致:\n")
all_same = True
recompute_kv = 0      # 方式 A 累计算了多少个字的 K、V
cached_kv = 0         # 方式 B 累计算了多少个字的 K、V
for t in range(T):
    out_a = attention_no_cache(tokens[:t + 1])     # 看 0..t 整段
    out_b = cache.step(tokens[t])                  # 只喂新字
    same = np.allclose(out_a, out_b)
    all_same = all_same and same
    recompute_kv += (t + 1)                        # 重算了 t+1 个字的 K、V
    cached_kv += 1                                 # 只算了 1 个新字
    print(f"  第 {t+1} 步:序列长 {t+1}  两种方式输出一致 = {same}")

print(f"\n全程输出完全一致: {all_same}  <- 缓存不改变结果,只省计算")
print("\n===== 算了多少个字的 K、V(越小越省)=====")
print(f"  每步重算(无缓存): {recompute_kv} 个   <- 1+2+3+...+T,随长度平方增长")
print(f"  用 KV cache       : {cached_kv} 个   <- 每步只算 1 个新字,线性增长")
print(f"  省下              : {recompute_kv - cached_kv} 个字的重复计算")

print("""
小结:
  · 自回归生成天然爱重算:每吐一个字,前面所有字的 K、V 又被从头算一遍。
  · KV cache:K、V 算过就存,下一步只算新字那一个,追加进缓存——结果一模一样。
  · 计算量从「随长度平方增长」降到「随长度线性增长」,生成越长省得越多。
  · 代价是显存:得把所有历史 K、V 存着。这也是长上下文很吃显存的根本原因之一。
  · 几乎所有 LLM 推理框架(vLLM、TensorRT-LLM...)都把 KV cache 当作头号优化。
""")
