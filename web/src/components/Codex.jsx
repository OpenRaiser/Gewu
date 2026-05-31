import { useState, useMemo, useRef, useEffect } from "react";
import LiveNum from "./LiveNum.jsx";
import { highlightLine } from "../lib/highlight.js";
import { BridgePanel } from "./TracePanels.jsx";

function renderLine(text, params, paramDefs, setParam) {
  const parts = text.split(/(\{\{\w+\}\})/g);
  return parts.map((part, i) => {
    const m = part.match(/^\{\{(\w+)\}\}$/);
    if (m) {
      const key = m[1];
      const def = paramDefs[key];
      return (
        <LiveNum key={i} value={params[key]} min={def.min} max={def.max}
          step={def.step} fmt={def.fmt} onChange={(v) => setParam(key, v)} />
      );
    }
    const toks = highlightLine(part);
    return toks.map((tk, j) => (
      <span key={i + "-" + j} className={tk.c}>{tk.t}</span>
    ));
  });
}

export default function Codex({ demo, tabs }) {
  const { title, intro, bridge, lines, paramDefs, initial, compute, frames, Viz, note, terms, playMs } = demo;
  const [params, setParams] = useState(initial);
  const [hoverStage, setHoverStage] = useState(lines.find((l) => l.stage != null)?.stage ?? null);
  const [playIdx, setPlayIdx] = useState(null);   // null = 未在演法
  const [paused, setPaused] = useState(false);
  const timer = useRef(null);
  const setParam = (k, v) => setParams((p) => ({ ...p, [k]: v }));

  const derived = useMemo(() => compute(params), [params, compute]);
  // 演法序列由当前参数实时算出:拖动参数后再演,即演「新过程」。
  const seq = useMemo(() => (frames ? frames(params, derived) : []), [params, derived, frames]);

  const atEnd = playIdx != null && playIdx >= seq.length - 1;

  // 播放循环:未暂停且未到末帧时,逐帧推进。
  useEffect(() => {
    if (playIdx == null || paused) return;
    if (playIdx >= seq.length - 1) return;
    timer.current = setTimeout(() => setPlayIdx((i) => i + 1), playMs || 950);
    return () => clearTimeout(timer.current);
  }, [playIdx, paused, seq.length, playMs]);

  // 一个按钮三态:起演 / 暂停 / 续演(到末帧再点则重演)。
  const onPlayBtn = () => {
    if (playIdx == null || atEnd) { setPaused(false); setPlayIdx(0); }
    else if (!paused) { setPaused(true); clearTimeout(timer.current); }
    else setPaused(false);
  };
  const stepBack = () => { setPaused(true); setPlayIdx((i) => Math.max(0, i - 1)); };
  const stepFwd = () => { setPaused(true); setPlayIdx((i) => Math.min(seq.length - 1, i + 1)); };
  const stopPlay = () => { clearTimeout(timer.current); setPlayIdx(null); setPaused(false); };

  const frame = playIdx != null ? seq[Math.min(playIdx, seq.length - 1)] : null;
  const effStage = frame ? frame.stage : hoverStage;
  const noteHtml = frame ? frame.say : note(hoverStage, params, derived);

  const onHover = (line) => {
    if (playIdx != null) return;   // 演法进行时,不被悬停打断
    if (line.stage != null) setHoverStage(line.stage);
  };

  return (
    <>
      <div className="middle">
        {tabs}
        <div className="scroll-intro" dangerouslySetInnerHTML={{ __html: intro }} />
        <BridgePanel bridge={bridge} />
        <div className="codex-pair">
          <div className="zone-code">
            <div className="section-label">心法 · 经文</div>
            <div className="manual">
              {lines.map((line, i) => {
                const lineNo = i + 1;
                const active = frame ? frame.line === lineNo
                  : (effStage != null && line.stage === effStage);
                return (
                  <div key={i} className={"manual-line" + (active ? " active" : "")}
                    onMouseEnter={() => onHover(line)}>
                    <span className="ln">{lineNo}</span>
                    <span className="src">
                      {renderLine(line.text, params, paramDefs, setParam)}
                      {line.text === "" ? " " : ""}
                    </span>
                  </div>
                );
              })}
            </div>
            <div className="play-bar">
              <button className="btn-play" onClick={onPlayBtn}>
                {playIdx == null || atEnd ? "演法 ▶" : paused ? "续演 ▶" : "暂停 ❙❙"}
              </button>
              {playIdx != null && (
                <>
                  <button className="btn-play ghost" onClick={stepBack}>◀ 退</button>
                  <button className="btn-play ghost" onClick={stepFwd}>进 ▶</button>
                  <button className="btn-play ghost" onClick={stopPlay}>收功</button>
                  <span className="play-count">第 {Math.min(playIdx + 1, seq.length)} / {seq.length} 招</span>
                </>
              )}
            </div>
          </div>

          <div className="zone-arena">
            <div className="section-label">{title}</div>
            <div className="arena">
              <Viz params={params} derived={derived} stage={effStage} play={frame} />
            </div>
          </div>
        </div>
        <p className="tip-banner">
          研习无须按序 · 改一字而万象随之而动 · 此谓「实时映射」之妙
        </p>
      </div>

      <aside className="zone-notes">
        <div className="section-label">批注 · 释义</div>
        <div className="note">
          <span className="label">批注</span>
          <span dangerouslySetInnerHTML={{ __html: noteHtml }} />
        </div>

        {terms && terms.length > 0 && (
          <div className="glossary">
            <div className="glossary-title">释义 · 小词典</div>
            <dl>
              {terms.map((t, i) => (
                <div key={i} className="gloss-item">
                  <dt dangerouslySetInnerHTML={{ __html: t.t }} />
                  <dd dangerouslySetInnerHTML={{ __html: t.d }} />
                </div>
              ))}
            </dl>
          </div>
        )}
      </aside>
    </>
  );
}
