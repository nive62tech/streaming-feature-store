"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { RetrainingEvent } from "@/lib/types";
import { RefreshCw, Zap } from "lucide-react";

export default function RetrainingHistoryLog() {
  const [history, setHistory] = useState<RetrainingEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [triggering, setTriggering] = useState(false);
  const [msg, setMsg] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.retrainingHistory();
      setHistory(data.history ?? []);
    } catch { setHistory([]); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, []);

  const triggerRetrain = async () => {
    setTriggering(true); setMsg("");
    try {
      const r = await api.triggerRetraining(true);
      if (r.status === "success") {
        setMsg(
          `Retraining complete — ${r.version} | ` +
          `accuracy: ${(r.accuracy_after * 100).toFixed(1)}% ` +
          `(delta: ${r.accuracy_delta > 0 ? "+" : ""}${(r.accuracy_delta * 100).toFixed(1)}%)`
        );
      } else {
        setMsg(`Status: ${r.status} — ${r.reason ?? r.error ?? ""}`);
      }
      await load();
    } catch (e: unknown) {
      setMsg(`Error: ${e instanceof Error ? e.message : "unknown"}`);
    } finally { setTriggering(false); }
  };

  const statusBadge = (status: string) => {
    if (status === "success") return "badge-green";
    if (status === "failed") return "badge-red";
    if (status === "rejected") return "badge-yellow";
    return "badge-gray";
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Zap size={18} className="text-yellow-400" />
          <span className="font-semibold">Retraining History</span>
          {loading && <span className="text-xs" style={{ color: "var(--text-muted)" }}>loading...</span>}
        </div>
        <button onClick={triggerRetrain} disabled={triggering}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold"
          style={{
            background: "rgba(234,179,8,0.15)", color: "#eab308",
            border: "1px solid rgba(234,179,8,0.3)",
            cursor: triggering ? "not-allowed" : "pointer",
          }}>
          <RefreshCw size={12} className={triggering ? "animate-spin" : ""} />
          {triggering ? "Retraining..." : "Trigger Retraining"}
        </button>
      </div>
      {msg && (
        <p className="text-xs mb-3 px-3 py-2 rounded-lg"
          style={{ background: "rgba(234,179,8,0.1)", color: "#eab308" }}>
          {msg}
        </p>
      )}
      {history.length === 0
        ? (
          <div className="flex items-center justify-center h-24"
            style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
            No retraining events yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: "1px solid #2a2d3e" }}>
                  {["Time", "Reason", "Samples", "Acc Before", "Acc After", "Delta", "Status"].map((h) => (
                    <th key={h} className="text-left pb-2 pr-3 text-xs font-semibold"
                      style={{ color: "var(--text-muted)" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {history.map((e) => {
                  const delta = (e.accuracy_after ?? 0) - (e.accuracy_before ?? 0);
                  return (
                    <tr key={e.id} style={{ borderBottom: "1px solid #1e2130" }}
                      className="hover:bg-white hover:bg-opacity-5 transition-colors">
                      <td className="py-2 pr-3 text-xs" style={{ color: "var(--text-muted)" }}>
                        {new Date(e.triggered_at).toLocaleString()}
                      </td>
                      <td className="py-2 pr-3 text-xs max-w-32 truncate"
                        style={{ color: "var(--text-muted)" }}>
                        {e.trigger_reason ?? "—"}
                      </td>
                      <td className="py-2 pr-3 text-xs">
                        {e.samples_used?.toLocaleString() ?? "—"}
                      </td>
                      <td className="py-2 pr-3 text-xs">
                        {e.accuracy_before != null ? `${(e.accuracy_before * 100).toFixed(1)}%` : "—"}
                      </td>
                      <td className="py-2 pr-3 text-xs font-semibold" style={{ color: "#22c55e" }}>
                        {e.accuracy_after != null ? `${(e.accuracy_after * 100).toFixed(1)}%` : "—"}
                      </td>
                      <td className="py-2 pr-3 text-xs font-semibold"
                        style={{ color: delta >= 0 ? "#22c55e" : "#ef4444" }}>
                        {delta !== 0 ? `${delta >= 0 ? "+" : ""}${(delta * 100).toFixed(1)}%` : "—"}
                      </td>
                      <td className="py-2">
                        <span className={`badge ${statusBadge(e.status)}`}>{e.status}</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
    </div>
  );
}