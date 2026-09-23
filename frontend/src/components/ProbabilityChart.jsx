export default function ProbabilityChart({ probabilities, predicted }) {
  const entries = Object.entries(probabilities).sort((a, b) => b[1] - a[1]);

  return (
    <div className="prob-chart">
      {entries.map(([cls, prob]) => (
        <div className="prob-row" key={cls}>
          <span className={`prob-label ${cls === predicted ? "pred" : ""}`}>
            {cls}
          </span>
          <div className="prob-bar-bg">
            <div
              className={`prob-bar ${cls === predicted ? "pred" : ""}`}
              style={{ width: `${(prob * 100).toFixed(1)}%` }}
            />
          </div>
          <span className="prob-value">{(prob * 100).toFixed(1)}%</span>
        </div>
      ))}
    </div>
  );
}