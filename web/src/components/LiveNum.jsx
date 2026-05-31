import { useRef } from "react";

// 嵌在代码里的"活字":可左右拖动改变数值,右图实时重算
export default function LiveNum({ value, min, max, step = 1, onChange, fmt }) {
  const drag = useRef(null);

  const onPointerDown = (e) => {
    e.preventDefault();
    drag.current = { startX: e.clientX, startVal: value };
    e.target.setPointerCapture(e.pointerId);
  };
  const onPointerMove = (e) => {
    if (!drag.current) return;
    const dx = e.clientX - drag.current.startX;
    // 每 14px 拖动 = 1 个 step
    let v = drag.current.startVal + Math.round(dx / 14) * step;
    v = Math.min(max, Math.max(min, v));
    v = Math.round(v / step) * step;
    onChange(v);
  };
  const onPointerUp = (e) => {
    drag.current = null;
    try { e.target.releasePointerCapture(e.pointerId); } catch {}
  };

  const text = fmt ? fmt(value) : String(value);
  return (
    <span
      className="live-num"
      title="按住左右拖动可改变此数值"
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
    >
      {text}
    </span>
  );
}
