import type { VisualSpec } from "../mve/contracts";

interface PanSpec {
  x_count: number;
  units: number;
}

interface FractionSpec {
  numerator: number;
  denominator: number;
}

interface TapeSegment {
  label: string;
  span: number;
  highlight: boolean;
}

interface AlgebraTerm {
  coefficient: number;
  variable?: string | null;
  degree: number;
  label: string;
  sign_changed?: boolean;
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
    <svg viewBox={`0 0 ${bx + totalW + 40} ${by + h + 50}`} className="visual" role="img" aria-label={spec.aria_label}>
      <text x={bx + xW / 2} y={by - 12} textAnchor="middle" className="viz-label">x</text>
      <text x={bx + xW + bW / 2} y={by - 12} textAnchor="middle" className="viz-label">{b}</text>
      <text x={bx - 14} y={by + h / 2} textAnchor="middle" className="viz-label">{a}</text>
      <rect x={bx} y={by} width={xW} height={h} className="viz-cell viz-cell-a" />
      <rect x={bx + xW} y={by} width={bW} height={h} className="viz-cell viz-cell-b" />
      <text x={bx + xW / 2} y={by + h / 2 + 6} textAnchor="middle" className="viz-term">{a}x</text>
      <text x={bx + xW + bW / 2} y={by + h / 2 + 6} textAnchor="middle" className="viz-term">{a}·{b}</text>
    </svg>
  );
}

function ArrayModel({ spec }: { spec: VisualSpec }) {
  const rows = Math.min(10, Math.max(1, Math.floor(spec.rows ?? 1)));
  const columns = Math.min(10, Math.max(1, Math.floor(spec.columns ?? 1)));
  const cell = 28;
  const pad = 28;
  const width = columns * cell + pad * 2;
  const height = rows * cell + pad * 2 + 24;
  const squares = spec.mode === "squares";
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="visual elementary-visual" role="img" aria-label={spec.aria_label}>
      {Array.from({ length: rows * columns }, (_, index) => {
        const row = Math.floor(index / columns);
        const column = index % columns;
        return squares ? (
          <rect key={index} x={pad + column * cell} y={pad + row * cell} width={cell} height={cell} className="viz-array-square" />
        ) : (
          <circle key={index} cx={pad + column * cell + cell / 2} cy={pad + row * cell + cell / 2} r="9" className="viz-array-counter" />
        );
      })}
      <text x={width / 2} y={height - 5} textAnchor="middle" className="viz-label">{rows} rows × {columns} in each row</text>
    </svg>
  );
}

function FractionBar({ spec }: { spec: VisualSpec }) {
  const denominator = Math.max(1, Math.floor(spec.denominator ?? spec.b ?? 1));
  const numerator = Math.min(denominator, Math.max(0, Math.floor(spec.numerator ?? spec.a ?? 0)));
  const width = 360;
  const x = 24;
  const y = 35;
  const h = 54;
  const cell = (width - 48) / denominator;
  return (
    <svg viewBox={`0 0 ${width} 125`} className="visual" role="img" aria-label={spec.aria_label ?? `${numerator} of ${denominator} equal parts shaded`}>
      {Array.from({ length: denominator }, (_, i) => (
        <rect key={i} x={x + i * cell} y={y} width={cell} height={h} className={`viz-cell ${i < numerator ? "viz-cell-a" : ""}`} />
      ))}
      <text x={width / 2} y={110} textAnchor="middle" className="viz-label">{numerator}/{denominator}</text>
    </svg>
  );
}

function CoordinatePlane({ spec }: { spec: VisualSpec }) {
  const min = spec.min ?? -5;
  const max = spec.max ?? 5;
  const px = spec.x ?? spec.a ?? 0;
  const py = spec.y ?? spec.b ?? 0;
  const labeled = spec.labeled ?? true;
  const size = 320;
  const pad = 28;
  const scale = (size - 2 * pad) / (max - min);
  const pos = (v: number) => pad + (v - min) * scale;
  const yPos = (v: number) => size - pos(v);
  const ticks = Array.from({ length: max - min + 1 }, (_, i) => min + i);
  const labelEvery = max - min > 14 ? 2 : 1;
  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="visual" role="img" aria-label={spec.aria_label ?? `Coordinate plane with point at ${px}, ${py}`}>
      {ticks.map((t) => (
        <g key={`g${t}`}>
          <line x1={pad} y1={yPos(t)} x2={size - pad} y2={yPos(t)} className="viz-grid" />
          <line x1={pos(t)} y1={pad} x2={pos(t)} y2={size - pad} className="viz-grid" />
        </g>
      ))}
      <line x1={pad} y1={yPos(0)} x2={size - pad} y2={yPos(0)} className="viz-axis" />
      <line x1={pos(0)} y1={pad} x2={pos(0)} y2={size - pad} className="viz-axis" />
      {ticks.map((t) => (
        <g key={t}>
          <line x1={pos(t)} y1={yPos(0) - 3} x2={pos(t)} y2={yPos(0) + 3} className="viz-tick" />
          <line x1={pos(0) - 3} y1={yPos(t)} x2={pos(0) + 3} y2={yPos(t)} className="viz-tick" />
          {t !== 0 && t % labelEvery === 0 && (
            <>
              <text x={pos(t)} y={yPos(0) + 15} textAnchor="middle" className="viz-tick-label">{t}</text>
              <text x={pos(0) - 8} y={yPos(t) + 4} textAnchor="end" className="viz-tick-label">{t}</text>
            </>
          )}
        </g>
      ))}
      <circle cx={pos(px)} cy={yPos(py)} r="6" className="viz-point viz-point-a" />
      {labeled && (
        <text x={pos(px) + 8} y={yPos(py) - 8} className="viz-label">({px}, {py})</text>
      )}
    </svg>
  );
}

function LinearGraph({ spec }: { spec: VisualSpec }) {
  const min = spec.min ?? -10;
  const max = spec.max ?? 10;
  const mNum = spec.m_num ?? 0;
  const mDen = spec.m_den ?? 1;
  const intercept = spec.b ?? 0;
  const m = mNum / mDen;
  const size = 340;
  const pad = 30;
  const scale = (size - 2 * pad) / (max - min);
  const pos = (v: number) => pad + (v - min) * scale;
  const yPos = (v: number) => size - pos(v);
  const ticks = Array.from({ length: max - min + 1 }, (_, i) => min + i);
  // Segment endpoints where the line crosses the visible window.
  const xAt = (y: number) => (y - intercept) / m;
  const endpoints = (
    [
      [min, m * min + intercept],
      [max, m * max + intercept],
      [xAt(min), min],
      [xAt(max), max],
    ] as [number, number][]
  )
    .filter(([x, y]) => x >= min - 1e-9 && x <= max + 1e-9 && y >= min - 1e-9 && y <= max + 1e-9)
    .slice(0, 2);
  const lattice = spec.mark_lattice
    ? ([
        [0, intercept],
        [mDen, intercept + mNum],
        [-mDen, intercept - mNum],
      ] as [number, number][])
        .filter(([x, y]) => x >= min && x <= max && y >= min && y <= max)
    : [];
  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="visual" role="img" aria-label={spec.aria_label ?? "A line graphed on a coordinate plane"}>
      {ticks.map((t) => (
        <g key={`g${t}`}>
          <line x1={pad} y1={yPos(t)} x2={size - pad} y2={yPos(t)} className="viz-grid" />
          <line x1={pos(t)} y1={pad} x2={pos(t)} y2={size - pad} className="viz-grid" />
        </g>
      ))}
      <line x1={pad} y1={yPos(0)} x2={size - pad} y2={yPos(0)} className="viz-axis" />
      <line x1={pos(0)} y1={pad} x2={pos(0)} y2={size - pad} className="viz-axis" />
      {ticks.filter((t) => t % 2 === 0).map((t) => (
        <g key={t}>
          <line x1={pos(t)} y1={yPos(0) - 3} x2={pos(t)} y2={yPos(0) + 3} className="viz-tick" />
          <line x1={pos(0) - 3} y1={yPos(t)} x2={pos(0) + 3} y2={yPos(t)} className="viz-tick" />
          {t !== 0 && (
            <>
              <text x={pos(t)} y={yPos(0) + 15} textAnchor="middle" className="viz-tick-label">{t}</text>
              <text x={pos(0) - 8} y={yPos(t) + 4} textAnchor="end" className="viz-tick-label">{t}</text>
            </>
          )}
        </g>
      ))}
      {endpoints.length === 2 && (
        <line
          x1={pos(endpoints[0][0])}
          y1={yPos(endpoints[0][1])}
          x2={pos(endpoints[1][0])}
          y2={yPos(endpoints[1][1])}
          className="viz-curve"
        />
      )}
      {lattice.map(([x, y]) => (
        <circle key={`${x},${y}`} cx={pos(x)} cy={yPos(y)} r="4.5" className="viz-point viz-point-a" />
      ))}
    </svg>
  );
}

function ParabolaGraph({ spec }: { spec: VisualSpec }) {
  const min = spec.min ?? -10;
  const max = spec.max ?? 10;
  const a = (spec.a_num ?? 1) / (spec.a_den ?? 1);
  const h = spec.h ?? 0;
  const k = spec.k ?? 0;
  const size = 340;
  const pad = 30;
  const scale = (size - 2 * pad) / (max - min);
  const pos = (v: number) => pad + (v - min) * scale;
  const yPos = (v: number) => size - pos(v);
  const ticks = Array.from({ length: max - min + 1 }, (_, i) => min + i);
  // Sample the curve; split the path wherever it leaves the window.
  const f = (x: number) => a * (x - h) * (x - h) + k;
  const step = (max - min) / 240;
  const segments: [number, number][][] = [];
  let segment: [number, number][] = [];
  for (let x = min; x <= max + 1e-9; x += step) {
    const y = f(x);
    if (y >= min - 0.5 && y <= max + 0.5) {
      segment.push([x, y]);
    } else if (segment.length) {
      segments.push(segment);
      segment = [];
    }
  }
  if (segment.length) segments.push(segment);
  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="visual" role="img" aria-label={spec.aria_label ?? "A parabola graphed on a coordinate plane"}>
      {ticks.map((t) => (
        <g key={`g${t}`}>
          <line x1={pad} y1={yPos(t)} x2={size - pad} y2={yPos(t)} className="viz-grid" />
          <line x1={pos(t)} y1={pad} x2={pos(t)} y2={size - pad} className="viz-grid" />
        </g>
      ))}
      <line x1={pad} y1={yPos(0)} x2={size - pad} y2={yPos(0)} className="viz-axis" />
      <line x1={pos(0)} y1={pad} x2={pos(0)} y2={size - pad} className="viz-axis" />
      {ticks.filter((t) => t % 2 === 0).map((t) => (
        <g key={t}>
          <line x1={pos(t)} y1={yPos(0) - 3} x2={pos(t)} y2={yPos(0) + 3} className="viz-tick" />
          <line x1={pos(0) - 3} y1={yPos(t)} x2={pos(0) + 3} y2={yPos(t)} className="viz-tick" />
          {t !== 0 && (
            <>
              <text x={pos(t)} y={yPos(0) + 15} textAnchor="middle" className="viz-tick-label">{t}</text>
              <text x={pos(0) - 8} y={yPos(t) + 4} textAnchor="end" className="viz-tick-label">{t}</text>
            </>
          )}
        </g>
      ))}
      {segments.map((points, i) => (
        <polyline
          key={i}
          points={points.map(([x, y]) => `${pos(x)},${yPos(y)}`).join(" ")}
          fill="none"
          className="viz-curve"
        />
      ))}
    </svg>
  );
}

function PolynomialGraph({ spec }: { spec: VisualSpec }) {
  const min = spec.min ?? -10;
  const max = spec.max ?? 10;
  const coeffs = spec.coeffs ?? [];
  const size = 340;
  const pad = 30;
  const scale = (size - 2 * pad) / (max - min);
  const pos = (v: number) => pad + (v - min) * scale;
  const yPos = (v: number) => size - pos(v);
  const ticks = Array.from({ length: max - min + 1 }, (_, i) => min + i);
  // Horner evaluation of the backend-expanded coefficients; the curve is
  // split wherever it leaves the window, same as the parabola renderer.
  const f = (x: number) => coeffs.reduce((acc, c) => acc * x + c, 0);
  const step = (max - min) / 240;
  const segments: [number, number][][] = [];
  let segment: [number, number][] = [];
  for (let x = min; x <= max + 1e-9; x += step) {
    const y = f(x);
    if (y >= min - 0.5 && y <= max + 0.5) {
      segment.push([x, y]);
    } else if (segment.length) {
      segments.push(segment);
      segment = [];
    }
  }
  if (segment.length) segments.push(segment);
  const roots = spec.mark_roots ? spec.roots ?? [] : [];
  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="visual" role="img" aria-label={spec.aria_label ?? "A polynomial curve graphed on a coordinate plane"}>
      {ticks.map((t) => (
        <g key={`g${t}`}>
          <line x1={pad} y1={yPos(t)} x2={size - pad} y2={yPos(t)} className="viz-grid" />
          <line x1={pos(t)} y1={pad} x2={pos(t)} y2={size - pad} className="viz-grid" />
        </g>
      ))}
      <line x1={pad} y1={yPos(0)} x2={size - pad} y2={yPos(0)} className="viz-axis" />
      <line x1={pos(0)} y1={pad} x2={pos(0)} y2={size - pad} className="viz-axis" />
      {ticks.filter((t) => t % 2 === 0).map((t) => (
        <g key={t}>
          <line x1={pos(t)} y1={yPos(0) - 3} x2={pos(t)} y2={yPos(0) + 3} className="viz-tick" />
          <line x1={pos(0) - 3} y1={yPos(t)} x2={pos(0) + 3} y2={yPos(t)} className="viz-tick" />
          {t !== 0 && (
            <>
              <text x={pos(t)} y={yPos(0) + 15} textAnchor="middle" className="viz-tick-label">{t}</text>
              <text x={pos(0) - 8} y={yPos(t) + 4} textAnchor="end" className="viz-tick-label">{t}</text>
            </>
          )}
        </g>
      ))}
      {segments.map((points, i) => (
        <polyline
          key={i}
          points={points.map(([x, y]) => `${pos(x)},${yPos(y)}`).join(" ")}
          fill="none"
          className="viz-curve"
        />
      ))}
      {roots.map((r) => (
        <circle key={r} cx={pos(r)} cy={yPos(0)} r="4.5" className="viz-point viz-point-a" />
      ))}
    </svg>
  );
}

function ExponentialGraph({ spec }: { spec: VisualSpec }) {
  const xMin = spec.x_min ?? -6;
  const xMax = spec.x_max ?? 6;
  const yMin = spec.y_min ?? -1;
  const yMax = spec.y_max ?? 16;
  const a = spec.a ?? 1;
  const base = (spec.b_num ?? 2) / (spec.b_den ?? 1);
  const size = 340;
  const pad = 30;
  const xFor = (v: number) => pad + ((v - xMin) / (xMax - xMin)) * (size - 2 * pad);
  const yFor = (v: number) => size - pad - ((v - yMin) / (yMax - yMin)) * (size - 2 * pad);
  const f = (x: number) => a * Math.pow(base, x);
  const step = (xMax - xMin) / 240;
  const segments: [number, number][][] = [];
  let segment: [number, number][] = [];
  for (let x = xMin; x <= xMax + 1e-9; x += step) {
    const y = f(x);
    if (y >= yMin - 0.5 && y <= yMax + 0.5) {
      segment.push([x, y]);
    } else if (segment.length) {
      segments.push(segment);
      segment = [];
    }
  }
  if (segment.length) segments.push(segment);
  const xTicks = Array.from({ length: xMax - xMin + 1 }, (_, i) => xMin + i).filter(
    (t) => t % 2 === 0
  );
  const yTicks = Array.from({ length: yMax - yMin + 1 }, (_, i) => yMin + i).filter(
    (t) => t % 2 === 0
  );
  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="visual" role="img" aria-label={spec.aria_label ?? "An exponential curve graphed on a coordinate plane"}>
      {xTicks.map((t) => (
        <line key={`v${t}`} x1={xFor(t)} y1={pad} x2={xFor(t)} y2={size - pad} className="viz-grid" />
      ))}
      {yTicks.map((t) => (
        <line key={`h${t}`} x1={pad} y1={yFor(t)} x2={size - pad} y2={yFor(t)} className="viz-grid" />
      ))}
      {xMin <= 0 && xMax >= 0 && (
        <line x1={xFor(0)} y1={pad} x2={xFor(0)} y2={size - pad} className="viz-axis" />
      )}
      {yMin <= 0 && yMax >= 0 && (
        <line x1={pad} y1={yFor(0)} x2={size - pad} y2={yFor(0)} className="viz-axis" />
      )}
      {xTicks.filter((t) => t !== 0).map((t) => (
        <text key={`xt${t}`} x={xFor(t)} y={yFor(0) + 15} textAnchor="middle" className="viz-tick-label">{t}</text>
      ))}
      {yTicks.filter((t) => t !== 0).map((t) => (
        <text key={`yt${t}`} x={xFor(0) - 8} y={yFor(t) + 4} textAnchor="end" className="viz-tick-label">{t}</text>
      ))}
      {segments.map((points, i) => (
        <polyline
          key={i}
          points={points.map(([x, y]) => `${xFor(x)},${yFor(y)}`).join(" ")}
          fill="none"
          className="viz-curve"
        />
      ))}
      {(spec.mark_points ?? []).map((p, i) => (
        <circle key={i} cx={xFor(p[0])} cy={yFor(p[1])} r="4.5" className="viz-point viz-point-a" />
      ))}
    </svg>
  );
}

function AngleDiagram({ spec }: { spec: VisualSpec }) {
  const angle = Math.min(180, Math.max(0, spec.angle ?? spec.a ?? 45));
  const cx = 80;
  const cy = 145;
  const radius = 90;
  const radians = (angle * Math.PI) / 180;
  const ex = cx + radius * Math.cos(radians);
  const ey = cy - radius * Math.sin(radians);
  const arcRadius = 34;
  const ax = cx + arcRadius * Math.cos(radians);
  const ay = cy - arcRadius * Math.sin(radians);
  const largeArc = angle > 180 ? 1 : 0;
  return (
    <svg viewBox="0 0 260 190" className="visual" role="img" aria-label={spec.aria_label ?? `Angle measuring ${angle} degrees`}>
      <line x1={cx} y1={cy} x2={cx + radius} y2={cy} className="viz-axis" />
      <line x1={cx} y1={cy} x2={ex} y2={ey} className="viz-axis" />
      {angle > 0 && <path d={`M ${cx + arcRadius} ${cy} A ${arcRadius} ${arcRadius} 0 ${largeArc} 0 ${ax} ${ay}`} className="viz-hop viz-hop-a" />}
      <circle cx={cx} cy={cy} r="4" className="viz-point viz-point-a" />
      {spec.labeled !== false && <text x={cx + 44} y={cy - 18} className="viz-label">{angle}°</text>}
    </svg>
  );
}

function AnglePair({ spec }: { spec: VisualSpec }) {
  const angle = spec.angle ?? 45;
  const cx = 60;
  const cy = 150;
  const radians = (angle * Math.PI) / 180;
  const mx = cx + 160 * Math.cos(radians);
  const my = cy - 160 * Math.sin(radians);
  const mid = radians / 2;
  const label1 = { x: cx + 52 * Math.cos(mid), y: cy - 52 * Math.sin(mid) };
  if (spec.kind === "complementary") {
    const mid2 = (radians + Math.PI / 2) / 2;
    const label2 = { x: cx + 66 * Math.cos(mid2), y: cy - 66 * Math.sin(mid2) };
    return (
      <svg viewBox="0 0 260 190" className="visual" role="img" aria-label={spec.aria_label}>
        <line x1={cx} y1={cy} x2={cx + 190} y2={cy} className="viz-axis" />
        <line x1={cx} y1={cy} x2={cx} y2={cy - 160} className="viz-axis" />
        <line x1={cx} y1={cy} x2={mx} y2={my} className="viz-axis" />
        <path d={`M ${cx + 30} ${cy} A 30 30 0 0 0 ${cx + 30 * Math.cos(radians)} ${cy - 30 * Math.sin(radians)}`} className="viz-hop viz-hop-a" />
        <path d={`M ${cx + 44 * Math.cos(radians)} ${cy - 44 * Math.sin(radians)} A 44 44 0 0 0 ${cx} ${cy - 44}`} className="viz-hop" />
        <text x={label1.x} y={label1.y} className="viz-label">{angle}°</text>
        <text x={label2.x} y={label2.y} className="viz-label">?</text>
      </svg>
    );
  }
  // supplementary — the two rays span a straight line
  const mid2 = (radians + Math.PI) / 2;
  const label2 = { x: cx + 66 * Math.cos(mid2), y: cy - 66 * Math.sin(mid2) };
  return (
    <svg viewBox="0 0 340 190" className="visual" role="img" aria-label={spec.aria_label}>
      <line x1={cx - 40} y1={cy} x2={cx + 260} y2={cy} className="viz-axis" />
      <line x1={cx} y1={cy} x2={mx} y2={my} className="viz-axis" />
      <path d={`M ${cx + 30} ${cy} A 30 30 0 0 0 ${cx + 30 * Math.cos(radians)} ${cy - 30 * Math.sin(radians)}`} className="viz-hop viz-hop-a" />
      <path d={`M ${cx + 44 * Math.cos(radians)} ${cy - 44 * Math.sin(radians)} A 44 44 0 0 0 ${cx - 44} ${cy}`} className="viz-hop" />
      <text x={label1.x} y={label1.y} className="viz-label">{angle}°</text>
      <text x={label2.x} y={label2.y} className="viz-label">?</text>
    </svg>
  );
}

function IntersectingLines({ spec }: { spec: VisualSpec }) {
  const angle = spec.angle ?? 60;
  const cx = 180;
  const cy = 105;
  const radians = (angle * Math.PI) / 180;
  const dx = 150 * Math.cos(radians);
  const dy = 150 * Math.sin(radians);
  // The marked sector sits between the right ray and the upper slanted ray.
  const markAdjacent = spec.mark === "adjacent";
  const qx = markAdjacent ? cx - 52 : cx + 52;
  const qy = markAdjacent ? cy - 40 : cy + 40;
  return (
    <svg viewBox="0 0 360 210" className="visual" role="img" aria-label={spec.aria_label}>
      <line x1={cx - 165} y1={cy} x2={cx + 165} y2={cy} className="viz-axis" />
      <line x1={cx - dx} y1={cy + dy} x2={cx + dx} y2={cy - dy} className="viz-axis" />
      <path
        d={`M ${cx + 34} ${cy} A 34 34 0 0 0 ${cx + 34 * Math.cos(radians)} ${cy - 34 * Math.sin(radians)}`}
        className="viz-hop viz-hop-a"
      />
      <text x={cx + 52} y={cy - 36} className="viz-label">{angle}°</text>
      <text x={qx} y={qy} textAnchor="middle" className="viz-label">?</text>
    </svg>
  );
}

function TriangleAngles({ spec }: { spec: VisualSpec }) {
  const a = spec.a ?? 60;
  const b = spec.b ?? 60;
  const x0 = 60;
  const x1 = 300;
  const y = 165;
  const cot = (deg: number) => 1 / Math.tan((deg * Math.PI) / 180);
  const height = (x1 - x0) / (cot(a) + cot(b));
  const apexX = x0 + height * cot(a);
  const apexY = y - height;
  return (
    <svg viewBox="0 0 360 200" className="visual" role="img" aria-label={spec.aria_label}>
      <path d={`M ${x0} ${y} L ${x1} ${y} L ${apexX} ${apexY} Z`} className="viz-cell viz-cell-a" />
      <text x={x0 + 20} y={y - 8} className="viz-label">{a}°</text>
      <text x={x1 - 34} y={y - 8} className="viz-label">{b}°</text>
      <text x={apexX} y={apexY + 26} textAnchor="middle" className="viz-label">?</text>
    </svg>
  );
}

function CircleMeasure({ spec }: { spec: VisualSpec }) {
  const r = spec.r ?? 0;
  return (
    <svg viewBox="0 0 360 210" className="visual" role="img" aria-label={spec.aria_label}>
      <circle cx="180" cy="105" r="82" className="viz-cell viz-cell-a" />
      <line x1="180" y1="105" x2="262" y2="105" className="viz-axis" />
      <circle cx="180" cy="105" r="4" className="viz-point viz-point-a" />
      <text x="221" y="96" textAnchor="middle" className="viz-label">r = {r}</text>
    </svg>
  );
}

function CompositeFigure({ spec }: { spec: VisualSpec }) {
  const w = spec.w ?? 8;
  const h = spec.h ?? 8;
  const a = spec.a ?? 3;
  const b = spec.b ?? 3;
  const unit = 20;
  const ox = 60;
  const oy = 15;
  const px = (v: number) => ox + v * unit;
  const py = (v: number) => oy + v * unit;
  // L-shape: outer w×h minus an a×b notch at the top right.
  const path =
    `M ${px(0)} ${py(0)} L ${px(w - a)} ${py(0)} L ${px(w - a)} ${py(b)} ` +
    `L ${px(w)} ${py(b)} L ${px(w)} ${py(h)} L ${px(0)} ${py(h)} Z`;
  return (
    <svg viewBox="0 0 360 240" className="visual" role="img" aria-label={spec.aria_label}>
      <path d={path} className="viz-cell viz-cell-a" />
      <text x={px(w / 2)} y={py(h) + 18} textAnchor="middle" className="viz-label">{w}</text>
      <text x={px(0) - 14} y={py(h / 2)} textAnchor="middle" className="viz-label">{h}</text>
      <text x={px(w - a / 2)} y={py(b) - 8} textAnchor="middle" className="viz-label">{a}</text>
      <text x={px(w - a) + 14} y={py(b / 2)} textAnchor="middle" className="viz-label">{b}</text>
    </svg>
  );
}

function TransformPlane({ spec }: { spec: VisualSpec }) {
  const bound = 8;
  const size = 320;
  const pad = 26;
  const scale = (size - 2 * pad) / (2 * bound);
  const pos = (v: number) => pad + (v + bound) * scale;
  const yPos = (v: number) => size - pos(v);
  const ticks = Array.from({ length: 2 * bound + 1 }, (_, i) => i - bound);
  const path = (points: number[][]) =>
    points.map((p, i) => `${i === 0 ? "M" : "L"} ${pos(p[0])} ${yPos(p[1])}`).join(" ") + " Z";
  const vertex = (p: number[], key: string, cls: string, label?: string) => (
    <g key={key}>
      <circle cx={pos(p[0])} cy={yPos(p[1])} r="5" className={cls} />
      {label && (
        <text x={pos(p[0]) + 8} y={yPos(p[1]) - 6} className="viz-label">{label}</text>
      )}
    </g>
  );
  const preimage = spec.preimage ?? [];
  const image = spec.image ?? [];
  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="visual" role="img" aria-label={spec.aria_label}>
      {ticks.map((t) => (
        <g key={`g${t}`}>
          <line x1={pad} y1={yPos(t)} x2={size - pad} y2={yPos(t)} className="viz-grid" />
          <line x1={pos(t)} y1={pad} x2={pos(t)} y2={size - pad} className="viz-grid" />
        </g>
      ))}
      <line x1={pad} y1={yPos(0)} x2={size - pad} y2={yPos(0)} className="viz-axis" />
      <line x1={pos(0)} y1={pad} x2={pos(0)} y2={size - pad} className="viz-axis" />
      {ticks.filter((t) => t !== 0 && t % 2 === 0).map((t) => (
        <g key={t}>
          <text x={pos(t)} y={yPos(0) + 14} textAnchor="middle" className="viz-tick-label">{t}</text>
          <text x={pos(0) - 7} y={yPos(t) + 4} textAnchor="end" className="viz-tick-label">{t}</text>
        </g>
      ))}
      {preimage.length >= 3 && <path d={path(preimage)} className="viz-cell viz-cell-a" />}
      {preimage.length === 1 && vertex(preimage[0], "pre", "viz-point viz-point-a", spec.labels?.[0])}
      {preimage.length >= 3 &&
        preimage.map((p, i) => vertex(p, `p${i}`, "viz-point viz-point-a", spec.labels?.[i]))}
      {image.length >= 3 && <path d={path(image)} className="viz-hidden" />}
      {image.length >= 3 &&
        image.map((p, i) => vertex(p, `i${i}`, "viz-point", spec.image_labels?.[i]))}
    </svg>
  );
}

function SimilarFigures({ spec }: { spec: VisualSpec }) {
  const pre = spec.preimage ?? [];
  const img = spec.image ?? [];
  const extent = (pts: number[][]) => {
    const xs = pts.map((p) => p[0]);
    const ys = pts.map((p) => p[1]);
    return Math.max(
      Math.max(...xs) - Math.min(...xs),
      Math.max(...ys) - Math.min(...ys),
      1
    );
  };
  // One shared unit keeps the figures proportional to each other.
  const unit = 130 / Math.max(extent(pre), extent(img));
  const draw = (pts: number[][], cx: number, baseY: number, labels?: (string | null)[]) => {
    const xs = pts.map((p) => p[0]);
    const ys = pts.map((p) => p[1]);
    const ox = cx - ((Math.min(...xs) + Math.max(...xs)) / 2) * unit;
    const oy = baseY - Math.min(...ys) * unit;
    const sx = (v: number) => ox + v * unit;
    const sy = (v: number) => oy - v * unit;
    const path =
      pts.map((p, i) => `${i === 0 ? "M" : "L"} ${sx(p[0])} ${sy(p[1])}`).join(" ") + " Z";
    return (
      <g>
        <path d={path} className="viz-cell viz-cell-a" />
        {labels?.map((label, i) => {
          if (!label) return null;
          const p1 = pts[i];
          const p2 = pts[(i + 1) % pts.length];
          const mx = (sx(p1[0]) + sx(p2[0])) / 2;
          const my = (sy(p1[1]) + sy(p2[1])) / 2;
          const ex = sx(p2[0]) - sx(p1[0]);
          const ey = sy(p2[1]) - sy(p1[1]);
          const len = Math.hypot(ex, ey) || 1;
          return (
            <text
              key={i}
              x={mx - (ey / len) * 12}
              y={my + (ex / len) * 12}
              textAnchor="middle"
              className="viz-label"
            >
              {label}
            </text>
          );
        })}
      </g>
    );
  };
  return (
    <svg viewBox="0 0 360 200" className="visual" role="img" aria-label={spec.aria_label}>
      {pre.length >= 3 && draw(pre, 90, 170, spec.pre_edge_labels)}
      {img.length >= 3 && draw(img, 275, 170, spec.image_edge_labels)}
    </svg>
  );
}

function LinearSystem({ spec }: { spec: VisualSpec }) {
  const min = spec.min ?? -9;
  const max = spec.max ?? 9;
  const size = 340;
  const pad = 30;
  const scale = (size - 2 * pad) / (max - min);
  const pos = (v: number) => pad + (v - min) * scale;
  const yPos = (v: number) => size - pos(v);
  const ticks = Array.from({ length: max - min + 1 }, (_, i) => min + i);
  const endpointsFor = (line: { m_num: number; m_den: number; i_num: number; i_den: number }) => {
    const m = line.m_num / line.m_den;
    const intercept = line.i_num / line.i_den;
    const xAt = (y: number) => (y - intercept) / m;
    const candidates: [number, number][] =
      m === 0
        ? [[min, intercept], [max, intercept]]
        : [
            [min, m * min + intercept],
            [max, m * max + intercept],
            [xAt(min), min],
            [xAt(max), max],
          ];
    return candidates
      .filter(([x, y]) => x >= min - 1e-9 && x <= max + 1e-9 && y >= min - 1e-9 && y <= max + 1e-9)
      .slice(0, 2);
  };
  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="visual" role="img" aria-label={spec.aria_label ?? "Two lines on a coordinate plane"}>
      {ticks.map((t) => (
        <g key={`g${t}`}>
          <line x1={pad} y1={yPos(t)} x2={size - pad} y2={yPos(t)} className="viz-grid" />
          <line x1={pos(t)} y1={pad} x2={pos(t)} y2={size - pad} className="viz-grid" />
        </g>
      ))}
      <line x1={pad} y1={yPos(0)} x2={size - pad} y2={yPos(0)} className="viz-axis" />
      <line x1={pos(0)} y1={pad} x2={pos(0)} y2={size - pad} className="viz-axis" />
      {ticks.filter((t) => t !== 0 && t % 2 === 0).map((t) => (
        <g key={t}>
          <text x={pos(t)} y={yPos(0) + 15} textAnchor="middle" className="viz-tick-label">{t}</text>
          <text x={pos(0) - 8} y={yPos(t) + 4} textAnchor="end" className="viz-tick-label">{t}</text>
        </g>
      ))}
      {(spec.lines ?? []).map((line, i) => {
        const endpoints = endpointsFor(line);
        return endpoints.length === 2 ? (
          <line
            key={i}
            x1={pos(endpoints[0][0])}
            y1={yPos(endpoints[0][1])}
            x2={pos(endpoints[1][0])}
            y2={yPos(endpoints[1][1])}
            className={i === 0 ? "viz-curve" : "viz-curve-b"}
          />
        ) : null;
      })}
    </svg>
  );
}

function RightTriangle({ spec }: { spec: VisualSpec }) {
  const a = spec.a ?? 3;
  const b = spec.b ?? 4;
  const width = 300;
  const height = 230;
  const pad = 42;
  const unit = Math.min((width - 2 * pad) / b, (height - 2 * pad) / a);
  const x0 = pad;
  const y0 = height - pad;
  const x1 = x0 + b * unit;
  const y1 = y0 - a * unit;
  const midHypX = (x0 + x1) / 2;
  const midHypY = (y0 + y1) / 2;
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="visual" role="img" aria-label={spec.aria_label ?? "A right triangle"}>
      <path d={`M ${x0} ${y0} L ${x1} ${y0} L ${x0} ${y1} Z`} className="viz-cell viz-cell-a" />
      <rect x={x0} y={y0 - 14} width="14" height="14" className="viz-right-angle" />
      <text x={(x0 + x1) / 2} y={y0 + 22} textAnchor="middle" className="viz-label">{spec.leg_b}</text>
      <text x={x0 - 20} y={(y0 + y1) / 2 + 4} textAnchor="middle" className="viz-label">{spec.leg_a}</text>
      <text x={midHypX + 16} y={midHypY - 8} textAnchor="middle" className="viz-label">{spec.hyp}</text>
    </svg>
  );
}

function DistanceSegment({ spec }: { spec: VisualSpec }) {
  const bound = 9;
  const size = 320;
  const pad = 26;
  const scale = (size - 2 * pad) / (2 * bound);
  const pos = (v: number) => pad + (v + bound) * scale;
  const yPos = (v: number) => size - pos(v);
  const points = spec.points ?? [];
  const labels = spec.labels ?? [];
  const [p1, p2] = points;
  const corner = p1 && p2 ? [p2[0], p1[1]] : null;
  const collinear =
    p1 && p2 && (p1[0] === p2[0] || p1[1] === p2[1]);
  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="visual" role="img" aria-label={spec.aria_label ?? "Two points on a coordinate plane"}>
      {Array.from({ length: 2 * bound + 1 }, (_, i) => i - bound).map((t) => (
        <g key={`g${t}`}>
          <line x1={pad} y1={yPos(t)} x2={size - pad} y2={yPos(t)} className={t === 0 ? "viz-axis" : "viz-grid"} />
          <line x1={pos(t)} y1={pad} x2={pos(t)} y2={size - pad} className={t === 0 ? "viz-axis" : "viz-grid"} />
        </g>
      ))}
      {p1 && p2 && corner && (
        <g>
          {!collinear && (
            <>
              <line x1={pos(p1[0])} y1={yPos(p1[1])} x2={pos(corner[0])} y2={yPos(corner[1])} className="viz-hidden" />
              <line x1={pos(corner[0])} y1={yPos(corner[1])} x2={pos(p2[0])} y2={yPos(p2[1])} className="viz-hidden" />
              <rect
                x={pos(corner[0]) + (p1[0] < corner[0] ? -9 : 0)}
                y={yPos(corner[1]) + (p2[1] > corner[1] ? -9 : 0)}
                width="9" height="9" className="viz-right-angle"
              />
            </>
          )}
          <line x1={pos(p1[0])} y1={yPos(p1[1])} x2={pos(p2[0])} y2={yPos(p2[1])} className="viz-curve" />
        </g>
      )}
      {points.map((p, i) => (
        <g key={i}>
          <circle cx={pos(p[0])} cy={yPos(p[1])} r="5" className="viz-point viz-point-a" />
          <text x={pos(p[0]) + 9} y={yPos(p[1]) - 7} className="viz-label">{labels[i]}</text>
        </g>
      ))}
    </svg>
  );
}

function Scatterplot({ spec }: { spec: VisualSpec }) {
  const size = 320;
  const pad = 36;
  const xMax = spec.x_max ?? 10;
  const yMax = spec.y_max ?? 10;
  const span = size - pad - 14;
  const xFor = (v: number) => pad + (v / xMax) * span;
  const yFor = (v: number) => size - pad - (v / yMax) * span;
  const ticks = Array.from({ length: xMax + 1 }, (_, i) => i);
  const fit = spec.fit;
  const fitEnds = () => {
    if (!fit) return null;
    const m = fit.m_num / fit.m_den;
    const intercept = fit.i_num / fit.i_den;
    const xAt = (y: number) => (y - intercept) / m;
    const candidates: [number, number][] =
      m === 0
        ? [[0, intercept], [xMax, intercept]]
        : [
            [0, intercept],
            [xMax, m * xMax + intercept],
            [xAt(0), 0],
            [xAt(yMax), yMax],
          ];
    const inside = candidates.filter(
      ([x, y]) => x >= -1e-9 && x <= xMax + 1e-9 && y >= -1e-9 && y <= yMax + 1e-9
    );
    return inside.length >= 2 ? inside.slice(0, 2) : null;
  };
  const ends = fitEnds();
  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="visual" role="img" aria-label={spec.aria_label ?? "A scatterplot"}>
      {ticks.map((t) => (
        <g key={`g${t}`}>
          <line x1={pad} y1={yFor(t)} x2={size - 14} y2={yFor(t)} className="viz-grid" />
          <line x1={xFor(t)} y1={14} x2={xFor(t)} y2={size - pad} className="viz-grid" />
        </g>
      ))}
      <line x1={pad} y1={size - pad} x2={size - 14} y2={size - pad} className="viz-axis" />
      <line x1={pad} y1={14} x2={pad} y2={size - pad} className="viz-axis" />
      {ticks.filter((t) => t !== 0 && t % 2 === 0).map((t) => (
        <g key={t}>
          <text x={xFor(t)} y={size - pad + 16} textAnchor="middle" className="viz-tick-label">{t}</text>
          <text x={pad - 8} y={yFor(t) + 4} textAnchor="end" className="viz-tick-label">{t}</text>
        </g>
      ))}
      {ends && (
        <line x1={xFor(ends[0][0])} y1={yFor(ends[0][1])} x2={xFor(ends[1][0])} y2={yFor(ends[1][1])} className="viz-fit" />
      )}
      {(spec.points ?? []).map((p, i) => (
        <circle key={i} cx={xFor(p[0])} cy={yFor(p[1])} r="4.5" className="viz-point viz-point-a" />
      ))}
    </svg>
  );
}

const COLOR_FILLS: Record<string, string> = {
  red: "#ef4444",
  blue: "#3b82f6",
  green: "#22c55e",
  yellow: "#eab308",
  purple: "#a855f7",
};

function Spinner({ spec }: { spec: VisualSpec }) {
  const sections = spec.sections ?? [];
  const size = 300;
  const cx = 150;
  const cy = 150;
  const radius = 120;
  const labelRadius = 82;
  const n = sections.length || 1;
  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="visual" role="img" aria-label={spec.aria_label ?? "A spinner"}>
      <circle cx={cx} cy={cy} r={radius + 6} className="viz-spinner-rim" />
      {sections.map((color, i) => {
        const a0 = (i / n) * 2 * Math.PI - Math.PI / 2;
        const a1 = ((i + 1) / n) * 2 * Math.PI - Math.PI / 2;
        const x0 = cx + radius * Math.cos(a0);
        const y0 = cy + radius * Math.sin(a0);
        const x1 = cx + radius * Math.cos(a1);
        const y1 = cy + radius * Math.sin(a1);
        const mid = (a0 + a1) / 2;
        return (
          <g key={i}>
            <path
              d={`M ${cx} ${cy} L ${x0} ${y0} A ${radius} ${radius} 0 0 1 ${x1} ${y1} Z`}
              fill={COLOR_FILLS[color] ?? "#94a3b8"}
              className="viz-sector"
            />
            <text
              x={cx + labelRadius * Math.cos(mid)}
              y={cy + labelRadius * Math.sin(mid) + 4}
              textAnchor="middle"
              className="viz-sector-label"
            >
              {color}
            </text>
          </g>
        );
      })}
      <line x1={cx} y1={cy - 14} x2={cx} y2={cy - radius - 2} className="viz-arrow" markerEnd="url(#viz-arrowhead)" />
      <circle cx={cx} cy={cy} r="7" className="viz-arrow" />
      <defs>
        <marker id="viz-arrowhead" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">
          <path d="M 0 0 L 8 4 L 0 8 Z" className="viz-arrow" />
        </marker>
      </defs>
    </svg>
  );
}

function MarbleBag({ spec }: { spec: VisualSpec }) {
  const marbles = spec.marbles ?? [];
  const perRow = 6;
  const rows = Math.max(1, Math.ceil(marbles.length / perRow));
  const width = 320;
  const height = 110 + rows * 44;
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="visual" role="img" aria-label={spec.aria_label ?? "A bag of marbles"}>
      <rect x="30" y="18" width={width - 60} height={height - 30} rx="22" className="viz-bag" />
      {marbles.map((color, i) => {
        const row = Math.floor(i / perRow);
        const inRow = Math.min(perRow, marbles.length - row * perRow);
        const gap = (width - 110) / Math.max(1, inRow - 1);
        const x = inRow === 1 ? width / 2 : 55 + i % perRow * gap;
        const y = 62 + row * 44;
        return <circle key={i} cx={x} cy={y} r="15" fill={COLOR_FILLS[color] ?? "#94a3b8"} className="viz-sector" />;
      })}
    </svg>
  );
}

function FrequencyTable({ spec }: { spec: VisualSpec }) {
  const cols = spec.col_labels ?? [];
  const rows = spec.row_labels ?? [];
  const cells = spec.cells ?? [];
  // The Total row/column always render — empty when the tier asks the
  // learner to produce them.
  const showTotals = spec.row_totals != null;
  return (
    <table className="viz-table" aria-label={spec.aria_label ?? "A two-way frequency table"}>
      <thead>
        <tr>
          <th scope="col" />
          {cols.map((c, i) => <th key={i} scope="col">{c}</th>)}
          <th scope="col">Total</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i}>
            <th scope="row">{r}</th>
            {(cells[i] ?? []).map((v, j) => <td key={j}>{v}</td>)}
            <td className="viz-table-total">{showTotals ? spec.row_totals![i] : ""}</td>
          </tr>
        ))}
        <tr>
          <th scope="row">Total</th>
          {cols.map((_, j) => (
            <td key={j} className="viz-table-total">{showTotals ? spec.col_totals![j] : ""}</td>
          ))}
          <td className="viz-table-total">{showTotals ? spec.grand_total : ""}</td>
        </tr>
      </tbody>
    </table>
  );
}

function NumberLine({ spec, compare = false }: { spec: VisualSpec; compare?: boolean }) {
  const min = spec.min ?? 0;
  const max = spec.max ?? 10;
  const width = 360;
  const pad = 24;
  const xFor = (v: number) => pad + ((v - min) / (max - min)) * (width - 2 * pad);
  const y = 60;
  const ticks = Array.from({ length: max - min + 1 }, (_, i) => min + i);
  const a = spec.a ?? 0;
  const b = spec.b ?? 0;
  const result = spec.result ?? a + b;

  return (
    <svg viewBox={`0 0 ${width} 110`} className="visual" role="img" aria-label={spec.aria_label}>
      <line x1={pad} y1={y} x2={width - pad} y2={y} className="viz-axis" />
      {ticks.map((t) => (
        <g key={t}>
          <line x1={xFor(t)} y1={y - 5} x2={xFor(t)} y2={y + 5} className="viz-tick" />
          <text x={xFor(t)} y={y + 20} textAnchor="middle" className="viz-tick-label">{t}</text>
        </g>
      ))}
      {compare ? (
        <>
          <circle cx={xFor(a)} cy={y} r="6" className="viz-point viz-point-a" />
          <text x={xFor(a)} y={y - 14} textAnchor="middle" className="viz-label">{a}</text>
          <circle cx={xFor(b)} cy={y} r="6" className="viz-point viz-point-b" />
          <text x={xFor(b)} y={y - 14} textAnchor="middle" className="viz-label">{b}</text>
        </>
      ) : (
        <>
          <path d={`M ${xFor(0)} ${y - 10} Q ${(xFor(0) + xFor(a)) / 2} ${y - 34} ${xFor(a)} ${y - 10}`} className="viz-hop viz-hop-a" markerEnd="url(#vizArrowA)" />
          <path d={`M ${xFor(a)} ${y - 10} Q ${(xFor(a) + xFor(result)) / 2} ${y - 44} ${xFor(result)} ${y - 10}`} className="viz-hop viz-hop-b" markerEnd="url(#vizArrowB)" />
          <circle cx={xFor(result)} cy={y} r="6" className="viz-point viz-point-b" />
          <defs>
            <marker id="vizArrowA" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" className="viz-arrow-a" /></marker>
            <marker id="vizArrowB" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" className="viz-arrow-b" /></marker>
          </defs>
          <text x={(xFor(0) + xFor(a)) / 2} y={y - 30} textAnchor="middle" className="viz-hop-label">{a >= 0 ? `+${a}` : a}</text>
          <text x={(xFor(a) + xFor(result)) / 2} y={y - 48} textAnchor="middle" className="viz-hop-label">{b >= 0 ? `+${b}` : b}</text>
        </>
      )}
    </svg>
  );
}


function XYTable({ spec }: { spec: VisualSpec }) {
  const pairs = spec.pairs ?? [];
  const labels = spec.col_labels ?? ["x", "y"];
  return (
    <table className="viz-table" aria-label={spec.aria_label ?? "A table of x and y values"}>
      <thead>
        <tr>
          <th scope="col">{labels[0]}</th>
          <th scope="col">{labels[1]}</th>
        </tr>
      </thead>
      <tbody>
        {pairs.map((pair, i) => (
          <tr key={i}>
            <td>{pair[0]}</td>
            <td>{pair[1]}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function InequalityLine({ spec }: { spec: VisualSpec }) {
  const min = spec.min ?? 0;
  const max = spec.max ?? 10;
  const point = spec.point ?? 0;
  const closed = spec.closed ?? false;
  const left = spec.direction !== "right";
  const width = 360;
  const pad = 24;
  const xFor = (v: number) => pad + ((v - min) / (max - min)) * (width - 2 * pad);
  const y = 60;
  const ticks = Array.from({ length: max - min + 1 }, (_, i) => min + i);
  const rayX1 = left ? pad - 4 : xFor(point);
  const rayX2 = left ? xFor(point) : width - pad + 4;

  return (
    <svg viewBox={`0 0 ${width} 110`} className="visual" role="img" aria-label={spec.aria_label}>
      <line x1={pad} y1={y} x2={width - pad} y2={y} className="viz-axis" />
      {ticks.map((t) => (
        <g key={t}>
          <line x1={xFor(t)} y1={y - 5} x2={xFor(t)} y2={y + 5} className="viz-tick" />
          <text x={xFor(t)} y={y + 20} textAnchor="middle" className="viz-tick-label">{t}</text>
        </g>
      ))}
      <line x1={rayX1} y1={y} x2={rayX2} y2={y} className="viz-ineq-ray" />
      <polygon
        points={left
          ? `${pad - 10},${y} ${pad},${y - 5} ${pad},${y + 5}`
          : `${width - pad + 10},${y} ${width - pad},${y - 5} ${width - pad},${y + 5}`}
        className="viz-ineq-tip"
      />
      <circle
        cx={xFor(point)}
        cy={y}
        r="6"
        className={closed ? "viz-point viz-point-a" : "viz-ineq-open"}
      />
      <text x={xFor(point)} y={y + 34} textAnchor="middle" className="viz-label">{point}</text>
    </svg>
  );
}

function DotPlot({ spec }: { spec: VisualSpec }) {
  const data = spec.data ?? [];
  const min = spec.min ?? Math.min(...data, 0);
  const max = spec.max ?? Math.max(...data, 10);
  const width = 360;
  const pad = 24;
  const xFor = (v: number) => pad + ((v - min) / (max - min)) * (width - 2 * pad);
  const axisY = 120;
  const ticks = Array.from({ length: max - min + 1 }, (_, i) => min + i);
  const counts = new Map<number, number>();
  for (const v of data) counts.set(v, (counts.get(v) ?? 0) + 1);
  const stacks = new Map<number, number>();

  return (
    <svg viewBox={`0 0 ${width} 140`} className="visual" role="img" aria-label={spec.aria_label}>
      <line x1={pad} y1={axisY} x2={width - pad} y2={axisY} className="viz-axis" />
      {ticks.map((t) => (
        <g key={t}>
          <line x1={xFor(t)} y1={axisY - 5} x2={xFor(t)} y2={axisY + 5} className="viz-tick" />
          <text
            x={xFor(t)}
            y={axisY + 18}
            textAnchor="middle"
            className={t === spec.highlight ? "viz-label" : "viz-tick-label"}
          >
            {t}
          </text>
        </g>
      ))}
      {data.map((v, i) => {
        const stack = stacks.get(v) ?? 0;
        stacks.set(v, stack + 1);
        return (
          <circle
            key={i}
            cx={xFor(v)}
            cy={axisY - 11 - stack * 13}
            r="5"
            className="viz-point viz-point-a"
          />
        );
      })}
    </svg>
  );
}

function ShapeArea({ spec }: { spec: VisualSpec }) {
  const width = 360;
  const height = 200;
  const pad = 34;
  const base = spec.base ?? 8;
  const h = spec.height ?? 5;
  const top = spec.top;
  const shape = spec.shape ?? "triangle";
  const unit = Math.min((width - 2 * pad - 30) / base, (height - 2 * pad) / h);
  const bw = base * unit;
  const hh = h * unit;
  const botY = height - pad;
  const topY = botY - hh;
  const x0 = (width - bw) / 2;
  const x1 = x0 + bw;
  const midX = (x0 + x1) / 2;
  const off = bw * 0.22;
  const tw = (top ?? 0) * unit;

  const points =
    shape === "triangle"
      ? `${x0},${botY} ${x1},${botY} ${midX},${topY}`
      : shape === "trapezoid"
        ? `${x0},${botY} ${x1},${botY} ${x1 - off},${topY} ${x0 + off + (bw - tw - 2 * off)},${topY}`
        : `${x0},${botY} ${x1},${botY} ${x1 - off},${topY} ${x0 - off},${topY}`;
  const heightX = shape === "trapezoid" ? x1 - off : midX;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="visual" role="img" aria-label={spec.aria_label}>
      <polygon points={points} className="viz-curve" fill="none" />
      <line x1={heightX} y1={topY} x2={heightX} y2={botY} className="viz-hidden" />
      <rect x={heightX} y={botY - 10} width="10" height="10" className="viz-right-angle" />
      <text x={midX} y={botY + 20} textAnchor="middle" className="viz-label">
        {base}
      </text>
      <text x={heightX + 8} y={(topY + botY) / 2} className="viz-label">
        {h}
      </text>
      {shape === "trapezoid" && top != null && (
        <text x={x1 - off - tw / 2} y={topY - 8} textAnchor="middle" className="viz-label">
          {top}
        </text>
      )}
      {shape === "parallelogram" && spec.slant != null && (
        <text x={x0 - off / 2 - 10} y={(topY + botY) / 2} textAnchor="end" className="viz-label">
          {spec.slant}
        </text>
      )}
    </svg>
  );
}

function RadicalLine({ spec }: { spec: VisualSpec }) {
  const min = spec.min ?? 0;
  const max = spec.max ?? 10;
  const markers = spec.markers ?? [];
  const width = 360;
  const pad = 24;
  const xFor = (v: number) => pad + ((v - min) / (max - min)) * (width - 2 * pad);
  const y = 60;
  const ticks = Array.from({ length: max - min + 1 }, (_, i) => min + i);

  return (
    <svg viewBox={`0 0 ${width} 110`} className="visual" role="img" aria-label={spec.aria_label}>
      <line x1={pad} y1={y} x2={width - pad} y2={y} className="viz-axis" />
      {ticks.map((t) => (
        <g key={t}>
          <line x1={xFor(t)} y1={y - 5} x2={xFor(t)} y2={y + 5} className="viz-tick" />
          <text x={xFor(t)} y={y + 20} textAnchor="middle" className="viz-tick-label">{t}</text>
        </g>
      ))}
      {markers.map((m) => (
        <g key={m.label}>
          <circle cx={xFor(m.position)} cy={y} r="6" className="viz-point viz-point-a" />
          <text x={xFor(m.position)} y={y - 14} textAnchor="middle" className="viz-label">{m.label}</text>
        </g>
      ))}
    </svg>
  );
}

function DecimalPlaceValue({ spec }: { spec: VisualSpec }) {
  const whole = Math.max(0, Math.floor(spec.whole ?? 0));
  const tenths = Math.min(9, Math.max(0, Math.floor(spec.tenths ?? 0)));
  const hundredths = Math.min(9, Math.max(0, Math.floor(spec.hundredths ?? 0)));
  const cells = [
    { label: "Ones", value: whole },
    { label: "Tenths", value: tenths },
    { label: "Hundredths", value: hundredths },
  ];
  return (
    <svg viewBox="0 0 390 145" className="visual elementary-visual" role="img" aria-label={spec.aria_label}>
      {cells.map((cell, index) => (
        <g key={cell.label}>
          <rect x={15 + index * 125} y="18" width="110" height="92" className="viz-cell" />
          <text x={70 + index * 125} y="48" textAnchor="middle" className="viz-label">{cell.label}</text>
          <text x={70 + index * 125} y="88" textAnchor="middle" className="viz-term">{cell.value}</text>
        </g>
      ))}
      <text x="195" y="132" textAnchor="middle" className="viz-label">
        {whole}.{tenths}{hundredths}
      </text>
    </svg>
  );
}

function SolidModel({ spec }: { spec: VisualSpec }) {
  const solid = spec.solid ?? "rectangular_prism";
  const label = spec.aria_label;
  if (solid === "rectangular_prism") {
    return (
      <svg viewBox="0 0 360 210" className="visual elementary-visual" role="img" aria-label={label}>
        <path d="M70 70 L230 70 L290 35 L130 35 Z" className="viz-cell" />
        <path d="M230 70 L290 35 L290 135 L230 170 Z" className="viz-cell viz-cell-b" />
        <rect x="70" y="70" width="160" height="100" className="viz-cell viz-cell-a" />
        {spec.l != null && <text x="150" y="190" textAnchor="middle" className="viz-label">l = {spec.l}</text>}
        {spec.h != null && <text x="216" y="125" textAnchor="middle" className="viz-label">h = {spec.h}</text>}
        {spec.w != null && <text x="297" y="85" textAnchor="middle" className="viz-label">w = {spec.w}</text>}
      </svg>
    );
  }
  if (solid === "square_pyramid") {
    // Base parallelogram uses the same projection as the prism top; hidden
    // base edges and the altitude are dashed.
    return (
      <svg viewBox="0 0 360 210" className="visual elementary-visual" role="img" aria-label={label}>
        <path d="M70 150 L130 115 L290 115" className="viz-hidden" />
        <path d="M70 150 L230 150 L290 115" className="viz-cell" fill="none" />
        <line x1="180" y1="40" x2="70" y2="150" className="viz-axis" />
        <line x1="180" y1="40" x2="230" y2="150" className="viz-axis" />
        <line x1="180" y1="40" x2="290" y2="115" className="viz-axis" />
        <line x1="180" y1="40" x2="130" y2="115" className="viz-hidden" />
        <line x1="180" y1="40" x2="180" y2="132" className="viz-hidden" />
        {spec.b != null && <text x="150" y="170" textAnchor="middle" className="viz-label">b = {spec.b}</text>}
        {spec.h != null && <text x="195" y="90" className="viz-label">h = {spec.h}</text>}
      </svg>
    );
  }
  if (solid === "cylinder") {
    return (
      <svg viewBox="0 0 360 210" className="visual elementary-visual" role="img" aria-label={label}>
        <path d="M100 160 A80 22 0 0 0 260 160" className="viz-hidden" />
        <path d="M100 160 A80 22 0 0 1 260 160" className="viz-axis" fill="none" />
        <ellipse cx="180" cy="60" rx="80" ry="22" className="viz-cell viz-cell-a" />
        <line x1="100" y1="60" x2="100" y2="160" className="viz-axis" />
        <line x1="260" y1="60" x2="260" y2="160" className="viz-axis" />
        <line x1="180" y1="60" x2="260" y2="60" className="viz-hidden" />
        {spec.r != null && <text x="220" y="52" textAnchor="middle" className="viz-label">r = {spec.r}</text>}
        {spec.h != null && <text x="278" y="115" className="viz-label">h = {spec.h}</text>}
      </svg>
    );
  }
  // cone
  return (
    <svg viewBox="0 0 360 210" className="visual elementary-visual" role="img" aria-label={label}>
      <path d="M100 150 A80 20 0 0 0 260 150" className="viz-hidden" />
      <path d="M100 150 A80 20 0 0 1 260 150" className="viz-axis" fill="none" />
      <line x1="180" y1="45" x2="100" y2="150" className="viz-axis" />
      <line x1="180" y1="45" x2="260" y2="150" className="viz-axis" />
      <line x1="180" y1="45" x2="180" y2="150" className="viz-hidden" />
      <line x1="180" y1="150" x2="260" y2="150" className="viz-hidden" />
      {spec.r != null && <text x="220" y="168" textAnchor="middle" className="viz-label">r = {spec.r}</text>}
      {spec.h != null && <text x="192" y="100" className="viz-label">h = {spec.h}</text>}
    </svg>
  );
}


function AlgebraTiles({ spec }: { spec: VisualSpec }) {
  const groups = spec.groups ?? [];
  return (
    <div className="visual algebra-tiles" role="img" aria-label={spec.aria_label}>
      {groups.map((group) => (
        <div className="algebra-tile-group" key={group.key}>
          <span className="viz-label">{group.key === "constant^0" ? "constants" : group.key.replace("^1", "")}</span>
          <div>
            {group.terms.map((term, index) => (
              <span className="algebra-tile" key={`${group.key}-${index}`}>
                {term.label}
              </span>
            ))}
          </div>
        </div>
      ))}
      <p className="viz-label">Combine coefficients only inside the same group.</p>
    </div>
  );
}

function PolynomialSignChange({ spec }: { spec: VisualSpec }) {
  const renderTerms = (terms: AlgebraTerm[]) =>
    terms.map((term, index) => (
      <span className={`algebra-tile ${term.sign_changed ? "sign-changed" : ""}`} key={index}>
        {term.coefficient > 0 && index > 0 ? "+" : ""}{term.coefficient}
        {term.variable ?? ""}{term.degree > 1 ? `^${term.degree}` : ""}
      </span>
    ));
  return (
    <div className="visual polynomial-sign-model" role="img" aria-label={spec.aria_label}>
      <div>{renderTerms(spec.left_terms ?? [])}</div>
      <span className="viz-label">{spec.operation === "-" ? "subtract the group → add its opposite" : "add the group"}</span>
      <div>{renderTerms(spec.transformed_right_terms ?? [])}</div>
    </div>
  );
}

function Pan({ pan, x }: { pan: PanSpec; x: number }) {
  const blockW = 26;
  const unitW = 10;
  const unitRows = Math.ceil(pan.units / 6);
  const items: React.ReactNode[] = [];
  for (let i = 0; i < pan.x_count; i += 1) {
    items.push(
      <g key={`x${i}`}>
        <rect x={x + i * (blockW + 4)} y={60 - 30} width={blockW} height={28} rx="3" className="viz-cell viz-cell-a" />
        <text x={x + i * (blockW + 4) + blockW / 2} y={60 - 11} textAnchor="middle" className="viz-term">x</text>
      </g>,
    );
  }
  const unitX = x + pan.x_count * (blockW + 4) + (pan.x_count ? 8 : 0);
  for (let i = 0; i < pan.units; i += 1) {
    const row = Math.floor(i / 6);
    const col = i % 6;
    items.push(
      <rect
        key={`u${i}`}
        x={unitX + col * (unitW + 2)}
        y={60 - 2 - (row + 1) * (unitW + 2)}
        width={unitW}
        height={unitW}
        rx="2"
        className="viz-cell viz-cell-b"
      />,
    );
  }
  const panW = Math.max(60, unitX - x + Math.min(pan.units, 6) * (unitW + 2));
  return (
    <g>
      {items}
      <line x1={x - 6} y1={62} x2={x + panW + 6} y2={62} className="viz-axis" strokeWidth={3} />
      {unitRows > 2 && <text x={x + panW / 2} y={78} textAnchor="middle" className="viz-label">{pan.units}</text>}
    </g>
  );
}

function BalanceScale({ spec }: { spec: VisualSpec }) {
  const left = spec.left ?? { x_count: 0, units: 0 };
  const right = spec.right ?? { x_count: 0, units: 0 };
  const width = 420;
  const leftLabel = [left.x_count ? `${left.x_count === 1 ? "" : left.x_count}x` : "", left.units ? String(left.units) : ""].filter(Boolean).join(" + ") || "0";
  const rightLabel = [right.x_count ? `${right.x_count === 1 ? "" : right.x_count}x` : "", right.units ? String(right.units) : ""].filter(Boolean).join(" + ") || "0";
  return (
    <svg viewBox={`0 0 ${width} 130`} className="visual" role="img" aria-label={spec.aria_label}>
      <line x1={width / 2} y1={70} x2={width / 2} y2={112} className="viz-axis" strokeWidth={4} />
      <line x1={40} y1={70} x2={width - 40} y2={70} className="viz-axis" strokeWidth={4} />
      <polygon points={`${width / 2 - 24},112 ${width / 2 + 24},112 ${width / 2},92`} className="viz-cell" />
      <Pan pan={left} x={48} />
      <Pan pan={right} x={width / 2 + 28} />
      <text x={width / 4 + 10} y={124} textAnchor="middle" className="viz-label">{leftLabel}</text>
      <text x={(3 * width) / 4 - 10} y={124} textAnchor="middle" className="viz-label">{rightLabel}</text>
    </svg>
  );
}

function FractionOperation({ spec }: { spec: VisualSpec }) {
  const first = spec.first ?? { numerator: 0, denominator: 1 };
  const second = spec.second ?? { numerator: 0, denominator: 1 };
  const common = Math.max(1, spec.common_denominator ?? Math.max(first.denominator, second.denominator));
  const width = 380;
  const x = 24;
  const barW = width - 48;
  const h = 34;
  const renderBar = (frac: FractionSpec, y: number) => {
    const scale = common / frac.denominator;
    const shaded = frac.numerator * scale;
    return (
      <g key={y}>
        {Array.from({ length: common }, (_, i) => (
          <rect key={i} x={x + (i * barW) / common} y={y} width={barW / common} height={h} className={`viz-cell ${i < shaded ? "viz-cell-a" : ""}`} />
        ))}
        {Array.from({ length: frac.denominator + 1 }, (_, i) => (
          <line key={`d${i}`} x1={x + (i * barW) / frac.denominator} y1={y - 3} x2={x + (i * barW) / frac.denominator} y2={y + h + 3} className="viz-axis" strokeWidth={2} />
        ))}
        <text x={x + barW + 6} y={y + h / 2 + 5} className="viz-label">{frac.numerator}/{frac.denominator}</text>
      </g>
    );
  };
  return (
    <svg viewBox={`0 0 ${width + 50} 140`} className="visual" role="img" aria-label={spec.aria_label}>
      {renderBar(first, 18)}
      <text x={x + barW / 2} y={72} textAnchor="middle" className="viz-term">{spec.operation === "-" ? "−" : "+"}</text>
      {renderBar(second, 84)}
      <text x={x} y={134} className="viz-label">each bar cut into {common} equal pieces</text>
    </svg>
  );
}

function TapeDiagram({ spec }: { spec: VisualSpec }) {
  const segments = spec.segments ?? [];
  const totalSpan = segments.reduce((sum, s) => sum + Math.max(0, s.span), 0) || 1;
  const width = 400;
  const x = 24;
  const barW = width - 48;
  const y = 36;
  const h = 44;
  let cursor = x;
  return (
    <svg viewBox={`0 0 ${width} 110`} className="visual" role="img" aria-label={spec.aria_label}>
      <line x1={x} y1={y - 12} x2={x + barW} y2={y - 12} className="viz-axis" strokeWidth={2} />
      <text x={x + barW / 2} y={y - 18} textAnchor="middle" className="viz-label">{spec.total_label}</text>
      {segments.map((segment, i) => {
        const w = (Math.max(0, segment.span) / totalSpan) * barW;
        const sx = cursor;
        cursor += w;
        return (
          <g key={i}>
            <rect x={sx} y={y} width={w} height={h} className={`viz-cell ${segment.highlight ? "viz-cell-a" : ""}`} />
            {w > 22 && <text x={sx + w / 2} y={y + h / 2 + 5} textAnchor="middle" className="viz-term">{segment.label}</text>}
          </g>
        );
      })}
    </svg>
  );
}

export default function ProblemVisual({ spec }: { spec: VisualSpec | null }) {
  if (!spec) return null;
  if (spec.type === "area_model") return <AreaModel spec={spec} />;
  if (spec.type === "balance_scale") return <BalanceScale spec={spec} />;
  if (spec.type === "fraction_operation") return <FractionOperation spec={spec} />;
  if (spec.type === "tape_diagram") return <TapeDiagram spec={spec} />;
  if (spec.type === "algebra_tiles") return <AlgebraTiles spec={spec} />;
  if (spec.type === "polynomial_sign_change") return <PolynomialSignChange spec={spec} />;
  if (spec.type === "number_line") return <NumberLine spec={spec} />;
  if (spec.type === "number_line_compare") return <NumberLine spec={spec} compare />;
  if (spec.type === "radical_line") return <RadicalLine spec={spec} />;
  if (spec.type === "inequality_line") return <InequalityLine spec={spec} />;
  if (spec.type === "dot_plot" || spec.type === "line_plot") return <DotPlot spec={spec} />;
  if (spec.type === "shape_area") return <ShapeArea spec={spec} />;
  if (spec.type === "array_model") return <ArrayModel spec={spec} />;
  if (spec.type === "fraction_bar" || spec.type === "ratio_bar") return <FractionBar spec={spec} />;
  if (spec.type === "coordinate_plane" || spec.type === "coordinate_point") return <CoordinatePlane spec={spec} />;
  if (spec.type === "linear_graph") return <LinearGraph spec={spec} />;
  if (spec.type === "parabola_graph") return <ParabolaGraph spec={spec} />;
  if (spec.type === "polynomial_graph") return <PolynomialGraph spec={spec} />;
  if (spec.type === "angle" || spec.type === "angle_diagram") return <AngleDiagram spec={spec} />;
  if (spec.type === "decimal_place_value") return <DecimalPlaceValue spec={spec} />;
  if (spec.type === "volume_model" || spec.type === "volume" || spec.type === "solid") return <SolidModel spec={spec} />;
  if (spec.type === "angle_pair") return <AnglePair spec={spec} />;
  if (spec.type === "intersecting_lines") return <IntersectingLines spec={spec} />;
  if (spec.type === "triangle_angles") return <TriangleAngles spec={spec} />;
  if (spec.type === "circle_measure") return <CircleMeasure spec={spec} />;
  if (spec.type === "composite_figure") return <CompositeFigure spec={spec} />;
  if (spec.type === "transformation") return <TransformPlane spec={spec} />;
  if (spec.type === "similar_figures") return <SimilarFigures spec={spec} />;
  if (spec.type === "linear_system") return <LinearSystem spec={spec} />;
  if (spec.type === "scatterplot") return <Scatterplot spec={spec} />;
  if (spec.type === "frequency_table") return <FrequencyTable spec={spec} />;
  if (spec.type === "xy_table") return <XYTable spec={spec} />;
  if (spec.type === "spinner") return <Spinner spec={spec} />;
  if (spec.type === "marble_bag") return <MarbleBag spec={spec} />;
  if (spec.type === "right_triangle") return <RightTriangle spec={spec} />;
  if (spec.type === "distance_segment") return <DistanceSegment spec={spec} />;
  if (spec.type === "exponential_graph") return <ExponentialGraph spec={spec} />;
  return null;
}
