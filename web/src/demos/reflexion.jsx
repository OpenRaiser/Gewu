const REFLEXION_URL = "https://arxiv.org/abs/2303.11366";
const SELF_REFINE_URL = "https://arxiv.org/abs/2303.17651";
const LATS_URL = "https://arxiv.org/abs/2310.04406";

// 两种处理失败的策略
const MODES = [
  { id: "fail", label: "打印即失败" },
  { id: "recover", label: "结构化回注修正" },
];

// recover 场景的真实三步（取自 agent.py scripted_recovery_response 实跑）
// node：落在哪个阶段；err：该步是否产生 ok:false
const STEPS = [
  {
    label: "① action（缺参数）",
    action: '{"action":"read_file","args":{}}',
    obs: '{"ok":false,"error_type":"validation_error","error":"missing required argument for read_file: path"}',
    err: true,
    failNote: "打印即失败：harness 只把错误打出来，循环中断，任务到此结束。",
    recoverNote: "结构化回注：错误包成 observation 进 context，error_count→1，模型据此改判。",
  },
  {
    label: "② 修正后 action",
    action: '{"action":"search_text","args":{"pattern":"Phase 04","path":"agent-volume/roadmap.md","max_matches":5}}',
    obs: '{"ok":true,"matches":[{"path":"agent-volume/roadmap.md","line":...}],"truncated":false}',
    err: false,
    failNote: "（已失败，不会有第二步）",
    recoverNote: "模型读到「缺 path」→ 改用带完整参数的 search_text，这步成功取证。",
  },
  {
    label: "③ final",
    action: '{"action":"final","answer":"恢复演示完成：失败→改判→成功"}',
    obs: "status=done · error_count=1 · steps=3",
    err: false,
    failNote: "（已失败，不会有 final）",
    recoverNote: "证据足够 → final。state 记录 error_count=1，失败与修正都留在 trace。",
  },
];

// 左侧心法经文：feedback-driven 恢复机制
const lines = [
  { text: "obs = run_tool(name, args)            # 工具执行,可能失败", stage: 0 },
  { text: "if observation_has_error(obs):        # ok:false?", stage: 1 },
  { text: "    error_count += 1                  # state 记录失败次数", stage: 2 },
  { text: "messages += structured_obs(obs)       # 错误也回注 context", stage: 3 },
  { text: "# 模型读到错误 -> 生成修正后的 action", stage: 4 },
  { text: "if error_count > THRESHOLD: stop()    # 防无限重试", stage: 5 },
];

const paramDefs = { mode: { min: 0, max: 1, step: 1, fmt: (v) => MODES[v].label } };
const initial = { mode: 1 };
function compute(p) {
  return { mode: MODES[p.mode].id, modeIndex: p.mode };
}

const OK = "#3f6b4f";
const ERR = "#9e2b1e";
const GOLD = "#9c7b2e";

function Viz({ derived: d, stage }) {
  const recover = d.mode === "recover";
  // fail 模式：第1步失败后链路中断，后续步不展示进展
  const idx = Math.min(STEPS.length - 1, Math.max(0, stage));
  const shownIdx = recover ? idx : 0;
  const s = STEPS[shownIdx];
  const dead = !recover && idx > 0;          // fail 模式越过第1步 = 死路
  const errCount = recover
    ? (idx >= 0 ? 1 : 0)
    : 1;
  const obsColor = s.err ? ERR : OK;
  const note = recover ? s.recoverNote : (dead ? "链路已断：错误只被打印，没有回注，模型拿不到修正信号。" : s.failNote);

  return (
    <svg viewBox="0 0 360 300" width="360" height="300">
      <text x="16" y="14" fill="#5a4a36" fontSize="10.5">
        失败恢复 · {MODES[d.modeIndex].label}{recover ? ` · 第 ${idx + 1}/3 步` : ""}
      </text>

      {/* 当前 action 卡 */}
      <rect x="16" y="24" width="328" height="46" rx="7"
        fill="#fff6e9" stroke={GOLD} strokeWidth="1.3" />
      <text x="26" y="40" fill={GOLD} fontSize="10" fontWeight="600">{s.label}</text>
      <foreignObject x="26" y="44" width="308" height="24">
        <div xmlns="http://www.w3.org/1999/xhtml" style={{
          fontFamily: "ui-monospace, Menlo, monospace", fontSize: "8.6px",
          lineHeight: "1.35", color: "#5a4a36", wordBreak: "break-all",
        }}>{s.action}</div>
      </foreignObject>

      {/* 向下箭头 */}
      <line x1="180" y1="70" x2="180" y2="86" stroke={obsColor} strokeWidth="1.4" />
      <path d={`M176 82 L180 88 L184 82`} fill="none" stroke={obsColor} strokeWidth="1.4" />

      {/* observation 卡 */}
      <rect x="16" y="90" width="328" height="50" rx="7"
        fill={s.err ? "rgba(158,43,30,0.06)" : "rgba(63,107,79,0.06)"}
        stroke={obsColor} strokeWidth="1.4" />
      <text x="26" y="106" fill={obsColor} fontSize="10" fontWeight="600">
        observation · {s.err ? "ok:false（错误）" : "ok:true / done"}
      </text>
      <foreignObject x="26" y="110" width="308" height="28">
        <div xmlns="http://www.w3.org/1999/xhtml" style={{
          fontFamily: "ui-monospace, Menlo, monospace", fontSize: "8.2px",
          lineHeight: "1.35", color: "#2b2117", wordBreak: "break-all",
        }}>{s.obs}</div>
      </foreignObject>

      {/* 恢复回路：错误 -> 回注 -> 改判 */}
      {s.err && (
        recover ? (
          <g>
            <path d="M16 115 C 6 115 6 50 16 50" fill="none" stroke={ERR}
              strokeWidth="1.5" strokeDasharray="4 3" />
            <path d="M12 56 L16 48 L20 56" fill="none" stroke={ERR} strokeWidth="1.5" />
            <text x="8" y="86" fill={ERR} fontSize="8.4" transform="rotate(-90 8 86)">
              结构化回注 → 改判
            </text>
          </g>
        ) : (
          <g>
            <line x1="150" y1="150" x2="210" y2="178" stroke={ERR} strokeWidth="2" />
            <line x1="210" y1="150" x2="150" y2="178" stroke={ERR} strokeWidth="2" />
            <text x="220" y="168" fill={ERR} fontSize="10" fontWeight="700">链路中断</text>
          </g>
        )
      )}

      {/* 下半：结果区 */}
      {recover && idx >= 1 && (
        <foreignObject x="16" y="156" width="328" height="40">
          <div xmlns="http://www.w3.org/1999/xhtml" style={{
            fontFamily: "var(--serif)", fontSize: "9.6px",
            lineHeight: "1.45", color: "#8a7656",
          }}>↳ {note}</div>
        </foreignObject>
      )}
      {(!recover || idx === 0) && (
        <foreignObject x="16" y="190" width="328" height="40">
          <div xmlns="http://www.w3.org/1999/xhtml" style={{
            fontFamily: "var(--serif)", fontSize: "9.6px",
            lineHeight: "1.45", color: "#8a7656",
          }}>↳ {note}</div>
        </foreignObject>
      )}

      {/* error_count 计数器 + 阈值 */}
      <text x="16" y="250" fill="#5a4a36" fontSize="9.5">state.error_count：</text>
      {[0, 1, 2].map((i) => (
        <rect key={i} x={120 + i * 16} y={242} width="12" height="12" rx="2"
          fill={i < errCount ? ERR : "#ece2cc"}
          stroke={i === 2 ? ERR : "#cdb98e"} strokeWidth={i === 2 ? 1.2 : 0.8}
          strokeDasharray={i === 2 ? "2 2" : "none"} />
      ))}
      <text x="176" y="251" fill="#a8946a" fontSize="8.2">超阈值即停止，防无限重试</text>

      <text x="16" y="282" fill={recover ? OK : ERR} fontSize="9.5">
        {recover
          ? "错误→结构化回注→改判→成功：失败成了下一步的决策信号。"
          : "只打印错误：模型拿不到修正信号，一步错→一路断。"}
      </text>
    </svg>
  );
}

function frames(params, d) {
  const recover = d.mode === "recover";
  return [
    { line: 1, stage: 0, say: recover
        ? `第 1 步：模型调 <code>read_file</code> 但<b>漏了必填 path</b>。harness 执行后得到 <b>ok:false</b> 的 observation——这是<b>环境反馈</b>，最可靠的一类。`
        : `第 1 步：模型调 <code>read_file</code> 漏了 path。这一版 harness 只把错误<b>打印</b>出来，不回注。` },
    { line: 2, stage: 1, say: `<code>observation_has_error</code> 判断 <code>ok is False</code>。<b>反馈不等于模型自言自语</b>：环境反馈 &gt; verifier &gt; 纯自评，这里是最硬的环境反馈。` },
    { line: 3, stage: 2, say: recover
        ? `<code>error_count += 1</code>。state 记录失败次数，既用于<b>防无限重试</b>，也是 <a href="${REFLEXION_URL}" target="_blank" rel="noreferrer">Reflexion</a> 式“把失败变经验”的最小雏形。`
        : `打印模式下没有 error_count、没有回注。错误信息<b>丢失</b>，模型下一轮看不到它，<b>无从修正</b>。` },
    { line: 4, stage: 3, say: recover
        ? `关键一步：错误<b>结构化回注进 context</b>。模型这才“看见”自己缺了 path——<code>tool error → observation → 模型看到 → 修正 action</code>。`
        : `<b>链路中断</b>：错误没有进入下一轮 context。这正是“打印即失败”和“可恢复 agent”的分界。` },
    { line: 5, stage: recover ? 4 : 3, say: recover
        ? `第 2 步：模型读到「缺 path」，<b>改用带完整参数的 search_text</b>，成功取证。失败成了有用的决策信号，而非终点。`
        : `没有回注就没有改判。Reflexion / Self-Refine / LATS 再强，也都建立在“反馈能回到下一步”这个前提上。` },
    { line: 6, stage: 5, say: recover
        ? `第 3 步 <code>final</code>，<code>error_count=1</code>、status=done。若失败反复累积超阈值，harness 会<b>停止或求助用户</b>，而不是无限重试。`
        : `兜底：即便可恢复，也要设失败阈值。<a href="${LATS_URL}" target="_blank" rel="noreferrer">LATS</a> 这类多路径探索更强但更贵，必须和预算一起看。` },
  ];
}

function note(stage, params, d) {
  switch (stage) {
    case 0:
      return "本章主线：让失败变成<b>下一步可用的决策信号</b>。<a href=\"" + REFLEXION_URL + "\" target=\"_blank\" rel=\"noreferrer\">Reflexion</a> 把失败总结成经验、<a href=\"" + SELF_REFINE_URL + "\" target=\"_blank\" rel=\"noreferrer\">Self-Refine</a> 生成-自评-修改、<a href=\"" + LATS_URL + "\" target=\"_blank\" rel=\"noreferrer\">LATS</a> 把行动空间当搜索树。";
    case 1:
      return "<b>三类反馈</b>：环境反馈（工具/测试/文件系统，最可靠）、verifier 反馈（规则/测试器/另一模型）、自我反馈（模型自评，不能替代事实验证）。本例 ok:false 属于<b>环境反馈</b>。";
    case 2:
      return "<b>Reflexion</b> 的工程雏形：失败不立刻改参数，而是把失败信息留存（这里是 error_count + trace）。可多次尝试、有明确成败信号的任务最适合。";
    case 3:
      return "可恢复 agent 的硬要求：<b>错误必须结构化、必须进入下一轮 context</b>。只 print 不回注，模型就拿不到修正信号——这也是 ch02 结构化 observation 的用武之地。";
    case 4:
      return "<b>Self-Refine</b> 是“生成→自评→修改”的自我编辑循环，适合写作/总结/草稿代码；但<b>自评不等于正确</b>，无外部验证时容易越改越偏、形成自洽幻觉。";
    case 5:
      return "<b>LATS</b> 把“下一步做什么”变成树搜索（候选行动→observation→打分→选择/回溯），降低单路径错误风险，但模型调用、工具调用、状态管理成本都上升，<b>必须配 max branches / depth / budget</b>。";
    default:
      return "拖朱字对比「打印即失败 / 结构化回注修正」，点演法走 recover 三步。";
  }
}

const pyCode = `# agent.py · 失败恢复（recover 场景实跑）
obs = run_tool(name, args)                 # 第1步: read_file 缺 path
if observation_has_error(obs):             # ok:false ?
    state["error_count"] += 1              # 记录失败次数
messages += structured_obs(obs)            # 错误也回注 context
# 模型读到 "missing path" -> 改用 search_text(带完整参数)  第2步
# observation 足够 -> final                                第3步
if state["error_count"] > THRESHOLD:       # 防无限重试
    stop("too_many_errors")
# 关键: 失败被回注成下一步的决策信号, 而不是直接中断`;

export const reflexionDemo = {
  title: "演武场 · 失败恢复闭环",
  intro: `<p>本式从三篇论文起手：<b><a href="${REFLEXION_URL}" target="_blank" rel="noreferrer">Reflexion</a></b>（失败后用语言总结经验、下次回灌）、<b><a href="${SELF_REFINE_URL}" target="_blank" rel="noreferrer">Self-Refine</a></b>（生成→自评→修改的迭代）、<b><a href="${LATS_URL}" target="_blank" rel="noreferrer">LATS</a></b>（把推理-行动-规划统一成树搜索）。它们共同回答：agent 如何<b>利用反馈改进下一步</b>。</p>
<p>前三式搭好了 loop、工具层和状态分流。本式补上让 agent 真正“能修正”的机制：<b>action → 错误/反馈 → 修订计划 → 下一步</b>。</p>
<p><b>核心判断</b>：关键不是“模型会反思”，而是 harness 能把<b>环境反馈、错误、验证结果</b>变成下一步可用的决策信号。失败若只被打印，链路就断了；失败若被<b>结构化回注</b>，模型才能改判。</p>
<p><b>三类反馈可靠性</b>：环境反馈（工具/测试）&gt; verifier 反馈 &gt; 纯自我反馈。自评不能替代外部验证。</p>
<p class="intro-arena-tip">右侧演武场用实验的 recover 场景（缺参数失败→改判→成功，输出取自实跑 <code>agent.py</code>）。拖 <b>朱字</b>对比「打印即失败 / 结构化回注修正」，点演法走三步。</p>`,
  bridge: {
    prev: "第三式：信息分流 —— context / state / memory / trace。",
    current: "第四式：失败恢复闭环 —— 反馈/错误/验证变成下一步决策信号。",
    next: "第五式：子代理与任务分解（sub-agent / orchestration）。",
    sources: ["Reflexion", "Self-Refine", "LATS"],
  },
  lines,
  paramDefs,
  initial,
  compute,
  frames,
  Viz,
  note,
  pyCode,
  playMs: 1450,
  terms: [
    { t: "ReAct", d: "边想边行动，用 observation 更新下一步。本卷第一式的最小闭环，但它不保证每步都对、不保证从错误中学习。" },
    { t: "Reflexion", d: "失败后用语言把原因总结成经验，下次尝试回灌。适合可多次尝试、有明确成败信号的任务。需真实反馈支撑，否则只是自言自语。" },
    { t: "Self-Refine", d: "生成→自评→修改的自我编辑循环，适合写作/总结/草稿代码。风险：自评不等于正确，无外部验证时易越改越偏。" },
    { t: "LATS", d: "把行动空间当搜索树：候选行动→observation→打分→选择/回溯。降低单路径错误风险，但成本显著上升，必须配预算上限。" },
    { t: "三类反馈", d: "环境反馈（工具/测试/文件系统，最可靠）、verifier 反馈（规则/测试器/另一模型）、自我反馈（模型自评，不替代事实验证）。" },
    { t: "error_count", d: "state 中记录的失败次数。既是 Reflexion 式“留存失败”的雏形，也用于设阈值防无限重试。" },
  ],
  localCmd: "cd agent-volume/experiments/minimal-harness && python3 agent.py \"演示失败后恢复\" --scripted-demo --scripted-scenario recover --reset-trace --reset-state",
};
