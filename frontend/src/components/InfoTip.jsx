export default function InfoTip({ text, label, placement = 'top' }) {
  return (
    <span
      className="infotip"
      tabIndex={0}
      role="img"
      aria-label={label ? `${label}: ${text}` : text}
    >
      <span className="infotip-icon" aria-hidden="true">i</span>
      <span className={`infotip-bubble infotip-${placement}`} role="tooltip">
        {label && <strong>{label}</strong>}
        {text}
      </span>
    </span>
  );
}
