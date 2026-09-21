export interface VisualSpec {
  type: string;
  a?: number;
  b?: number;
  result?: number;
  min?: number;
  max?: number;
  aria_label?: string;
}

function AreaModel({ spec }: { spec: VisualSpec }) {
  const a = spec.a ?? 1;
  const b = spec.b ?? 1;
  const xW = 120;
  const bW = Math.min(120, Math.max(40, Math.abs(b) * 18));
  const h = Math.min(140, Math.max(48, Math.abs(a) * 22));
  const totalW = xW + bW;
  const bx = 60;
  const by = 40;
  return (
    <svg
      viewBox={`0 0 ${bx + totalW + 40} ${by + h + 50}`}
      className="visual"
      role="img"
      aria-label={spec.aria_label}
    >
      {/* top labels */}
      <text x={bx + xW / 2} y={by - 12} textAnchor="middle" className="viz-label">
        x
      </text>
      <text
        x={bx + xW + bW / 2}
        y={by - 12}
        textAnchor="middle"
        className="viz-label"
      >
        {b}
      </text>
      {/* left label */}
      <text
        x={bx - 14}
        y={by + h / 2}
        textAnchor="middle"
        className="viz-label"
      >
        {a}
      </text>
      {/* cells */}
      <rect
        x={bx}
        y={by}
        width={xW}
        height={h}
        className="viz-cell viz-cell-a"
      />
      <rect
        x={bx + xW}
        y={by}
        width={bW}
        height={h}
        className="viz-cell viz-cell-b"
      />
      {/* cell contents */}
      <text
        x={bx + xW / 2}
        y={by + h / 2 + 6}
        textAnchor="middle"
        className="viz-term"
      >
        {a}x
      </text>
      <text
        x={bx + xW + bW / 2}
        y={by + h / 2 + 6}
        textAnchor="middle"
        className="viz-term"
      >
        {a}·{b}
      </text>
    </svg>
  );
}

function NumberLine({
  spec,
  compare = false,
}: {
  spec: VisualSpec;
  compare?: boolean;
}) {
  const min = spec.min ?? 0;
  const max = spec.max ?? 10;
  const width = 360;
  const pad = 24;
  const xFor = (v: number) =>
    pad + ((v - min) / (max - min)) * (width - 2 * pad);
  const y = 60;
  const ticks = Array.from({ length: max - min + 1 }, (_, i) => min + i);
  const a = spec.a ?? 0;
  const b = spec.b ?? 0;
  const result = spec.result ?? a + b;

  return (
    <svg
      viewBox={`0 0 ${width} 110`}
      className="visual"
      role="img"
      aria-label={spec.aria_label}
    >
      <line x1={pad} y1={y} x2={width - pad} y2={y} className="viz-axis" />
      {ticks.map((t) => (
        <g key={t}>
          <line x1={xFor(t)} y1={y - 5} x2={xFor(t)} y2={y + 5} className="viz-tick" />
          <text x={xFor(t)} y={y + 20} textAnchor="middle" className="viz-tick-label">
            {t}
          </text>
        </g>
      ))}
      {compare ? (
        <>
          <circle cx={xFor(a)} cy={y} r="6" className="viz-point viz-point-a" />
          <text x={xFor(a)} y={y - 14} textAnchor="middle" className="viz-label">
            {a}
          </text>
          <circle cx={xFor(b)} cy={y} r="6" className="viz-point viz-point-b" />
          <text x={xFor(b)} y={y - 14} textAnchor="middle" className="viz-label">
            {b}
          </text>
        </>
      ) : (
        <>
          <path
            d={`M ${xFor(0)} ${y - 10} Q ${(xFor(0) + xFor(a)) / 2} ${y - 34} ${xFor(a)} ${y - 10}`}
            className="viz-hop viz-hop-a"
            markerEnd="url(#vizArrowA)"
          />
          <path
            d={`M ${xFor(a)} ${y - 10} Q ${(xFor(a) + xFor(result)) / 2} ${y - 44} ${xFor(result)} ${y - 10}`}
            className="viz-hop viz-hop-b"
            markerEnd="url(#vizArrowB)"
          />
          <circle cx={xFor(result)} cy={y} r="6" className="viz-point viz-point-b" />
          <defs>
            <marker id="vizArrowA" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">
              <path d="M0,0 L8,4 L0,8 z" className="viz-arrow-a" />
            </marker>
            <marker id="vizArrowB" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">
              <path d="M0,0 L8,4 L0,8 z" className="viz-arrow-b" />
            </marker>
          </defs>
          <text x={(xFor(0) + xFor(a)) / 2} y={y - 30} textAnchor="middle" className="viz-hop-label">
            {a >= 0 ? `+${a}` : a}
          </text>
          <text x={(xFor(a) + xFor(result)) / 2} y={y - 48} textAnchor="middle" className="viz-hop-label">
            {b >= 0 ? `+${b}` : b}
          </text>
        </>
      )}
    </svg>
  );
}

export default function ProblemVisual({ spec }: { spec: VisualSpec | null }) {
  if (!spec) return null;
  if (spec.type === "area_model") return <AreaModel spec={spec} />;
  if (spec.type === "number_line") return <NumberLine spec={spec} />;
  if (spec.type === "number_line_compare")
    return <NumberLine spec={spec} compare />;
  return null;
}
