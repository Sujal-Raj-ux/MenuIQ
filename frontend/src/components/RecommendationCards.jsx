const CATEGORY_LABELS = {
  placement: 'Placement',
  combo: 'Combo',
  promotion: 'Promotion',
  pricing: 'Pricing',
  retire: 'Retire',
};

export default function RecommendationCards({
  summary,
  recommendations,
  error,
  loading,
  embedded = false,
}) {
  if (loading) {
    const block = (
      <div className="state-block">
        <div className="spinner" />
        <p className="muted">Generating recommendations…</p>
      </div>
    );
    return embedded ? block : (
      <div className="card">
        <div className="card-header"><h2>Recommendations</h2></div>
        {block}
      </div>
    );
  }

  if (error) {
    const block = (
      <div className="error-banner">
        {error}
        <br />
        <small>Set GROQ_API_KEY in backend .env and restart the API.</small>
      </div>
    );
    return embedded ? block : (
      <div className="card">
        <div className="card-header"><h2>Recommendations</h2></div>
        {block}
      </div>
    );
  }

  if (!recommendations?.length) {
    return embedded ? (
      <p className="muted">No recommendations available.</p>
    ) : (
      <div className="card">
        <div className="card-header"><h2>Recommendations</h2></div>
        <p className="muted">No recommendations available.</p>
      </div>
    );
  }

  const content = (
    <>
      {summary && (
        <div className="exec-summary">
          <span className="exec-summary-label">Executive summary</span>
          <p>{summary}</p>
        </div>
      )}

      <div className="rec-list">
        {recommendations.map((rec) => (
          <article
            key={`${rec.priority}-${rec.title}`}
            className={`rec-card rec-accent-${rec.category}`}
          >
            <div className="rec-card-top">
              <span className="priority-badge">P{rec.priority}</span>
              <span className={`category-tag category-${rec.category}`}>
                {CATEGORY_LABELS[rec.category] || rec.category}
              </span>
            </div>
            <h3>{rec.title}</h3>
            <p>{rec.recommendation}</p>

            {rec.related_items?.length > 0 && (
              <div className="tag-row">
                {rec.related_items.map((item) => (
                  <span key={item} className="item-tag">{item}</span>
                ))}
              </div>
            )}

            {rec.supporting_facts?.length > 0 && (
              <ul className="facts">
                {rec.supporting_facts.map((fact) => (
                  <li key={fact}>{fact}</li>
                ))}
              </ul>
            )}
          </article>
        ))}
      </div>
    </>
  );

  if (embedded) return content;

  return (
    <div className="card">
      <div className="card-header">
        <h2>Recommendations</h2>
      </div>
      {content}
    </div>
  );
}
