import SystemStatusBar from "@/components/SystemStatusBar";
import DriftScoreTimeline from "@/components/DriftScoreTimeline";
import FeatureDistributionChart from "@/components/FeatureDistributionChart";
import ModelVersionTable from "@/components/ModelVersionTable";
import RetrainingHistoryLog from "@/components/RetrainingHistoryLog";

export default function Home() {
  return (
    <main style={{ maxWidth: 1280, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <div className="mb-8">
        <h1 className="text-2xl font-bold mb-1">Streaming Feature Store</h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
          Real-time ML infrastructure — Kafka → Feature Computation →
          Drift Detection → Auto-Retraining
        </p>
      </div>
      <SystemStatusBar />
      <div className="grid grid-cols-1 gap-6 mb-6 lg:grid-cols-2">
        <DriftScoreTimeline />
        <FeatureDistributionChart />
      </div>
      <div className="mb-6">
        <ModelVersionTable />
      </div>
      <div className="mb-6">
        <RetrainingHistoryLog />
      </div>
      <div className="text-center py-4 text-xs"
        style={{ color: "var(--text-muted)", borderTop: "1px solid #2a2d3e" }}>
        Streaming Feature Store — built with Kafka · Redis · FastAPI · Next.js
      </div>
    </main>
  );
}