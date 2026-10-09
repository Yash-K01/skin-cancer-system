import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  listPendingCases,
  approveCase,
  getRetrainingQueue,
  triggerRetrain,
} from "../api/endpoints";
import Logo from "../components/Logo";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export default function Admin() {
  const [pending, setPending] = useState([]);
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState(null);

  const refresh = async () => {
    setLoading(true);
    try {
      const [p, q] = await Promise.all([listPendingCases(), getRetrainingQueue()]);
      setPending(p.data);
      setQueue(q.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const handleApprove = async (id) => {
    await approveCase(id);
    setActionMsg(`Case #${id} approved and moved to retraining queue.`);
    refresh();
    setTimeout(() => setActionMsg(null), 4000);
  };

  const handleTrigger = async () => {
    const r = await triggerRetrain();
    setActionMsg(`Ready for retrain: ${r.data.ready_for_retrain} case(s).`);
    setTimeout(() => setActionMsg(null), 4000);
  };

  const imageUrl = (path) => {
    const name = path.split(/[\\/]/).pop();
    return `${API_BASE}/uploads/${name}`;
  };

  return (
    <div className="page page-clinical">
      <header className="topbar">
        <h1 className="brand">
          <Logo size={34} />
          <span>Admin Panel</span>
        </h1>
        <Link to="/predict" className="link-btn">Back</Link>
      </header>

      <main className="admin-layout">
        {actionMsg && (
          <div className="action-toast">
            <span className="action-icon">✓</span>
            <span>{actionMsg}</span>
          </div>
        )}

        <div className="stats">
          <div className="stat card-3d">
            <span className="stat-num">{pending.length}</span>
            <span className="stat-label">Pending cases</span>
          </div>
          <div className="stat card-3d">
            <span className="stat-num">{queue.length}</span>
            <span className="stat-label">In retraining queue</span>
          </div>
        </div>

        <section className="card card-3d">
          <div className="card-head">
            <h3>Pending New Cases</h3>
            <span className="card-sub">awaiting admin approval</span>
          </div>

          {loading && <p className="muted">Loading...</p>}
          {!loading && pending.length === 0 && (
            <p className="muted">No pending cases.</p>
          )}

          {pending.map((c) => (
            <div key={c.id} className="case-row">
              <img
                src={imageUrl(c.image)}
                alt="case"
                className="thumb"
                onError={(e) => { e.target.style.display = "none"; }}
              />
              <div className="case-meta">
                <span className="case-id">Case #{c.id}</span>
                <span className="case-label">{c.label}</span>
              </div>
              <button onClick={() => handleApprove(c.id)}>Approve</button>
            </div>
          ))}
        </section>

        <section className="card card-3d">
          <div className="card-head">
            <h3>Retraining Queue</h3>
            <span className="card-sub">manual trigger only</span>
          </div>
          <p className="muted">
            {queue.length} case(s) ready for retraining. The model does not
            retrain automatically — an administrator must trigger a training
            cycle offline.
          </p>
          <button
            className="trigger-btn"
            onClick={handleTrigger}
            disabled={queue.length === 0}
          >
            Trigger Retrain (manual)
          </button>
        </section>
      </main>
    </div>
  );
}