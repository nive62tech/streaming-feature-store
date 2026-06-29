# Phase 8 — React Dashboard

## What Was Built
- Full Next.js 14 dashboard at http://localhost:3000
- Dark-themed ML infrastructure monitoring UI with 5 live panels
- All data fetched from FastAPI — auto-refreshes every 30 seconds

## Components

| Component | What It Shows |
|---|---|
| SystemStatusBar | API health, Redis status, offline store row count, feature count, retraining runs |
| DriftScoreTimeline | Max PSI and Avg PSI over time as line chart with threshold reference lines. Run Drift Check button. |
| FeatureDistributionChart | Per-feature PSI as bar chart. Click any feature to see PSI, PSI label, KS stat, KS p-value. |
| ModelVersionTable | All MLflow model versions with accuracy, train samples, registered time. Active model starred. |
| RetrainingHistoryLog | Full retraining event log with accuracy before/after, delta, status. Trigger Retraining button. |

## How to Start
- API: `uvicorn feature_store.serving.api:app --host 0.0.0.0 --port 8000 --reload`
- Dashboard: `cd dashboard && npm run dev`
- Open: http://localhost:3000

## Key Decisions
- All data fetched client-side — no Next.js server components needed
- Auto-refresh every 30 seconds on all components independently
- Drift check and retraining triggered from dashboard buttons — no CLI needed
- Dark theme with CSS variables — consistent color system across all components
- No heavy UI library — just Recharts for charts and Lucide for icons

## Files Created This Phase
- `dashboard/.env.local`
- `dashboard/lib/api.ts`
- `dashboard/lib/types.ts`
- `dashboard/app/globals.css`
- `dashboard/app/layout.tsx`
- `dashboard/app/page.tsx`
- `dashboard/components/SystemStatusBar.tsx`
- `dashboard/components/DriftScoreTimeline.tsx`
- `dashboard/components/FeatureDistributionChart.tsx`
- `dashboard/components/ModelVersionTable.tsx`
- `dashboard/components/RetrainingHistoryLog.tsx`