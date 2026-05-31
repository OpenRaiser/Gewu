export function BridgePanel({ bridge }) {
  if (!bridge) return null;
  const items = [
    ["承前", bridge.prev],
    ["本式", bridge.current],
    ["启后", bridge.next],
    ["来源", bridge.sources],
  ].filter(([, value]) => value && value.length);

  if (items.length === 0) return null;

  return (
    <div className="bridge-panel">
      {items.map(([label, value]) => (
        <div className="bridge-item" key={label}>
          <div className="bridge-label">{label}</div>
          <div className="bridge-text">
            {Array.isArray(value) ? value.join(" · ") : value}
          </div>
        </div>
      ))}
    </div>
  );
}

export function MatrixHeatmap({
  x = 0,
  y = 0,
  rows,
  cols,
  values,
  cell = 34,
  gap = 3,
  title,
  formatter = (v) => Number.isFinite(v) ? v.toFixed(2) : "-∞",
  fillFor,
  textFor,
  highlightRow = null,
  highlightCol = null,
  showValues = true,
}) {
  const labelW = 34;
  const labelH = 18;
  const width = cols.length * (cell + gap) - gap;
  const height = rows.length * (cell + gap) - gap;

  const defaultFill = (v) => {
    if (v === -Infinity) return "#eee3cf";
    const clamped = Math.max(0, Math.min(1, Math.abs(v)));
    return `rgba(158,43,30,${0.12 + clamped * 0.62})`;
  };

  return (
    <g transform={`translate(${x}, ${y})`}>
      {title && <text x={labelW} y={0} fill="#5a4a36" fontSize="11">{title}</text>}
      {cols.map((c, j) => (
        <text key={"c" + j} x={labelW + j * (cell + gap) + cell / 2} y={labelH}
          fill={highlightCol === j ? "#9e2b1e" : "#5a4a36"} fontSize="10.5" textAnchor="middle">
          {c}
        </text>
      ))}
      {rows.map((r, i) => (
        <g key={"r" + i}>
          <text x={labelW - 8} y={labelH + 5 + i * (cell + gap) + cell / 2}
            fill={highlightRow === i ? "#9e2b1e" : "#5a4a36"} fontSize="10.5" textAnchor="end">
            {r}
          </text>
          {cols.map((_, j) => {
            const v = values[i][j];
            const hot = highlightRow === i || highlightCol === j;
            const tx = labelW + j * (cell + gap);
            const ty = labelH + 6 + i * (cell + gap);
            const text = textFor ? textFor(v, i, j) : formatter(v, i, j);
            return (
              <g key={j}>
                <rect x={tx} y={ty} width={cell} height={cell} rx="3"
                  fill={fillFor ? fillFor(v, i, j) : defaultFill(v)}
                  stroke={hot ? "#9e2b1e" : "#cdb98e"}
                  strokeWidth={hot ? 1.5 : 0.7}
                  style={{ transition: "fill .25s ease, stroke .2s ease" }} />
                {showValues && (
                  <text x={tx + cell / 2} y={ty + cell / 2 + 4}
                    fill={v > 0.55 ? "#fff" : "#2b2117"} fontSize="9.5" textAnchor="middle">
                    {text}
                  </text>
                )}
              </g>
            );
          })}
        </g>
      ))}
      <rect x={labelW - 1} y={labelH + 5} width={width + 2} height={height + 2}
        fill="none" stroke="#cdb98e" strokeWidth="0.5" opacity="0.35" />
    </g>
  );
}
