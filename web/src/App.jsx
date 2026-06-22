import { useState } from "react";
import Codex from "./components/Codex.jsx";
import { vectorDemo } from "./demos/vectorDot.jsx";
import { matrixDemo } from "./demos/matrixMul.jsx";
import { softmaxDemo } from "./demos/softmax.jsx";
import { gradientDemo } from "./demos/gradientDescent.jsx";
import { shapeDemo } from "./demos/tensorShape.jsx";
import { autogradDemo } from "./demos/autograd.jsx";
import { trainDemo } from "./demos/trainLine.jsx";
import { bigramDistDemo } from "./demos/bigramDist.jsx";
import { bigramGenDemo } from "./demos/bigramGen.jsx";
import { bigramLossDemo } from "./demos/bigramLoss.jsx";
import { charTokDemo } from "./demos/charTok.jsx";
import { bpeDemo } from "./demos/bpe.jsx";
import { tiktokenDemo } from "./demos/tiktokenViz.jsx";
import { embedTableDemo } from "./demos/embedTable.jsx";
import { cosineDemo } from "./demos/cosineSim.jsx";
import { trainEmbedDemo } from "./demos/trainEmbed.jsx";
import { numIdDemo } from "./demos/numIdProblem.jsx";
import { wordPointDemo } from "./demos/wordAsPoint.jsx";
import { attnRawDemo } from "./demos/attnRaw.jsx";
import { attnQkvDemo } from "./demos/attnQkv.jsx";
import { attnMaskDemo } from "./demos/attnMask.jsx";
import { posEncDemo } from "./demos/posEnc.jsx";
import { layerNormDemo } from "./demos/layerNorm.jsx";
import { gptDemo } from "./demos/gptAssemble.jsx";
import { trainGptDemo } from "./demos/trainGpt.jsx";
import { tempDemo } from "./demos/temperature.jsx";
import { topKpDemo } from "./demos/topKp.jsx";
import { loraParamDemo } from "./demos/loraParam.jsx";
import { loraRankDemo } from "./demos/loraRank.jsx";
import { rewardModelDemo } from "./demos/rewardModel.jsx";
import { dpoDemo } from "./demos/dpo.jsx";
import { kvCacheDemo } from "./demos/kvCache.jsx";
import { quantizeDemo } from "./demos/quantize.jsx";
import { ragDemo } from "./demos/rag.jsx";
import { agentDemo } from "./demos/agent.jsx";
import { agentHarnessDemo } from "./demos/agentHarness.jsx";
import { toolUseDemo } from "./demos/toolUse.jsx";
import { memoryStateDemo } from "./demos/memoryState.jsx";
import { reflexionDemo } from "./demos/reflexion.jsx";
import { subAgentDemo } from "./demos/subAgent.jsx";

const LLM_VOLUMES = [
  {
    id: "vol1", name: "卷一 · 数理筑基",
    scrolls: [
      { id: "vec", label: "第一式 · 向量点诀", demo: vectorDemo },
      { id: "mat", label: "第二式 · 矩阵变形", demo: matrixDemo },
      { id: "sm", label: "第三式 · 柔息归元", demo: softmaxDemo },
      { id: "gd", label: "第四式 · 寻谷心法", demo: gradientDemo },
    ],
  },
  {
    id: "vol2", name: "卷二 · 火候初成 (PyTorch)",
    scrolls: [
      { id: "shape", label: "第一式 · 形合之诀", demo: shapeDemo },
      { id: "grad", label: "第二式 · 正反相生", demo: autogradDemo },
      { id: "train", label: "第三式 · 红线归位", demo: trainDemo },
    ],
  },
  {
    id: "vol3", name: "卷三 · 猜字成文 (语言模型)",
    scrolls: [
      { id: "dist", label: "第一式 · 数往知来", demo: bigramDistDemo },
      { id: "gen", label: "第二式 · 无中生有", demo: bigramGenDemo },
      { id: "loss", label: "第三式 · 以损度功", demo: bigramLossDemo },
    ],
  },
  {
    id: "vol4", name: "卷四 · 拆文为号 (分词)",
    scrolls: [
      { id: "char", label: "第一式 · 拆文为号", demo: charTokDemo },
      { id: "bpe", label: "第二式 · 并对成词", demo: bpeDemo },
      { id: "tik", label: "第三式 · 真身现形", demo: tiktokenDemo },
    ],
  },
  {
    id: "vol5", name: "卷五 · 赋字以义 (词嵌入)",
    scrolls: [
      { id: "numid", label: "第一式 · 数字之惑", demo: numIdDemo },
      { id: "point", label: "第二式 · 坐标藏义", demo: wordPointDemo },
      { id: "table", label: "第三式 · 查表取义", demo: embedTableDemo },
      { id: "cos", label: "第四式 · 度义之尺", demo: cosineDemo },
      { id: "train", label: "第五式 · 习而得义", demo: trainEmbedDemo },
    ],
  },
  {
    id: "vol6", name: "卷六 · 顾盼生义 (注意力)",
    scrolls: [
      { id: "raw", label: "第一式 · 顾盼生义", demo: attnRawDemo },
      { id: "qkv", label: "第二式 · 问答相济", demo: attnQkvDemo },
      { id: "mask", label: "第三式 · 隐于未来", demo: attnMaskDemo },
    ],
  },
  {
    id: "vol7", name: "卷七 · 序中藏位 (Transformer Block)",
    scrolls: [
      { id: "pos", label: "第一式 · 序中藏位", demo: posEncDemo },
      { id: "ln", label: "第二式 · 归元固本", demo: layerNormDemo },
    ],
  },
  {
    id: "vol8", name: "卷八 · 万法归一 (完整 GPT)",
    scrolls: [
      { id: "gpt", label: "第一式 · 万法归一", demo: gptDemo },
    ],
  },
  {
    id: "vol9", name: "卷九 · 千锤百炼 (训练 GPT)",
    scrolls: [
      { id: "train", label: "第一式 · 千锤百炼", demo: trainGptDemo },
    ],
  },
  {
    id: "vol10", name: "卷十 · 冷暖自调 (采样)",
    scrolls: [
      { id: "temp", label: "第一式 · 冷暖自调", demo: tempDemo },
      { id: "topkp", label: "第二式 · 去芜存菁", demo: topKpDemo },
    ],
  },
  {
    id: "vol11", name: "卷十一 · 以小驭大 (LoRA)",
    scrolls: [
      { id: "param", label: "第一式 · 以小驭大", demo: loraParamDemo },
      { id: "rank", label: "第二式 · 旁路得道", demo: loraRankDemo },
    ],
  },
  {
    id: "vol12", name: "卷十二 · 合人之意 (对齐)",
    scrolls: [
      { id: "reward", label: "第一式 · 以好恶为尺", demo: rewardModelDemo },
      { id: "dpo", label: "第二式 · 直取人心", demo: dpoDemo },
    ],
  },
  {
    id: "vol13", name: "卷十三 · 又快又省 (推理优化)",
    scrolls: [
      { id: "kv", label: "第一式 · 缓存省算", demo: kvCacheDemo },
      { id: "quant", label: "第二式 · 化整为简", demo: quantizeDemo },
    ],
  },
  {
    id: "vol14", name: "卷十四 · 学以致用 (RAG / Agent)",
    scrolls: [
      { id: "rag", label: "第一式 · 开卷而答", demo: ragDemo },
      { id: "agent", label: "第二式 · 想做相生", demo: agentDemo },
    ],
  },
];

const AGENT_VOLUMES = [
  {
    id: "agent-vol1",
    name: "卷一 · 想做相生 (Harness)",
    scrolls: [
      { id: "harness", label: "想做相生", demo: agentHarnessDemo },
    ],
  },
  {
    id: "agent-vol2",
    name: "卷二 · 立规执器 (工具)",
    scrolls: [
      { id: "tooluse", label: "立规执器", demo: toolUseDemo },
    ],
  },
  {
    id: "agent-vol3",
    name: "卷三 · 分流持态 (记忆)",
    scrolls: [
      { id: "memory", label: "分流持态", demo: memoryStateDemo },
    ],
  },
  {
    id: "agent-vol4",
    name: "卷四 · 败中求正 (反馈)",
    scrolls: [
      { id: "reflexion", label: "败中求正", demo: reflexionDemo },
    ],
  },
  {
    id: "agent-vol5",
    name: "卷五 · 分而委之 (子 Agent)",
    scrolls: [
      { id: "subagent", label: "分而委之", demo: subAgentDemo },
    ],
  },
];

const BOOKS = [
  { id: "llm", title: "大模型卷", volumes: LLM_VOLUMES },
  { id: "agent", title: "Agent 卷", volumes: AGENT_VOLUMES },
];

export default function App() {
  const [bookIndex, setBookIndex] = useState(0);
  const [vol, setVol] = useState(0);
  const [active, setActive] = useState(0);
  const book = BOOKS[bookIndex];
  const volume = book.volumes[vol];
  const scroll = volume?.scrolls[active];

  const switchVol = (i) => { setVol(i); setActive(0); };
  const switchBook = (i) => { setBookIndex(i); setVol(0); setActive(0); };

  return (
    <div className="app">
      <div className="page-inner">
        <header className="app-header">
          <a className="repo-star" href="https://github.com/OpenRaiser/Gewu"
            target="_blank" rel="noreferrer" aria-label="在 GitHub 上 Star Gewu">
            <span className="repo-star-icon">★</span>
            <span>Star</span>
          </a>
          <div className="seal" aria-label="格物致知">
            <span>格</span><span>物</span>
            <span>致</span><span>知</span>
          </div>
          <h1 className="book-title">格物</h1>
          <div className="book-sub">{book.title}{volume ? ` · ${volume.name}` : ""}</div>
          <nav className="book-switch" aria-label="分卷">
            {BOOKS.map((b, i) => (
              <button
                key={b.id}
                className={"book-tab" + (i === bookIndex ? " active" : "")}
                onClick={() => switchBook(i)}
              >
                {b.title}
              </button>
            ))}
          </nav>
        </header>

        <div className="divider">— ❖ 拖动文中朱字 · 或以指掠过经文 · 演武场即时演化 ❖ —</div>

        <div className="book-body">
          <nav className="vol-nav">
            <div className="vol-nav-title">目录</div>
            {book.volumes.length > 0 ? book.volumes.map((v, i) => (
              <button key={v.id}
                className={"vol-tab" + (i === vol ? " active" : "")}
                onClick={() => switchVol(i)}>
                {v.name}
              </button>
            )) : (
              <div className="vol-empty">{book.empty}</div>
            )}
          </nav>

          {volume && scroll ? (
            <Codex
              key={book.id + "-" + volume.id + "-" + scroll.id}
              demo={scroll.demo}
              tabs={
                <nav className="scrolls">
                  {volume.scrolls.map((s, i) => (
                    <button
                      key={s.id}
                      className={"scroll-tab" + (i === active ? " active" : "")}
                      onClick={() => setActive(i)}
                    >
                      {s.label}
                    </button>
                  ))}
                </nav>
              }
            />
          ) : (
            <main className="book-placeholder">
              <h2>{book.empty}</h2>
              <p>先读 Agent 卷正文与实验，待 trace 演武场稳定后接入此处。</p>
            </main>
          )}
        </div>
      </div>
    </div>
  );
}
