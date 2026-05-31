"""
ch04 · 示例 3:从零实现 BPE(字节对编码)
==========================================
BPE 的思想一句话:**反复把「最常一起出现的相邻一对」合并成一个新 token。**

从最小的单位(单个字符 / 字节)出发,统计哪一对相邻 token 出现得最频繁,
就把这一对合并成一个新符号,加进词表。重复 N 次,就「长」出了一批子词。
  · 常见的组合(如 "ing"、"自然")会被合并成整块 -> 序列变短
  · 生僻词没被合并,仍可由更小的片拼出 -> 不会 OOV

这正是 GPT-2/GPT-3/GPT-4 分词器的核心算法。下面用纯 Python 实现一遍。
"""
from collections import Counter

# 训练语料:重复几次,让某些字符对的频次拉开差距,好观察合并顺序
TEXT = "低头思故乡 低头思故乡 举头望明月 低头思故乡"


def get_stats(ids):
    """统计每一对相邻 token 出现的次数。返回 {(a, b): 次数}。"""
    counts = Counter()
    for a, b in zip(ids, ids[1:]):
        counts[(a, b)] += 1
    return counts


def merge(ids, pair, new_id):
    """把 ids 里所有的 pair=(a,b) 替换成单个 new_id。"""
    out, i = [], 0
    while i < len(ids):
        if i < len(ids) - 1 and ids[i] == pair[0] and ids[i + 1] == pair[1]:
            out.append(new_id)
            i += 2          # 跳过被合并的两个
        else:
            out.append(ids[i])
            i += 1
    return out


# ---------- 训练:从字符出发,做 NUM_MERGES 次合并 ----------
NUM_MERGES = 5

# 初始词表:每个不同字符一个 id(这里直接用字符当初始 token,便于阅读)
vocab = {i: ch for i, ch in enumerate(sorted(set(TEXT)))}
stoi = {ch: i for i, ch in vocab.items()}
ids = [stoi[ch] for ch in TEXT]
base_len = len(ids)

merges = {}   # (a, b) -> new_id,记录合并规则,编码时要按这个顺序复现
print(f"初始:{base_len} 个 token,词表 {len(vocab)} 个\n")
print("开始合并(每次挑当前最高频的相邻对):")

for step in range(NUM_MERGES):
    stats = get_stats(ids)
    if not stats:
        break
    # 选最高频的一对(频次相同就按 id 顺序,保证可复现)
    pair = max(stats, key=lambda p: (stats[p], -p[0], -p[1]))
    new_id = len(vocab)
    merged_str = vocab[pair[0]] + vocab[pair[1]]
    vocab[new_id] = merged_str
    merges[pair] = new_id
    ids = merge(ids, pair, new_id)
    print(f"  第{step+1}次:把 '{merged_str}' (出现 {stats[pair]} 次) 合并为新 token #{new_id}"
          f"  ->  序列剩 {len(ids)} 个")

print(f"\n训练完:序列从 {base_len} 压到 {len(ids)} 个 token,词表长到 {len(vocab)} 个。")
print("学到的合并规则(按先后顺序):")
for (a, b), nid in merges.items():
    print(f"   '{vocab[a]}' + '{vocab[b]}'  ->  '{vocab[nid]}'  (#{nid})")


# ---------- 用学到的规则来 encode / decode ----------
def encode(text):
    """先拆成字符,再按训练时的顺序,能合就合。"""
    ids = [stoi[ch] for ch in text]
    while len(ids) >= 2:
        stats = get_stats(ids)
        # 在「当前能合并的对」里,选最早学会的那条规则(merges 里 id 最小)
        candidates = [(merges[p], p) for p in stats if p in merges]
        if not candidates:
            break
        _, pair = min(candidates)
        ids = merge(ids, pair, merges[pair])
    return ids


def decode(ids):
    return "".join(vocab[i] for i in ids)


sample = "低头思故乡"
enc = encode(sample)
print(f"\n用学到的分词器编码 '{sample}':")
print(f"   token id:{enc}")
print(f"   每块对应:{[vocab[i] for i in enc]}")
print(f"   {len(sample)} 个字 -> {len(enc)} 个 token(常见词被合并了)")
assert decode(encode(sample)) == sample
print("   ✓ decode(encode(x)) == x")

print("""
看明白了吗?BPE 没有任何「语言知识」,它只是在数频次、合并高频对。
跑得够多次,常用词就自然「长」成了整块,生僻字仍能拆成小片 —— 两头的好处都占了。
真实 GPT 在海量文本上做了几万次这样的合并,词表约 5 万~10 万。
""")
