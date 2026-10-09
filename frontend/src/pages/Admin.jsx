import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  listPendingCases,
  approveCase,
  getRetrainingQueue,
  triggerRetrain,
} from "../api/endpoints";
import Logo from "../components/Logo";

export default function Admin() {
  const [pending, setPending] = useState([]);
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(false);

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
    refresh();
  };

  const handleTrigger = async () => {
    const r = await triggerRetrain();
    alert(`Ready for retrain: ${r.data.ready_for_retrain}`);
  };

  return (
    <div className="page">
      <header className="topbar">
        <h1 className="brand">
          <Logo size={34} />
          <span>Admin Panel</span>
        </h1>
        <Link to="/predict" className="link-btn">Back</Link>
      </header>

      <main className="admin-layout">
        <div className="stats">
          <div className="stat">
            <span className="stat-num">{pending.length}</span>
            <span className="stat-label">Pending cases</span>
          </div>
          <div className="stat">
            <span className="stat-num">{queue.length}</span>
            <span className="stat-label">In retraining queue</span>
          </div>
        </div>

        <section className="card">
          <h2>Pending New Cases</h2>
          {loading && <p>Loading...</p>}
          {pending.length === 0 && <p>No pending cases.</p>}
          {pending.map((c) => (
            <div key={c.id} className="case-row">
              <img
                src={`http://127.0.0.1:8000/uploads/${c.image.split(/[\\/]/).pop()}`}
                alt="case"
                className="thumb"
                onError={(e) => { e.target.style.display = "none"; }}
              />
              <span className="case-id">Case #{c.id}</span>
              <span className="case-label">{c.label}</span>
              <button onClick={() => handleApprove(c.id)}>Approve</button>
            </div>
          ))}
        </section>

        <section className="card">
          <h2>Retraining Queue</h2>
          <p>{queue.length} case(s) ready for retraining.</p>
          <button onClick={handleTrigger}>Trigger Retrain (manual)</button>
        </section>
      </main>
    </div>
  );
}