"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { HealthResponse, StatsResponse } from "@/lib/types";
import { Activity, Database, Server, Cpu } from "lucide-react";

export default function SystemStatusBar() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [error, setError] = useState(false);

  const load = async () => {
    try {
      const [h, s] = await Promise.all([api.health(), api.stats()]);
      setHealth(h); setStats(s); setError(false);
    } catch { setError(true); }
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="card mb-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-2">
          <Activity size={18} className="text-blue-400" />
          <span className="font-semibold text-sm">System Status</span>
          {error && <span className="badge badge-red ml-2">API Unreachable</span>}
        </div>
        <div className="flex flex-wrap gap-6 text-sm">
          <Stat icon={<Server size={14} />} label="API" value={health?.status ?? "—"} ok={health?.status === "ok"} />
          <Stat icon={<Database size={14} />} label="Redis" value={health?.redis ?? "—"} ok={health?.redis === "ok"} />
          <Stat icon={<Database size={14} />} label="Offline Rows" value={stats?.offline_store_rows?.toLocaleString() ?? "—"} ok={true} />
          <Stat icon={<Cpu size={14} />} label="Features" value={stats?.registry_features?.toString() ?? "—"} ok={true} />
          <Stat icon={<Activity size={14} />} label="Retraining Runs" value={stats?.retraining_runs?.toString() ?? "—"} ok={true} />
        </div>
        <span className="text-xs" style={{ color: "var(--text-muted)" }}>Auto-refresh 30s</span>
      </div>
    </div>
  );
}

function Stat({ icon, label, value, ok }: {
  icon: React.ReactNode; label: string; value: string; ok: boolean;
}) {
  return (
    <div className="flex items-center gap-1.5">
      <span style={{ color: "var(--text-muted)" }}>{icon}</span>
      <span style={{ color: "var(--text-muted)" }}>{label}:</span>
      <span className="font-semibold"
        style={{ color: ok ? "var(--accent-green)" : "var(--accent-red)" }}>
        {value}
      </span>
    </div>
  );
}