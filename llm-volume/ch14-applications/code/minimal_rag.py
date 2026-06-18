"""
ch14 · 示例 1:最小 RAG —— 先查资料,再回答
============================================
模型本身已经讲透了。但光有模型不够,它有两个天生的短板:
  · 知识停在训练那一刻,新发生的事、你私有的文档,它一概不知道;
  · 凭记忆硬答容易「一本正经地胡说」(幻觉)。

RAG(Retrieval-Augmented Generation,检索增强生成)的主意很直接:
**回答之前,先去一个资料库里查最相关的几条,把它们塞进提示词,再让模型照着答。**
就像开卷考试——不靠死记硬背,而是先翻到相关那页,再下笔。

一套最小 RAG 就两步:
  1) 检索(Retrieval):把问题和每条资料都变成向量,找最相似的几条;
  2) 增强生成(Augmented Generation):把查到的资料拼进提示词,交给模型。
本示例手写「检索」这一核心(用最简单的词袋向量 + 余弦相似度),
生成那一步用一个「假模型」演示——重点是看清:**答案是从检索到的资料里来的,不是编的。**
"""
import numpy as np

np.set_printoptions(precision=3, suppress=True)

# ---------- 0. 一个小小的「私有知识库」(模型训练时绝不可能见过)----------
DOCS = [
    "我们公司的年会定在 12 月 20 日晚上六点,地点是滨江大酒店三楼宴会厅。",
    "报销流程:先在 OA 系统提交发票,主管审批后,财务每周五统一打款。",
    "公司 WiFi 名称是 Office_5G,密码是 welcome2024,访客网络无需密码。",
    "午休时间为 12 点到 13 点半,健身房在 B 座负一层,刷工牌进入。",
    "请年假需提前三天在 OA 提交,连休超过五天的需要总监审批。",
]

# ---------- 1. 把文本变成向量:最朴素的「词袋」----------
# 真实 RAG 用神经网络做的「嵌入(embedding)」,这里用最简单的方式抓住核心:
# 建一个词表,每条文本数一数各词出现没出现,变成一个 0/1 向量。
def tokenize(text):
    # 中文按字切就够演示了(去掉标点),真实场景会用更好的分词/子词
    return [c for c in text if c not in "，。:、 "]

vocab = sorted(set(c for d in DOCS for c in tokenize(d)))
vocab_index = {c: i for i, c in enumerate(vocab)}

def embed(text):
    v = np.zeros(len(vocab))
    for c in tokenize(text):
        if c in vocab_index:           # 问题里可能有库中没见过的字,跳过
            v[vocab_index[c]] = 1.0
    return v

doc_vecs = np.array([embed(d) for d in DOCS])

# ---------- 2. 检索:问题向量和每条资料算余弦相似度,取最像的 top-k ----------
def cosine(a, b):
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-12
    return float(a @ b / denom)

def retrieve(question, k=2):
    qv = embed(question)
    sims = [cosine(qv, dv) for dv in doc_vecs]
    top = np.argsort(sims)[::-1][:k]   # 相似度最高的 k 条
    return [(i, sims[i]) for i in top]

# ---------- 3. 增强生成:把查到的资料拼进提示词,再「回答」----------
def fake_llm(prompt):
    """假模型:真实里这是个 GPT。这里直接回显它「被喂了哪些资料」,以看清 RAG 的本质。"""
    return "(模型据此作答)" + prompt.split("【资料】")[1].split("【问题】")[0].strip()

def rag_answer(question, k=2):
    hits = retrieve(question, k)
    context = "\n".join(f"- {DOCS[i]}" for i, _ in hits)
    prompt = f"请只根据以下资料回答问题。\n【资料】\n{context}\n【问题】{question}"
    return hits, prompt, fake_llm(prompt)

# ---------- 跑几个问题看看 ----------
for q in ["年会是什么时候?在哪里开?", "WiFi 密码是多少?", "怎么请年假?"]:
    hits, prompt, ans = rag_answer(q, k=2)
    print(f"问题:{q}")
    print("  检索到最相关的资料(按相似度):")
    for i, s in hits:
        print(f"    相似度 {s:.3f} | {DOCS[i]}")
    print(f"  -> 喂给模型后回答:{ans}\n")

print("""
小结:
  · RAG = 先检索、再生成。回答前先去资料库查最相关的几条,塞进提示词,让模型照着答。
  · 检索的核心:把问题和资料都变成向量,用相似度(这里是余弦)找最像的 top-k。
    真实场景用神经网络嵌入 + 向量数据库,但「向量化 + 找最近」的思想一模一样。
  · 好处:① 能用模型没学过的新知识/私有文档;② 答案有出处,大幅减少幻觉。
  · 这就是为什么「让 AI 读你的 PDF / 知识库再问答」的产品,底层几乎都是 RAG。
""")
