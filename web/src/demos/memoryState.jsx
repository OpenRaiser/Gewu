const GENAGENTS_URL = "https://arxiv.org/abs/2304.03442";
const VOYAGER_URL = "https://arxiv.org/abs/2305.16291";

const MODES = [
  { id: "route", label: "合理分流" },
  { id: "dump", label: "全塞 prompt" },
  { id: "traceOnly", label: "只留 trace" },
];

const EVENTS = [
  {
    label: "系统指令", tag: "sys", item: "system prompt + tool schema",
    needNow: true, big: false, progress: false, reusable: false, audit: false,
    context: "system + tools", state: null, memory: null, trace: null,
    note: "固定规则每轮都要给模型；它是 context 的底座，不是长期记忆。",
  },
  {
    label: "当前任务", tag: "task", item: "总结 Agent 卷 Phase 01",
    needNow: true, big: false, progress: true, reusable: false, audit: true,
    context: "goal", state: "current_task", memory: null, trace: "task event",
    note: "任务既要进 context 供下一步决策，也要写 state，便于恢复。",
  },
  {
    label: "模型动作", tag: "act", item: 'read_file("roadmap.md")',
    needNow: true, big: false, progress: true, reusable: false, audit: true,
    context: "last action", state: "last_action", memory: null, trace: "model event",
    note: "action 是当前回合工作材料，trace 也要完整留证。",
  },
  {
    label: "大 observation", tag: "obs!", item: "roadmap 全文 1583 字",
    needNow: true, big: true, progress: true, reusable: false, audit: true,
    context: "obs 摘要", state: "obs_summary", memory: null, trace: "全文 observation",
    note: "大输出不能整段塞回 prompt；摘要进 context/state，全文只进 trace。",
  },
  {
    label: "工具错误", tag: "err", item: "file not found",
    needNow: true, big: false, progress: true, reusable: false, audit: true,
    context: "error obs", state: "error_count", memory: null, trace: "error event",
    note: "错误是下一步修正的证据，也要写入 trace 方便复盘。",
  },
  {
    label: "可复用结论", tag: "skill", item: "Phase 01 = harness loop",
    needNow: false, big: false, progress: false, reusable: true, audit: true,
    context: null, state: null, memory: "harness fact", trace: "distilled insight",
    note: "只有跨任务可复用的结论才进 memory；memory 不是 trace 的复制品。",
  },
  {
    label: "最终答案", tag: "final", item: "三段总结 + status done",
    needNow: false, big: false, progress: true, reusable: false, audit: true,
    context: null, state: "final_answer", memory: null, trace: "final event",
    note: "final 更新当前状态；完整答案仍由 trace 留档。",
  },
];

const lines = [
  { text: "{{mode}}", stage: 0 },
  { text: "next()", stage: 0 },
  { text: "now>ctx", stage: 1 },
  { text: "big>sum", stage: 3 },
  { text: "prog>st", stage: 4 },
  { text: "reuse>mem", stage: 5 },
  { text: "audit>log", stage: 6 },
];

const paramDefs = { mode: { min: 0, max: 2, step: 1, fmt: (v) => MODES[v].label } };
const initial = { mode: 0 };
function compute(p) {
  return { mode: MODES[p.mode].id, modeIndex: p.mode };
}

const COLOR = {
  context: "#9e2b1e",
  state: "#9c7b2e",
  memory: "#3f6b4f",
  trace: "#6b3a2e",
  gate: "#8a7656",
};

const GATES = [
  { key: "needNow", label: "下一步要用?", yes: "context" },
  { key: "big", label: "太大?", yes: "summary" },
  { key: "progress", label: "更新进度?", yes: "state" },
  { key: "reusable", label: "可复用?", yes: "memory" },
  { key: "audit", label: "需审计?", yes: "trace" },
];

function upto(stage) {
  return EVENTS.slice(0, Math.min(EVENTS.length, stage + 1));
}

function buildStores(mode, stage) {
  const seen = upto(stage);
  const trace = seen.filter((e) => e.audit).map((e) => e.tag);

  if (mode === "dump") {
    const context = [];
    seen.forEach((e) => {
      if (!e.needNow) return;
      context.push(e.tag);
      if (e.big) context.push("全文", "全文", "全文");
    });
    const lastProgress = [...seen].reverse().find((e) => e.progress);
    const memory = seen.filter((e) => e.reusable).map((e) => e.tag);
    return {
      context,
      contextOver: context.length > 6,
      contextStatus: context.length > 6 ? "目标/工具被挤" : "仍可读",
      state: lastProgress ? [lastProgress.state] : [],
      memory,
      trace,
    };
  }

  if (mode === "traceOnly") {
    const context = seen.filter((e) => e.label === "系统指令" || e.label === "当前任务").map((e) => e.tag);
    return {
      context,
      contextOver: false,
      contextStatus: stage >= 3 ? "缺 obs 摘要" : "只有初始材料",
      state: [],
      memory: [],
      trace,
    };
  }

  const context = seen
    .filter((e) => e.needNow)
    .map((e) => e.big ? "obs摘要" : e.tag)
    .slice(-4);
  const lastProgress = [...seen].reverse().find((e) => e.progress);
  const memory = seen.filter((e) => e.reusable).map((e) => "skill");
  return {
    context,
    contextOver: false,
    contextStatus: "工作集清爽",
    state: lastProgress ? [lastProgress.state] : [],
    memory,
    trace,
  };
}

function GatePanel({ event }) {
  return (
    <g>
      {GATES.map((g, i) => {
        const y = 80 + i * 28;
        const yes = Boolean(event[g.key]);
        const fill = yes ? "rgba(63,107,79,0.14)" : "#f4ead7";
        const stroke = yes ? "#3f6b4f" : "#cdb98e";
        return (
          <g key={g.key}>
            <rect x="18" y={y - 14} width="132" height="22" rx="4" fill={fill} stroke={stroke} />
            <text x="28" y={y} fill={yes ? "#3f6b4f" : "#8a7656"} fontSize="9.6">{g.label}</text>
            <text x="140" y={y} fill={yes ? "#3f6b4f" : "#b8a888"} fontSize="9" textAnchor="end">
              {yes ? "是" : "否"}
            </text>
          </g>
        );
      })}
    </g>
  );
}

function chipWidth(text) {
  const ascii = String(text).replace(/[^\x00-\x7F]/g, "").length;
  const wide = String(text).length - ascii;
  return Math.max(34, ascii * 4.8 + wide * 8 + 12);
}

function Chip({ x, y, text, color, muted = false, width = chipWidth(text) }) {
  return (
    <g>
      <rect x={x} y={y} width={width} height="16" rx="3" fill={muted ? "#e8ddc8" : color} opacity={muted ? 0.9 : 0.82} />
      <text x={x + width / 2} y={y + 11} fill={muted ? "#8a7656" : "#fff"} fontSize="6.8" textAnchor="middle">{text}</text>
    </g>
  );
}

function StoreBox({ x, y, title, sub, color, items, status, warn }) {
  const visible = items.slice(0, 4);
  let chipX = x + 8;
  const chips = visible.map((item, i) => {
    const width = Math.min(chipWidth(item), x + 152 - chipX);
    const chip = <Chip key={i} x={chipX} y={y + 20} text={item} color={color} muted={item === "全文"} width={width} />;
    chipX += width + 4;
    return chip;
  });
  return (
    <g>
      <rect x={x} y={y} width="168" height="43" rx="5"
        fill={warn ? "rgba(158,43,30,0.08)" : "#fbf6ea"}
        stroke={warn ? "#9e2b1e" : color} strokeWidth={warn ? 1.6 : 1} />
      <text x={x + 8} y={y + 13} fill={color} fontSize="9.7" fontWeight="600">{title}</text>
      <text x={x + 78} y={y + 13} fill="#a8946a" fontSize="7.3">{sub}</text>
      {items.length === 0 ? (
        <text x={x + 8} y={y + 31} fill="#b8a888" fontSize="8">空</text>
      ) : chips}
      {items.length > 4 && <text x={x + 154} y={y + 31} fill="#8a7656" fontSize="7">+{items.length - 4}</text>}
      {status && <text x={x + 160} y={y + 13} fill={warn ? "#9e2b1e" : "#8a7656"} fontSize="7.2" textAnchor="end">{status}</text>}
    </g>
  );
}

function Viz({ derived: d, stage }) {
  const idx = Math.min(EVENTS.length - 1, Math.max(0, stage));
  const event = EVENTS[idx];
  const stores = buildStores(d.mode, idx);
  return (
    <svg viewBox="0 0 360 300" width="360" height="300">
      <text x="16" y="15" fill="#5a4a36" fontSize="10.5">
        信息分拣器 · {MODES[d.modeIndex].label}
      </text>

      <rect x="16" y="26" width="328" height="39" rx="7" fill="#fff6e9" stroke="#9c7b2e" strokeWidth="1.2" />
      <rect x="25" y="36" width="32" height="19" rx="4" fill="#9c7b2e" />
      <text x="41" y="49" fill="#fff" fontSize="7.2" textAnchor="middle">{event.tag}</text>
      <text x="66" y="42" fill="#9c7b2e" fontSize="10" fontWeight="600">
        第 {idx + 1}/{EVENTS.length} 条 · {event.label}
      </text>
      <text x="66" y="56" fill="#5a4a36" fontSize="8.2">{event.item}</text>

      <GatePanel event={event} />

      <path d="M154 139 C171 139 171 139 188 139" fill="none" stroke="#cdb98e" strokeWidth="1.5" />
      <text x="171" y="132" fill="#a8946a" fontSize="8" textAnchor="middle">落盘/回灌</text>

      <StoreBox x={190} y={75} title="context" sub="工作台" color={COLOR.context}
        items={stores.context} status={stores.contextStatus} warn={stores.contextOver} />
      <StoreBox x={190} y={124} title="state.json" sub="当前快照" color={COLOR.state}
        items={stores.state} status={d.mode === "traceOnly" ? "不可恢复" : "覆盖"} warn={d.mode === "traceOnly" && idx >= 3} />
      <StoreBox x={190} y={173} title="memory" sub="经验库" color={COLOR.memory}
        items={stores.memory} status={stores.memory.length ? "提炼后" : "挑食"} />
      <StoreBox x={190} y={222} title="trace.jsonl" sub="审计流水" color={COLOR.trace}
        items={stores.trace} status="append" />

      {d.mode === "dump" && stores.contextOver && (
        <text x="18" y="251" fill="#9e2b1e" fontSize="9.4" fontWeight="600">
          全塞后果：目标和工具规则被大输出挤掉，下一轮易跑偏。
        </text>
      )}
      {d.mode === "traceOnly" && idx >= 3 && (
        <text x="18" y="251" fill="#9e2b1e" fontSize="9.4" fontWeight="600">
          只留 trace：能审计，但下一轮没有状态摘要可恢复。
        </text>
      )}
      {d.mode === "route" && (
        <text x="18" y="251" fill="#8a7656" fontSize="9.2">
          合理分流：context 短、state 可恢复、memory 只收经验、trace 全留。
        </text>
      )}

      <text x="18" y="286" fill="#8a7656" fontSize="8.8">
        Generative Agents: memory stream / reflection / planning · Voyager: skill library
      </text>
    </svg>
  );
}

function frames(params, d) {
  return EVENTS.map((event, i) => {
    let say;
    if (i === 0) {
      say = `第 1 条·<b>${event.label}</b>：规则和工具 schema 是 context 底座。它每轮都要给模型，但不写进 state，也不算长期 memory。`;
    } else if (i === 3) {
      say = d.mode === "dump"
        ? "第 4 条·<b>大 observation</b>：全塞模式把全文直接灌进 context。演武场右上角会开始超载，这就是长任务污染上下文的典型失败。"
        : "第 4 条·<b>大 observation</b>：先过“太大?”关卡，被压成摘要进 context/state；全文进入 trace，既保留证据又不污染 prompt。";
    } else if (i === 5) {
      say = "第 6 条·<b>可复用结论</b>：它不一定影响下一步，但值得跨任务复用，所以提炼成 memory。Voyager 的 skill library 就是这种思路。";
    } else if (i === 6) {
      say = "第 7 条·<b>final</b>：state 覆盖成 status=done + final_answer，trace 追加最终事件。state 是快照，trace 是全史。";
    } else {
      say = `第 ${i + 1} 条·<b>${event.label}</b>：${event.note}`;
    }
    return { line: i + 1, stage: i, say };
  });
}

function note(stage, params, d) {
  switch (stage) {
    case 0:
      return "第三式的核心不是“有四个桶”，而是 harness 对每条信息做分拣判断：下一步需不需要？太不太大？是不是进度？能不能跨任务复用？要不要审计？";
    case 1:
      return "<b>context</b> 是下一步决策的工作台，不是数据库。它应该短、鲜活、直接服务下一轮推理。";
    case 2:
      return "action 进 context 是为了让模型知道刚刚自己做了什么；同时进 trace 是为了后续 debug。它通常不进 memory。";
    case 3:
      return "大 observation 是长任务的分水岭：全塞 prompt 会污染上下文；合理做法是摘要进 context/state，全文只留 trace。";
    case 4:
      return "<b>state.json</b> 不是完整历史，而是当前任务快照：current_task、last_action、last_observation_summary、error_count、status。";
    case 5:
      return `<b>memory</b> 要挑食。<a href="${GENAGENTS_URL}" target="_blank" rel="noreferrer">Generative Agents</a> 把 observation 积累成 memory stream，再检索、反思、规划；<a href="${VOYAGER_URL}" target="_blank" rel="noreferrer">Voyager</a> 把成功经验提炼成 skill library。`;
    case 6:
      return "trace 是 append-only 流水账，适合审计、重放、失败归因；state 是可恢复快照，适合 UI 展示和下一轮 prompt 摘要。两者不能混用。";
    default:
      return "拖朱字切换三种策略：合理分流、全塞 prompt、只留 trace。点演法观察每条信息如何被分拣。";
  }
}

const pyCode = `# 信息分拣器：同一条 info，按用途变形后去不同地方
def route(info, state, memory, trace):
    trace.append(raw(info))                    # 全史: 审计/重放

    if need_now(info):                         # 工作台: 下一步要用
        messages.append(summarize(info) if big(info) else info)

    if progress(info):                         # 快照: 当前可恢复状态
        state.update(summary_fields(info))

    if reusable(info):                         # 经验: 跨任务复用
        memory.add(distill_skill(info))

    return rebuild_context(state, memory)      # 下轮从摘要恢复`;

export const memoryStateDemo = {
  title: "演武场 · 信息分拣器",
  intro: `<p>本式从两篇论文起手：<b><a href="${GENAGENTS_URL}" target="_blank" rel="noreferrer">Generative Agents</a></b> 给出 memory stream → retrieval → reflection → planning 的长期记忆管线；<b><a href="${VOYAGER_URL}" target="_blank" rel="noreferrer">Voyager</a></b> 把成功经验提炼成 skill library。它们共同说明：长任务不是把历史全塞回 prompt，而是要<b>分拣、摘要、落盘、再检索</b>。</p>
<p><b>心法</b>：每条信息先过五问：下一步要用吗？太大吗？是不是当前进度？是否可复用？是否需要审计？然后分别进入 <b>context</b>、<b>state.json</b>、<b>memory</b>、<b>trace.jsonl</b>。</p>
<p><b>四个去处不是四个同类桶</b>：context 是有限工作台；state 是当前快照；memory 是跨任务经验库；trace 是完整审计流水。它们保存的形态不同，回灌方式也不同。</p>
<p class="intro-arena-tip">右侧演武场让一条长任务的 7 张信息纸条逐条通过分拣器。拖 <b>朱字</b>切换「合理分流 / 全塞 prompt / 只留 trace」，看全塞如何挤掉目标，只留 trace 又为何无法恢复状态。</p>`,
  bridge: {
    prev: "第二式：工具层 —— schema 校验 + 结构化 observation。",
    current: "第三式：长任务信息分拣 —— context / state / memory / trace 各司其职。",
    next: "第四式：反思与自我修正（Reflexion / Self-Refine）。",
    sources: ["Generative Agents", "Voyager"],
  },
  lines,
  paramDefs,
  initial,
  compute,
  frames,
  Viz,
  note,
  pyCode,
  playMs: 1400,
  terms: [
    { t: "context", d: "每轮发给模型的工作台：当前目标、工具、最近观察、状态摘要。窗口有限，不能当数据库。" },
    { t: "state.json", d: "当前任务快照：current_task、last_action、last_observation_summary、error_count、status、final_answer。用于恢复和展示。" },
    { t: "memory", d: "跨任务复用经验：用户偏好、项目事实、可复用 skill。需要提炼和检索，不是 trace 复制品。" },
    { t: "trace.jsonl", d: "完整审计流水：task/model/tool/error/final 全留。用于 debug、审计、重放、失败归因。" },
    { t: "summarize", d: "把大 observation 压成摘要进 context/state，全文进 trace。它是防止上下文污染的关键动作。" },
  ],
  localCmd: "cd agent-volume/experiments/minimal-harness && python3 agent.py \"演示 state 和 trace 的区别\" --scripted-demo --reset-trace --reset-state",
};
