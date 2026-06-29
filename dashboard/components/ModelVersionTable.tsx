"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ModelVersion, ActiveModel } from "@/lib/types";
import { Cpu, Star } from "lucide-react";

export default function ModelVersionTable() {
  const [versions, setVersions] = useState<ModelVersion[]>([]);
  const [active, setActive] = useState<ActiveModel | null>(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [v, a] = await Promise.all([api.modelVersions(), api.activeModel()]);
      setVersions(v.versions ?? []); setActive(a);
    } catch { setVersions([]); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <Cpu size={18} className="text-green-400" />
        <span className="font-semibold">Model Versions</span>
        {loading && <span className="text-xs" style={{ color: "var(--text-muted)" }}>loading...</span>}
        {active && (
          <span className="badge badge-green ml-auto">
            Active: {active.version.slice(0, 20)}...
          </span>
        )}
      </div>
      {versions.length === 0
        ? (
          <div className="flex items-center justify-center h-24"
            style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
            No model versions found.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: "1px solid #2a2d3e" }}>
                  {["Version", "Accuracy", "Train Samples", "Registered", "Status"].map((h) => (
                    <th key={h} className="text-left pb-2 pr-4 text-xs font-semibold"
                      style={{ color: "var(--text-muted)" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {versions.map((v) => {
                  const isActive = active?.version === v.version;
                  return (
                    <tr key={v.run_id} style={{ borderBottom: "1px solid #1e2130" }}
                      className="hover:bg-white hover:bg-opacity-5 transition-colors">
                      <td className="py-2 pr-4 font-mono text-xs">
                        <div className="flex items-center gap-1">
                          {isActive && <Star size={12} className="text-yellow-400" />}
                          {v.version.slice(0, 24)}
                        </div>
                      </td>
                      <td className="py-2 pr-4">
                        <span className="font-semibold"
                          style={{ color: v.accuracy > 0.7 ? "#22c55e" : "#eab308" }}>
                          {(v.accuracy * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-2 pr-4 text-xs" style={{ color: "var(--text-muted)" }}>
                        {v.n_train?.toLocaleString()}
                      </td>
                      <td className="py-2 pr-4 text-xs" style={{ color: "var(--text-muted)" }}>
                        {new Date(v.started_at).toLocaleString()}
                      </td>
                      <td className="py-2">
                        <span className={`badge ${isActive ? "badge-green" : "badge-gray"}`}>
                          {isActive ? "active" : v.status.toLowerCase()}
                        </span>
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