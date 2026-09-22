export interface VisualSpec {
  type: string;
  a?: number;
  b?: number;
  result?: number;
  min?: number;
  max?: number;
  numerator?: number;
  denominator?: number;
  x?: number;
  y?: number;
  aria_label?: string;
}

function AreaModel({ spec }: { spec: VisualSpec }) {
  const a = spec.a ?? 1; const b = spec.b ?? 1; const xW = 120;
  const bW = Math.min(120, Math.max(40, Math.abs(b) * 18));
  const h = Math.min(140, Math.max(48, Math.abs(a) * 22));
  const bx = 60; const by = 40;
  return <svg viewBox={`0 0 ${bx + xW + bW + 40} ${by + h + 50}`} className="visual" role="img" aria-label={spec.aria_label}>
    <text x={bx+xW/2} y={by-12} textAnchor="middle" className="viz-label">x</text>
    <text x={bx+xW+bW/2} y={by-12} textAnchor="middle" className="viz-label">{b}</text>
    <text x={bx-14} y={by+h/2} textAnchor="middle" className="viz-label">{a}</text>
    <rect x={bx} y={by} width={xW} height={h} className="viz-cell viz-cell-a" />
    <rect x={bx+xW} y={by} width={bW} height={h} className="viz-cell viz-cell-b" />
    <text x={bx+xW/2} y={by+h/2+6} textAnchor="middle" className="viz-term">{a}x</text>
    <text x={bx+xW+bW/2} y={by+h/2+6} textAnchor="middle" className="viz-term">{a}·{b}</text>
  </svg>;
}

function FractionBar({ spec }: { spec: VisualSpec }) {
  const denominator = Math.max(1, Math.floor(spec.denominator ?? spec.b ?? 1));
  const numerator = Math.min(denominator, Math.max(0, Math.floor(spec.numerator ?? spec.a ?? 0)));
  const width=360, x=24, y=35, h=54, cell=(width-48)/denominator;
  return <svg viewBox={`0 0 ${width} 125`} className="visual" role="img" aria-label={spec.aria_label ?? `${numerator} of ${denominator} equal parts shaded`}>
    {Array.from({length: denominator},(_,i)=><rect key={i} x={x+i*cell} y={y} width={cell} height={h} className={`viz-cell ${i<numerator?'viz-cell-a':''}`} />)}
    <text x={width/2} y={110} textAnchor="middle" className="viz-label">{numerator}/{denominator}</text>
  </svg>;
}

function CoordinatePlane({ spec }: { spec: VisualSpec }) {
  const min=spec.min ?? -5, max=spec.max ?? 5, px=spec.x ?? spec.a ?? 0, py=spec.y ?? spec.b ?? 0;
  const size=320, pad=28, scale=(size-2*pad)/(max-min), pos=(v:number)=>pad+(v-min)*scale, yPos=(v:number)=>size-pos(v);
  const ticks=Array.from({length:max-min+1},(_,i)=>min+i);
  return <svg viewBox={`0 0 ${size} ${size}`} className="visual" role="img" aria-label={spec.aria_label ?? `Coordinate plane with point at ${px}, ${py}`}>
    <line x1={pad} y1={yPos(0)} x2={size-pad} y2={yPos(0)} className="viz-axis" />
    <line x1={pos(0)} y1={pad} x2={pos(0)} y2={size-pad} className="viz-axis" />
    {ticks.map(t=><g key={t}><line x1={pos(t)} y1={yPos(0)-3} x2={pos(t)} y2={yPos(0)+3} className="viz-tick"/><line x1={pos(0)-3} y1={yPos(t)} x2={pos(0)+3} y2={yPos(t)} className="viz-tick"/></g>)}
    <circle cx={pos(px)} cy={yPos(py)} r="6" className="viz-point viz-point-a" />
    <text x={pos(px)+8} y={yPos(py)-8} className="viz-label">({px}, {py})</text>
  </svg>;
}

function NumberLine({ spec, compare=false }: { spec: VisualSpec; compare?: boolean }) {
  const min=spec.min??0,max=spec.max??10,width=360,pad=24,xFor=(v:number)=>pad+((v-min)/(max-min))*(width-2*pad),y=60;
  const ticks=Array.from({length:max-min+1},(_,i)=>min+i),a=spec.a??0,b=spec.b??0,result=spec.result??a+b;
  return <svg viewBox={`0 0 ${width} 110`} className="visual" role="img" aria-label={spec.aria_label}>
    <line x1={pad} y1={y} x2={width-pad} y2={y} className="viz-axis" />
    {ticks.map(t=><g key={t}><line x1={xFor(t)} y1={y-5} x2={xFor(t)} y2={y+5} className="viz-tick"/><text x={xFor(t)} y={y+20} textAnchor="middle" className="viz-tick-label">{t}</text></g>)}
    {compare?<><circle cx={xFor(a)} cy={y} r="6" className="viz-point viz-point-a"/><circle cx={xFor(b)} cy={y} r="6" className="viz-point viz-point-b"/></>:<><path d={`M ${xFor(0)} ${y-10} Q ${(xFor(0)+xFor(a))/2} ${y-34} ${xFor(a)} ${y-10}`} className="viz-hop viz-hop-a"/><path d={`M ${xFor(a)} ${y-10} Q ${(xFor(a)+xFor(result))/2} ${y-44} ${xFor(result)} ${y-10}`} className="viz-hop viz-hop-b"/><circle cx={xFor(result)} cy={y} r="6" className="viz-point viz-point-b"/></>}
  </svg>;
}

export default function ProblemVisual({spec}:{spec:VisualSpec|null}) {
  if(!spec) return null;
  if(spec.type==="area_model") return <AreaModel spec={spec}/>;
  if(spec.type==="number_line") return <NumberLine spec={spec}/>;
  if(spec.type==="number_line_compare") return <NumberLine spec={spec} compare/>;
  if(spec.type==="fraction_bar" || spec.type==="ratio_bar") return <FractionBar spec={spec}/>;
  if(spec.type==="coordinate_plane" || spec.type==="coordinate_point") return <CoordinatePlane spec={spec}/>;
  return null;
}
