"use client";
import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, Legend, ResponsiveContainer,
} from "recharts";
import { api } from "@/lib/api";
import { DriftHistoryRow } from "@/lib/types";
import { TrendingUp, RefreshCw } from "lucide-react";

export default function DriftScoreTimeline() {
  const [history, setHistory] = useState<DriftHistoryRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [triggering, setTriggering] = useState(false);
  const [msg, setMsg] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.driftHistory(30);
      setHistory([...data.history].reverse());
    } catch { setHistory([]); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, []);

  const triggerCheck = async () => {
    setTriggering(true); setMsg("");
    try {
      const r = await api.triggerDriftCheck();
      setMsg(
        `Check complete — max_psi=${r.max_psi?.toFixed(4)}, ` +
        `drifted=${r.n_features_drifted}/${r.n_features_checked}`
      );
      await load();
    } catch (e: unknown) {
      setMsg(`Error: ${e instanceof Error ? e.message : "unknown"}`);
    } finally { setTriggering(false); }
  };

  const chartData = history.map((r) => ({
    time: new Date(r.checked_at).toLocaleTimeString(),
    max_psi: Number(r.max_psi?.toFixed(4)),
    avg_psi: Number(r.avg_psi?.toFixed(4)),
  }));

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <TrendingUp size={18} className="text-purple-400" />
          <span className="font-semibold">Drift Score Timeline</span>
          {loading && <span className="text-xs" style={{ color: "var(--text-muted)" }}>loading...</span>}
        </div>
        <button onClick={triggerCheck} disabled={triggering}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold"
          style={{
            background: "rgba(168,85,247,0.15)", color: "#a855f7",
            border: "1px solid rgba(168,85,247,0.3)",
            cursor: triggering ? "not-allowed" : "pointer",
          }}>
          <RefreshCw size={12} className={triggering ? "animate-spin" : ""} />
          {triggering ? "Running..." : "Run Drift Check"}
        </button>
      </div>
      {msg && (
        <p className="text-xs mb-3 px-3 py-2 rounded-lg"
          style={{ background: "rgba(168,85,247,0.1)", color: "#a855f7" }}>
          {msg}
        </p>
      )}
      {chartData.length === 0
        ? <EmptyState text="No drift checks yet. Run a check or start the scheduler." />
        : (
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3e" />
              <XAxis dataKey="time" tick={{ fill: "#64748b", fontSize: 11 }} />
              <YAxis tick={{ fill: "#64748b", fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: "#1a1d27", border: "1px solid #2a2d3e" }}
                labelStyle={{ color: "#e2e8f0" }} />
              <Legend />
              <ReferenceLine y={0.2} stroke="#ef4444" strokeDasharray="4 4"
                label={{ value: "Threshold 0.2", fill: "#ef4444", fontSize: 10 }} />
              <ReferenceLine y={0.1} stroke="#eab308" strokeDasharray="4 4"
                label={{ value: "Moderate 0.1", fill: "#eab308", fontSize: 10 }} />
              <Line type="monotone" dataKey="max_psi" name="Max PSI"
                stroke="#a855f7" strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="avg_psi" name="Avg PSI"
                stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        )}
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="flex items-center justify-center h-40"
      style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
      {text}
    </div>
  );
}