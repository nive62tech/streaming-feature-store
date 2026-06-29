"use client";
import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from "recharts";
import { api } from "@/lib/api";
import { FeatureDriftResult } from "@/lib/types";
import { BarChart2 } from "lucide-react";

export default function FeatureDistributionChart() {
  const [results, setResults] = useState<FeatureDriftResult[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const latest = await api.driftLatest();
      const featureResults: FeatureDriftResult[] =
        latest?.feature_results?.filter((r: FeatureDriftResult) => !r.skipped) ?? [];
      setResults(featureResults);
      if (featureResults.length > 0 && !selected) setSelected(featureResults[0].feature);
    } catch { setResults([]); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, []);

  const chartData = results.map((r) => ({
    feature: r.feature.replace(/_/g, " "),
    psi: Number(r.psi?.toFixed(4) ?? 0),
  }));

  const selectedResult = results.find((r) => r.feature === selected);

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <BarChart2 size={18} className="text-blue-400" />
        <span className="font-semibold">Feature Drift — PSI per Feature</span>
        {loading && <span className="text-xs" style={{ color: "var(--text-muted)" }}>loading...</span>}
      </div>
      {chartData.length === 0
        ? (
          <div className="flex items-center justify-center h-40"
            style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
            No drift data yet. Run a drift check first.
          </div>
        ) : (
          <>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={chartData} margin={{ bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3e" />
                <XAxis dataKey="feature" tick={{ fill: "#64748b", fontSize: 9 }}
                  angle={-45} textAnchor="end" interval={0} />
                <YAxis tick={{ fill: "#64748b", fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ background: "#1a1d27", border: "1px solid #2a2d3e" }}
                  labelStyle={{ color: "#e2e8f0" }} />
                <Bar dataKey="psi" name="PSI" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <div className="mt-4">
              <p className="text-xs mb-2" style={{ color: "var(--text-muted)" }}>
                Select feature for details:
              </p>
              <div className="flex flex-wrap gap-2">
                {results.slice(0, 9).map((r) => (
                  <button key={r.feature} onClick={() => setSelected(r.feature)}
                    className="px-2 py-1 rounded text-xs font-medium"
                    style={{
                      background: selected === r.feature ? "rgba(59,130,246,0.2)" : "rgba(255,255,255,0.05)",
                      border: selected === r.feature ? "1px solid #3b82f6" : "1px solid #2a2d3e",
                      color: r.drift_detected ? "#ef4444" : "#94a3b8",
                      cursor: "pointer",
                    }}>
                    {r.feature.replace("event_count_", "cnt_").replace("_price_", "_p_")}
                  </button>
                ))}
              </div>
              {selectedResult && (
                <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
                  {[
                    { label: "PSI", value: selectedResult.psi?.toFixed(4) },
                    { label: "PSI Label", value: selectedResult.psi_label },
                    { label: "KS Stat", value: selectedResult.ks_statistic?.toFixed(4) },
                    { label: "KS p-value", value: selectedResult.ks_p_value?.toFixed(4) },
                  ].map(({ label, value }) => (
                    <div key={label} className="rounded-lg p-2 text-center"
                      style={{ background: "rgba(255,255,255,0.03)", border: "1px solid #2a2d3e" }}>
                      <p className="text-xs" style={{ color: "var(--text-muted)" }}>{label}</p>
                      <p className="text-sm font-semibold mt-0.5">{value ?? "—"}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
    </div>
  );
}