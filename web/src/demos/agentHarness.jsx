const REACT_URL = "https://arxiv.org/abs/2210.03629";
const MRKL_URL = "https://arxiv.org/abs/2205.00445";
const TOOLFORMER_URL = "https://arxiv.org/abs/2302.04761";

const READINGS = [
  {
    label: "为何不能只答",
    title: "一问：为什么不能只输出最终答案？",
    short: "缺证据时，直接回答就是猜。",
    arena: ["很多任务要外部证据", "没读文件就答，是猜", "行动让答案落到事实上"],
    detail: "ReAct 的起点不是让模型更会写过程，而是承认很多任务需要外部证据：查文件、查网页、调用 API、运行代码。没有行动，模型只能凭上下文和参数记忆生成，答得像真的，也可能完全没看过事实。",
    takeaway: "先取证，再回答。",
  },
  {
    label: "TAO 解决什么",
    title: "二问：Thought -> Action -> Observation 解决了什么？",
    short: "把推理和外部世界接成闭环。",
    arena: ["Thought 判断缺口", "Action 请求工具", "Observation 带回事实"],
    detail: "Thought 负责判断缺什么信息，Action 负责请求工具，Observation 把环境反馈带回来。模型不再一次性押答案，而是在每次观察后修正下一步。",
    takeaway: "想、做、看，再想。",
  },
  {
    label: "观察如何改判",
    title: "三问：Observation 如何改变下一步推理？",
    short: "Observation 是证据，不是装饰日志。",
    arena: ["成功结果补充事实", "失败结果推翻假设", "空结果迫使换路线"],
    detail: "工具返回的内容会进入下一轮上下文。它可能确认假设，也可能推翻假设：文件不存在、搜索为空、测试失败，都会迫使模型换路线。",
    takeaway: "环境反馈会改写计划。",
  },
  {
    label: "何时应该停止",
    title: "四问：agent 什么时候应该停止？",
    short: "停止条件必须工程化。",
    arena: ["证据足够就 final", "不可恢复报 blocker", "预算耗尽必须硬停"],
    detail: "停止不能只靠模型感觉想完了。证据足够时 final；路径错误时报告 blocker；预算耗尽时硬停；重复调用同一工具时由 harness 干预。",
    takeaway: "final + 预算 + 防循环。",
  },
];

const TRACES = [
  {
    label: "取证成功",
    task: "总结 Phase 01 的学习目标",
    steps: [
      { role: "thought", text: "我需要先看到路线文档。", note: "缺证据" },
      { role: "action", text: 'read_file("agent-volume/roadmap.md")', note: "请求工具" },
      { role: "observation", text: "Phase 01 = Single-Agent Harness", note: "证据回流" },
      { role: "action", text: 'search_text("Phase 01")', note: "补定位" },
      { role: "final", text: "总结目标、论文、完成标准", note: "证据足够" },
    ],
  },
  {
    label: "失败恢复",
    task: "读取一个不存在的章节",
    steps: [
      { role: "thought", text: "我先按用户给的路径读。", note: "初始假设" },
      { role: "action", text: 'read_file("agent-volume/ch99.md")', note: "请求工具" },
      { role: "observation", text: "error: file does not exist", note: "假设失败" },
      { role: "action", text: 'list_files("agent-volume")', note: "换路线" },
      { role: "final", text: "说明 ch99 不存在，并列可用章节", note: "可恢复停止" },
    ],
  },
];

const lines = [
  { text: "paper = \"ReAct\"              # 先读论文,不先堆框架", stage: 0 },
  { text: "question = {{reading}}        # 四问定纲", stage: 1 },
  { text: "thought = ask(\"我缺什么证据?\")", stage: 2 },
  { text: "action = choose_tool(thought) # 模型只提出请求", stage: 3 },
  { text: "observation = harness.run(action)", stage: 4 },
  { text: "state = revise(state, observation)", stage: 5 },
  { text: "if enough_evidence or blocked: final()", stage: 6 },
  { text: "trace.write(thought, action, observation)", stage: 7 },
];

const paramDefs = {
  reading: { min: 0, max: 3, step: 1, fmt: (v) => READINGS[v].label },
  trace: { min: 0, max: 1, step: 1, fmt: (v) => TRACES[v].label },
};

const initial = { reading: 0, trace: 0 };

function compute(params) {
  return {
    reading: READINGS[params.reading],
    trace: TRACES[params.trace],
    readingIndex: params.reading,
  };
}

const roleColor = {
  thought: "#3f6b4f",
  action: "#9c7b2e",
  observation: "#6b3a2e",
  final: "#9e2b1e",
};

function QuestionCards({ active }) {
  return (
    <g>
      {READINGS.map((q, i) => {
        const x = 20 + (i % 2) * 162;
        const y = 42 + Math.floor(i / 2) * 40;
        const hot = i === active;
        return (
          <g key={q.label}>
            <rect x={x} y={y} width="150" height="34" rx="4"
              fill={hot ? "rgba(158,43,30,0.13)" : "#efe6d2"}
              stroke={hot ? "#9e2b1e" : "#cdb98e"} strokeWidth={hot ? 1.3 : 0.8} />
            <text x={x + 8} y={y + 14} fill={hot ? "#9e2b1e" : "#8a7656"} fontSize="9">
              ReAct 四问 · {i + 1}
            </text>
            <text x={x + 8} y={y + 27} fill={hot ? "#9e2b1e" : "#2b2117"} fontSize="10">{q.label}</text>
          </g>
        );
      })}
    </g>
  );
}

const roleLabel = {
  thought: "Thought",
  action: "Action",
  observation: "Observ.",
  final: "Final",
};

function TraceCards({ trace, reveal }) {
  const visible = trace.steps.slice(0, reveal);
  return (
    <g>
      <text x="20" y="160" fill="#5a4a36" fontSize="10.5">演武场任务：{trace.task}</text>
      {visible.length === 0 ? (
        <text x="20" y="184" fill="#8a7656" fontSize="10">
          先读四问，再让 trace 一步步展开。
        </text>
      ) : (
        visible.map((s, i) => {
          const y = 178 + i * 20;
          const color = roleColor[s.role];
          return (
            <g key={i}>
              <circle cx="25" cy={y - 3} r="3.5" fill={color} />
              <text x="33" y={y} fill={color} fontSize="8.5">{roleLabel[s.role]}</text>
              <text x="92" y={y} fill="#2b2117" fontSize="8.5">{s.text}</text>
              <text x="340" y={y} fill="#8a7656" fontSize="8" textAnchor="end">{s.note}</text>
            </g>
          );
        })
      )}
    </g>
  );
}

function Viz({ derived: d, stage }) {
  const reveal = stage < 3 ? 0 : Math.min(d.trace.steps.length, Math.max(1, stage - 2));
  return (
    <svg viewBox="0 0 360 300" width="360" height="300">
      <text x="20" y="16" fill="#5a4a36" fontSize="11">
        论文起手：ReAct · Reasoning and Acting
      </text>
      <text x="20" y="30" fill="#8a7656" fontSize="9">
        arXiv:2210.03629 · 先解读论文，再写 harness
      </text>

      <QuestionCards active={d.readingIndex} />

      <text x="20" y="132" fill="#9e2b1e" fontSize="11">{d.reading.title}</text>
      <rect x="20" y="140" width="320" height="3" fill="#cdb98e" opacity="0.55" />

      {stage <= 2 ? (
        <g>
          {d.reading.arena.map((line, i) => (
            <text key={i} x="20" y={164 + i * 18} fill="#2b2117" fontSize="10.5">{line}</text>
          ))}
          <text x="20" y="226" fill="#3f6b4f" fontSize="11">心法：{d.reading.takeaway}</text>
        </g>
      ) : (
        <TraceCards trace={d.trace} reveal={reveal} />
      )}

      <text x="20" y="286" fill="#8a7656" fontSize="9.5">
        {stage < 3 ? "论文四问给心法定纲；后半段再进入可执行 trace。" : "Thought / Action / Observation 被 harness 记录成可复盘轨迹。"}
      </text>
    </svg>
  );
}

function frames(params, d) {
  return [
    {
      line: 1,
      stage: 0,
      say: `第一章从论文读起：<a href="${REACT_URL}" target="_blank" rel="noreferrer">ReAct</a> 不是“多写几句思考”，而是把推理和行动接成闭环。`,
    },
    {
      line: 2,
      stage: 1,
      say: `先抓四问中的一问：<b>${d.reading.title}</b>。本章所有心法和演武场都围绕这四问展开。`,
    },
    {
      line: 3,
      stage: 2,
      say: `Thought 不是神秘内心戏，而是工程上的“缺口判断”：<b>${d.reading.short}</b>`,
    },
    {
      line: 4,
      stage: 3,
      say: `Action 是模型提出的工具请求。模型不能假装已经读文件或跑命令，真实执行必须交给 harness。当前 trace：<b>${d.trace.steps[1].text}</b>。`,
    },
    {
      line: 5,
      stage: 4,
      say: `Observation 是工具返回的环境事实。它可能是证据，也可能是错误；两者都要回注给模型。`,
    },
    {
      line: 6,
      stage: 5,
      say: "Observation 回注后，模型会修正 state：成功则继续补证据，失败则换工具或报告 blocker。",
    },
    {
      line: 7,
      stage: 6,
      say: "停止条件要工程化：final、证据足够、不可恢复错误、预算耗尽、重复动作检测，都是 harness 的责任。",
    },
    {
      line: 8,
      stage: 7,
      say: "trace 让 agent 可解释：每一步为什么做、做了什么、看见什么、为何停止，都能复盘。",
    },
  ];
}

function note(stage, params, d) {
  switch (stage) {
    case 0:
      return `论文入口：<a href="${REACT_URL}" target="_blank" rel="noreferrer">ReAct: Synergizing Reasoning and Acting in Language Models</a>。先读它，才知道 agent loop 不是框架黑话。`;
    case 1:
      return `<b>${d.reading.title}</b><br/>${d.reading.detail}`;
    case 2:
      return "Thought 在教学里可以写出来；在真实产品里可以只保留结构化 reason / plan，避免暴露完整推理链。重点是让模型知道自己缺什么证据。";
    case 3:
      return "Action 必须机器可解析：工具名、参数、理由。自然语言“我去读一下文件”没有执行意义。";
    case 4:
      return "Observation 要结构化：ok/error、路径、摘要、截断标记。把一大坨 stdout 直接塞回 prompt，会让上下文很快失控。";
    case 5:
      return "ReAct 的精髓在“看见以后改判”。如果 observation 没有改变下一步，那只是把日志贴回模型，不是 agent。";
    case 6:
      return "停止条件不能只靠模型自觉。生产 harness 必须有 max steps、重复动作检测、错误上报和用户授权边界。";
    case 7:
      return `三篇论文的分工：<a href="${REACT_URL}" target="_blank" rel="noreferrer">ReAct</a> 给闭环，<a href="${MRKL_URL}" target="_blank" rel="noreferrer">MRKL</a> 给模块化工具观，<a href="${TOOLFORMER_URL}" target="_blank" rel="noreferrer">Toolformer</a> 说明模型何时学会用工具。`;
    default:
      return "拖动朱字切换 ReAct 四问和 trace 小剧场。";
  }
}

const pyCode = `# 论文四问 -> harness 心法 -> trace 演武场
def run(task, max_steps):
    state = {"goal": task, "evidence": []}
    for step in range(max_steps):
        thought = ask_gap(state)              # 我缺什么证据?
        action = choose_tool(thought)         # 模型提出请求
        observation = harness.run(action)     # harness 真实执行
        trace.write(thought, action, observation)
        state = revise(state, observation)    # 看见以后改判
        if enough_evidence(state) or blocked(state):
            return final(state)
    return stopped_by_budget(state)`;

export const agentHarnessDemo = {
  title: "演武场 · ReAct 四问",
  intro: `Agent 卷第一章从论文起手：先读 <a href="${REACT_URL}" target="_blank" rel="noreferrer">ReAct</a> 的四个问题，再落到心法和演武场。不是先讲框架名词，而是先弄明白：为什么模型要行动、工具返回如何改变判断、何时该停。`,
  bridge: {
    prev: "LLM 卷说明模型如何生成文字。",
    current: "ReAct 四问 -> harness 心法 -> trace 演武场。",
    next: "下一章细讲 tool schema、工具选择和 observation 治理。",
    sources: ["ReAct", "MRKL", "Toolformer"],
  },
  lines,
  paramDefs,
  initial,
  compute,
  frames,
  Viz,
  note,
  pyCode,
  playMs: 1350,
  terms: [
    { t: "ReAct 四问", d: "本章按四个问题读 ReAct：为什么不能只答、TAO 解决什么、Observation 如何改判、什么时候停止。" },
    { t: "Thought", d: "工程上可理解为缺口判断：我现在缺什么证据，下一步该验证什么。" },
    { t: "Action", d: "模型提出的结构化工具请求。真正执行由 harness 完成。" },
    { t: "Observation", d: "工具返回的环境事实。成功、失败、空结果都要回注，供下一轮改判。" },
    { t: "Trace", d: "可复盘轨迹：thought、action、observation、final。它让 agent 从黑箱变成可调试系统。" },
  ],
  localCmd: "cd agent-volume/experiments/minimal-harness && python3 agent.py \"演示 Agent 卷第一章的最小 harness\" --scripted-demo --reset-trace",
};
