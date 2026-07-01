import {
  CartesianGrid,
  Label,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from 'recharts';
import InfoTip from './InfoTip';

const QUADRANT_COLORS = {
  Star: '#16a34a',
  Plowhorse: '#2563eb',
  Puzzle: '#ea580c',
  Dog: '#64748b',
};

const QUADRANT_INFO = {
  Star: 'High popularity and high profit margin. Your best items — keep them prominent and protect their quality.',
  Plowhorse: 'High popularity but low margin. Customers love them, but they earn little — try raising price or bundling.',
  Puzzle: 'Low popularity but high margin. Profitable when sold — promote, reposition, or feature them more.',
  Dog: 'Low popularity and low margin. Weak performers — consider reworking, repricing, or removing them.',
};

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const item = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <strong>{item.name}</strong>
      <span className={`badge badge-${item.quadrant.toLowerCase()}`}>{item.quadrant}</span>
      <div>{item.units_sold} units sold</div>
      <div>${item.margin.toFixed(2)} margin</div>
    </div>
  );
}

function DotLabel({ x, y, name }) {
  return (
    <text x={x} y={y - 10} textAnchor="middle" className="chart-dot-label">
      {name}
    </text>
  );
}

export default function QuadrantChart({ items, popularityThreshold, marginThreshold }) {
  if (!items?.length) return null;

  const maxPop = Math.max(...items.map((i) => i.units_sold)) * 1.1;
  const maxMargin = Math.max(...items.map((i) => i.margin)) * 1.15;

  return (
    <div className="card">
      <div className="card-header">
        <h2>Menu Engineering Matrix</h2>
        <p className="muted">Popularity (units sold) × profitability (per-unit margin)</p>
      </div>

      <div className="quadrant-legend">
        {Object.entries(QUADRANT_COLORS).map(([name, color]) => (
          <span key={name} className="legend-item">
            <span className="legend-dot" style={{ background: color }} />
            {name}
            <InfoTip label={name} text={QUADRANT_INFO[name]} />
          </span>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={420}>
        <ScatterChart margin={{ top: 24, right: 24, bottom: 24, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />

          <ReferenceArea
            x1={popularityThreshold}
            x2={maxPop}
            y1={marginThreshold}
            y2={maxMargin}
            fill="#dcfce7"
            fillOpacity={0.35}
          />
          <ReferenceArea
            x1={0}
            x2={popularityThreshold}
            y1={marginThreshold}
            y2={maxMargin}
            fill="#ffedd5"
            fillOpacity={0.35}
          />
          <ReferenceArea
            x1={popularityThreshold}
            x2={maxPop}
            y1={0}
            y2={marginThreshold}
            fill="#dbeafe"
            fillOpacity={0.35}
          />
          <ReferenceArea
            x1={0}
            x2={popularityThreshold}
            y1={0}
            y2={marginThreshold}
            fill="#f1f5f9"
            fillOpacity={0.5}
          />

          <ReferenceLine x={popularityThreshold} stroke="#94a3b8" strokeDasharray="4 4">
            <Label value="Pop. threshold" position="insideTopRight" fill="#64748b" fontSize={11} />
          </ReferenceLine>
          <ReferenceLine y={marginThreshold} stroke="#94a3b8" strokeDasharray="4 4">
            <Label value="Margin threshold" position="insideTopLeft" fill="#64748b" fontSize={11} />
          </ReferenceLine>

          <XAxis
            type="number"
            dataKey="units_sold"
            name="Units sold"
            domain={[0, maxPop]}
            tick={{ fontSize: 12 }}
            label={{ value: 'Popularity (units sold)', position: 'insideBottom', offset: -8, fontSize: 12 }}
          />
          <YAxis
            type="number"
            dataKey="margin"
            name="Margin"
            domain={[0, maxMargin]}
            tick={{ fontSize: 12 }}
            tickFormatter={(v) => `$${v}`}
            label={{ value: 'Profitability ($)', angle: -90, position: 'insideLeft', fontSize: 12 }}
          />
          <ZAxis range={[80, 80]} />
          <Tooltip content={<CustomTooltip />} />

          {Object.keys(QUADRANT_COLORS).map((quadrant) => (
            <Scatter
              key={quadrant}
              name={quadrant}
              data={items.filter((i) => i.quadrant === quadrant)}
              fill={QUADRANT_COLORS[quadrant]}
              label={(props) => (
                <DotLabel x={props.x} y={props.y} name={props.payload?.name} />
              )}
            />
          ))}
        </ScatterChart>
      </ResponsiveContainer>

      <div className="quadrant-labels">
        <span>Puzzle <InfoTip label="Puzzle" text={QUADRANT_INFO.Puzzle} /></span>
        <span>Star <InfoTip label="Star" text={QUADRANT_INFO.Star} /></span>
        <span>Dog <InfoTip label="Dog" text={QUADRANT_INFO.Dog} /></span>
        <span>Plowhorse <InfoTip label="Plowhorse" text={QUADRANT_INFO.Plowhorse} /></span>
      </div>
    </div>
  );
}
