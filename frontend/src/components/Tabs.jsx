import { useState } from 'react';

export default function Tabs({ tabs, defaultTab }) {
  const [active, setActive] = useState(defaultTab || tabs[0]?.id);

  const current = tabs.find((t) => t.id === active);

  return (
    <div className="tabs">
      <div className="tabs-list" role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={active === tab.id}
            className={`tab-btn ${active === tab.id ? 'tab-btn-active' : ''}`}
            onClick={() => setActive(tab.id)}
          >
            {tab.label}
            {tab.badge != null && <span className="tab-badge">{tab.badge}</span>}
          </button>
        ))}
      </div>
      <div className="tabs-panel" role="tabpanel">
        {current?.content}
      </div>
    </div>
  );
}
