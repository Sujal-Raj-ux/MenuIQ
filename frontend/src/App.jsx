import { useEffect, useMemo, useState } from 'react';
import { fetchAssociations, fetchMenuAnalysis, fetchMenuMatrix } from './api';
import AssociationsView from './components/AssociationsView';
import ChatPanel from './components/ChatPanel';
import QuadrantChart from './components/QuadrantChart';
import RecommendationCards from './components/RecommendationCards';
import Tabs from './components/Tabs';
import UploadPanel from './components/UploadPanel';
import './App.css';

function App() {
  const [matrixData, setMatrixData] = useState(null);
  const [matrixError, setMatrixError] = useState(null);
  const [matrixLoading, setMatrixLoading] = useState(true);

  const [menuData, setMenuData] = useState(null);
  const [menuError, setMenuError] = useState(null);
  const [menuLoading, setMenuLoading] = useState(true);

  const [pairs, setPairs] = useState([]);
  const [assocError, setAssocError] = useState(null);
  const [assocLoading, setAssocLoading] = useState(true);

  // Uploaded dataset (null = demo data). Drives every analytics/chat fetch.
  const [uploadSummary, setUploadSummary] = useState(null);
  const datasetSessionId = uploadSummary?.session_id ?? null;

  const demoSessionId = useMemo(
    () => `session-${crypto.randomUUID?.() ?? Date.now()}`,
    [],
  );
  // Chat shares the dataset's session so the agent answers over the same data.
  const chatSessionId = datasetSessionId ?? demoSessionId;

  useEffect(() => {
    setMatrixLoading(true);
    setMatrixError(null);
    fetchMenuMatrix(datasetSessionId)
      .then(setMatrixData)
      .catch((err) => setMatrixError(err.message))
      .finally(() => setMatrixLoading(false));
  }, [datasetSessionId]);

  useEffect(() => {
    setMenuLoading(true);
    setMenuError(null);
    fetchMenuAnalysis(datasetSessionId)
      .then(setMenuData)
      .catch((err) => setMenuError(err.message))
      .finally(() => setMenuLoading(false));
  }, [datasetSessionId]);

  useEffect(() => {
    setAssocLoading(true);
    setAssocError(null);
    fetchAssociations(10, datasetSessionId)
      .then((data) => setPairs(data.pairs))
      .catch((err) => setAssocError(err.message))
      .finally(() => setAssocLoading(false));
  }, [datasetSessionId]);

  const recCount = menuData?.recommendations?.length ?? 0;

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-brand">
          <div className="logo-mark">M</div>
          <div>
            <h1>MenuIQ</h1>
            <p className="header-tagline">Menu optimization powered by POS analytics</p>
          </div>
        </div>
        <div className="header-meta">
          <span className="meta-pill">
            {matrixData?.items?.length ?? '—'} menu items
          </span>
          <span className="meta-pill meta-pill-live">
            {uploadSummary ? 'Your data' : 'Demo data'}
          </span>
        </div>
      </header>

      <main className="dashboard">
        <section className="dashboard-main">
          <UploadPanel
            activeSummary={uploadSummary}
            onUploaded={setUploadSummary}
            onReset={() => setUploadSummary(null)}
          />

          {matrixLoading && (
            <div className="card">
              <div className="state-block">
                <div className="spinner" />
                <p className="muted">Loading menu matrix…</p>
              </div>
            </div>
          )}
          {matrixError && !matrixData && (
            <div className="card">
              <div className="error-banner">Menu matrix unavailable: {matrixError}</div>
            </div>
          )}
          {matrixData && (
            <QuadrantChart
              items={matrixData.items}
              popularityThreshold={matrixData.popularity_threshold}
              marginThreshold={matrixData.margin_threshold}
            />
          )}

          <div className="card insights-card">
            <Tabs
              defaultTab="associations"
              tabs={[
                {
                  id: 'associations',
                  label: 'Top Associations',
                  badge: pairs.length || null,
                  content: (
                    <AssociationsView
                      pairs={pairs}
                      error={assocError}
                      loading={assocLoading}
                      embedded
                    />
                  ),
                },
                {
                  id: 'recommendations',
                  label: 'Recommendations',
                  badge: recCount || null,
                  content: (
                    <RecommendationCards
                      summary={menuData?.executive_summary}
                      recommendations={menuData?.recommendations}
                      error={menuError}
                      loading={menuLoading}
                      embedded
                    />
                  ),
                },
              ]}
            />
          </div>
        </section>

        <aside className="dashboard-side">
          <ChatPanel key={chatSessionId} sessionId={chatSessionId} />
        </aside>
      </main>

      <footer className="app-footer">
        <span>Analytics computed in Python/Pandas</span>
        <span className="footer-dot">·</span>
        <span>AI explains pre-computed results only</span>
      </footer>
    </div>
  );
}

export default App;
