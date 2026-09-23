import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  listPendingCases,
  approveCase,
  getRetrainingQueue,
  triggerRetrain,
} from "../api/endpoints";

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
        <h1>Admin Panel</h1>
        <Link to="/predict" className="link-btn">Back</Link>
      </header>

      <main className="admin-layout">
        <section className="card">
          <h2>Pending New Cases</h2>
          {loading && <p>Loading...</p>}
          {pending.length === 0 && <p>No pending cases.</p>}
          {pending.map((c) => (
            <div key={c.id} className="case-row">
              <span>Case #{c.id}</span>
              <span>{c.label}</span>
              <img
                src={`http://127.0.0.1:8000/uploads/${c.image.split(/[\\/]/).pop()}`}
                alt="case"
                className="thumb"
                onError={(e) => { e.target.style.display = "none"; }}
              />
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