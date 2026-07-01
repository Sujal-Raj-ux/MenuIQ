import InfoTip from './InfoTip';

const METRIC_INFO = {
  lift: 'How many times more likely customers add the second item when they order the first, versus ordering it on its own. Above 1× means a real pairing; higher is stronger.',
  attach: 'Of all orders containing the first item, the share that also include the second item (confidence).',
  support: 'The share of all orders that contain both items together. Shows how common the pairing is overall.',
};

export default function AssociationsView({ pairs, error, loading, embedded = false }) {
  const content = (
    <>
      {!embedded && (
        <div className="panel-intro">
          <p className="muted">
            Market-basket analysis — item pairs ranked by lift (how much more likely
            customers add B when they order A).
          </p>
        </div>
      )}

      {error && <div className="error-banner">{error}</div>}
      {loading && (
        <div className="state-block">
          <div className="spinner" />
          <p className="muted">Loading associations…</p>
        </div>
      )}

      {!loading && !error && pairs?.length > 0 && (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>When ordered</th>
                <th>Also adds</th>
                <th>
                  <span className="th-with-info">
                    Lift <InfoTip label="Lift" text={METRIC_INFO.lift} placement="bottom" />
                  </span>
                </th>
                <th>
                  <span className="th-with-info">
                    Attach rate <InfoTip label="Attach rate" text={METRIC_INFO.attach} placement="bottom" />
                  </span>
                </th>
                <th>
                  <span className="th-with-info">
                    Support <InfoTip label="Support" text={METRIC_INFO.support} placement="bottom" />
                  </span>
                </th>
              </tr>
            </thead>
            <tbody>
              {pairs.map((pair, index) => (
                <tr key={`${pair.antecedent_name}-${pair.consequent_name}`}>
                  <td className="rank-cell">{index + 1}</td>
                  <td>
                    <span className="item-name">{pair.antecedent_name}</span>
                  </td>
                  <td>
                    <span className="item-name">{pair.consequent_name}</span>
                  </td>
                  <td>
                    <span className={`lift-pill ${pair.lift >= 3 ? 'lift-high' : ''}`}>
                      {pair.lift.toFixed(2)}×
                    </span>
                  </td>
                  <td>{(pair.confidence * 100).toFixed(1)}%</td>
                  <td className="muted-cell">{(pair.support * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );

  if (embedded) return content;

  return (
    <div className="card">
      <div className="card-header">
        <h2>Top Associations</h2>
      </div>
      {content}
    </div>
  );
}
