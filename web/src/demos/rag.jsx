// 卷十四 · 第一式 · 开卷而答:RAG —— 回答前先检索私有知识库,让答案有出处、少幻觉
// 真实数据来自 ch14/minimal_rag.py:词袋向量 + 余弦相似度,数值由该脚本实测
const DOCS = [
  "年会定在 12 月 20 日晚六点,滨江大酒店三楼宴会厅",
  "报销:OA 提交发票,主管审批,财务每周五打款",
  "公司 WiFi 是 Office_5G,密码 welcome2024",
  "午休 12:00–13:30,健身房在 B 座负一层刷工牌进",
  "请年假需提前三天在 OA 提交,连休超 5 天需总监审批",
];
// 每个问题对 5 条资料的真实余弦相似度(python 实测)
const QS = [
  { q: "WiFi 密码是多少?", sims: [0.075, 0.0, 0.44, 0.0, 0.0] },
  { q: "怎么请年假?", sims: [0.105, 0.0, 0.0, 0.0, 0.354] },
  { q: "年会什么时候?在哪开?", sims: [0.327, 0.085, 0.08, 0.175, 0.183] },
];

const lines = [
  { text: "qi = {{qi}}                    # 选一个问题(拖朱字)", stage: 0 },
  { text: "qv = embed(question)          # 问题变成向量", stage: 1 },
  { text: "sims = [cosine(qv, dv) ...]   # 和每条资料算相似度", stage: 2 },
  { text: "top = argsort(sims)[-k:]      # 取最像的 k 条", stage: 3 },
  { text: "prompt = 资料 + 问题 → LLM    # 照着资料答,有出处", stage: 4 },
];

const paramDefs = { qi: { min: 0, max: 2, step: 1, fmt: (v) => v + 1 } };
const initial = { qi: 0 };

function compute(p) {
  const item = QS[p.qi];
  const order = item.sims.map((s, i) => [s, i]).sort((a, b) => b[0] - a[0]);
  const top1 = order[0][1], top2 = order[1][1];
  return { qi: p.qi, q: item.q, sims: item.sims, top1, top2 };
}

const X0 = 26, BARX = 38, BARW = 150, ROWH = 40, TOP = 78, SIMX = 196;
function Viz({ derived: d, stage }) {
  const showSim = stage >= 2;
  const showTop = stage >= 3;
  const mx = 0.44;
  return (
    <svg viewBox="0 0 360 300" width="360" height="300">
      <text x={X0} y={20} fill="#8a7656" fontSize="12">私有知识库(模型绝没见过)· 问:「{d.q}」</text>
      <text x={X0} y={38} fill="#5a4a36" fontSize="10.5">
        {showSim ? <tspan><tspan fill="#3f6b4f">绿=检索命中(最相似)</tspan> · 浅 = 其余资料</tspan>
          : "把问题和每条资料都变成向量,比相似度"}
      </text>

      {DOCS.map((doc, j) => {
        const y = TOP + j * ROWH;
        const s = d.sims[j];
        const isTop1 = showTop && j === d.top1;
        const isTop2 = showTop && j === d.top2;
        const hit = isTop1 || isTop2;
        const barw = showSim ? Math.max(2, (s / mx) * BARW) : 0;
        return (
          <g key={j}>
            <rect x={BARX} y={y - 14} width={SIMX - BARX - 6} height={ROWH - 8} rx="3"
              fill={hit ? "rgba(63,107,79,0.12)" : "transparent"} stroke={hit ? "#3f6b4f" : "none"} strokeWidth="0.8" />
            <text x={BARX + 4} y={y - 1} fill={hit ? "#2b2117" : "#8a7656"} fontSize="9.5">
              {doc.length > 18 ? doc.slice(0, 18) + "…" : doc}
            </text>
            {/* 相似度条 */}
            <rect x={SIMX} y={y - 12} width={BARW} height={16} rx="3" fill="#efe6d2" stroke="#cdb98e" strokeWidth="0.6" />
            {showSim && (
              <rect x={SIMX} y={y - 12} width={barw} height={16} rx="3"
                fill={hit ? "#3f6b4f" : "#d9cfb6"} style={{ transition: "width .35s ease" }} />
            )}
            {showSim && (
              <text x={SIMX + barw + 5} y={y} fill={hit ? "#3f6b4f" : "#8a7656"} fontSize="9.5">
                {s.toFixed(3)}{isTop1 ? " ◀ top1" : ""}
              </text>
            )}
          </g>
        );
      })}

      {stage >= 4 ? (
        <>
          <text x={X0} y={TOP + 5 * ROWH + 4} fill="#9e2b1e" fontSize="12">
            把 top-{showTop ? 2 : 0} 资料拼进提示词 → 模型照着答
          </text>
          <text x={X0} y={TOP + 5 * ROWH + 22} fill="#8a7656" fontSize="11">答案来自检索到的资料,不是凭记忆编的 → 有出处、少幻觉</text>
        </>
      ) : (
        <text x={X0} y={TOP + 5 * ROWH + 8} fill="#8a7656" fontSize="11">
          {showSim ? "命中的资料相似度明显最高,正好对应问题" : "点「演法」:看检索如何精准命中那一条"}
        </text>
      )}
    </svg>
  );
}

function frames(d0, d) {
  return [
    { line: 1, stage: 0, say: `模型知识停在训练那一刻,你公司的私有文档它<b>一概不知道</b>,硬答还容易幻觉。RAG:回答前<b>先查资料</b>。当前问:「<b>${d.q}</b>」。` },
    { line: 2, stage: 1, say: "第一步<b>检索</b>:把问题和每条资料都<b>变成向量</b>(这里用最朴素的词袋,真实用神经网络嵌入)。" },
    { line: 3, stage: 2, say: `用<b>余弦相似度</b>比问题和每条资料。命中那条相似度 <b>${d.sims[d.top1].toFixed(3)}</b>,明显高出其余——正好对应问题。` },
    { line: 4, stage: 3, say: `取最像的 <b>top-k</b>(这里 k=2)。第一名是第 ${d.top1 + 1} 条,精准命中。「向量化 + 找最近邻」就是检索的核心。` },
    { line: 5, stage: 4, say: "第二步<b>增强生成</b>:把查到的资料拼进提示词,让模型<b>照着答</b>。答案从资料里来、<b>有出处</b>——这就是「让 AI 读你的 PDF/知识库再问答」的底层。" },
  ];
}

function note(stage, p, d) {
  switch (stage) {
    case 0: return "模型两个短板之一:<b>知识冻结</b>(不知新事/私有文档)。RAG 补这个——回答前先检索资料库。拖朱字换问题。";
    case 1: return "<b>检索</b>:问题和每条资料都向量化。本例用词袋(数各字出没),真实 RAG 用神经网络<b>嵌入 + 向量数据库</b>,思想一样。";
    case 2: return `<b>余弦相似度</b>找最像的。命中条相似度 <b>${d.sims[d.top1].toFixed(3)}</b>,远高于其余——检索精准命中。`;
    case 3: return `取 <b>top-k</b>(k=2)塞进提示词。第一名第 ${d.top1 + 1} 条。「向量化 + 找最近邻」是一切 RAG 的内核。`;
    case 4: return "<b>增强生成</b>:资料拼进提示词再交给模型。好处:① 用上没学过的新知识/私有文档 ② 答案有出处、<b>大幅减少幻觉</b>。";
    default: return "拖朱字换问题,点「演法」看检索命中。";
  }
}

const pyCode = `import numpy as np
DOCS = ["...年会...", "...报销...", "WiFi 密码 welcome2024", ...]
def embed(text):                 # 最朴素的词袋向量(真实用神经嵌入)
    v = np.zeros(len(vocab))
    for c in tokenize(text): v[vocab_index[c]] = 1.0
    return v
def cosine(a, b): return a @ b / (norm(a)*norm(b) + 1e-12)
def retrieve(question, k=2):
    qv = embed(question)
    sims = [cosine(qv, dv) for dv in doc_vecs]
    return np.argsort(sims)[::-1][:k]   # 取最像的 k 条
# 问 WiFi 密码 → 命中第 3 条,相似度 0.440(其余近 0)`;

export const ragDemo = {
  title: "演武场 · 开卷而答",
  intro: "模型知识<b>冻结</b>在训练那刻,私有文档它不知道,硬答易幻觉。<b>RAG</b>:回答前先把问题和资料<b>向量化</b>、用<b>余弦相似度</b>检索最相关几条," +
    "拼进提示词再生成——<b>答案有出处</b>。拖动 <b>问题朱字</b>,看检索如何精准命中知识库里那一条。",
  lines, paramDefs, initial, compute, frames, Viz, note, pyCode, playMs: 1150,
  terms: [
    { t: "模型的知识短板", d: "训练完成那刻起,新发生的事、你的私有文档,模型<b>一概不知</b>;凭记忆硬答还容易<b>幻觉</b>。RAG 专补这个短板。" },
    { t: "RAG 两步", d: "① <b>检索</b>:问题和资料都变向量,找最相似的 top-k;② <b>增强生成</b>:把查到的资料拼进提示词再交给模型。就像<b>开卷考试</b>——先翻到相关那页再下笔。" },
    { t: "检索的核心", d: "<b>向量化 + 找最近邻</b>。本例用词袋向量 + 余弦相似度演示;真实 RAG 用神经网络<b>嵌入</b> + 向量数据库,但思想一模一样。" },
    { t: "为什么有用", d: "① 能用上模型<b>没学过</b>的新知识/私有文档;② 答案<b>有出处</b>,大幅减少幻觉。这就是「让 AI 读你的 PDF/知识库再问答」类产品的底层。" },
  ],
  localCmd: "cd ch14-applications/code && python3 minimal_rag.py",
};
