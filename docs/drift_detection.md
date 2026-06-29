# Drift Detection — PSI and KS Test

## Why Drift Detection Matters

A model trained on historical data will degrade when the live data distribution
shifts. This is called data drift or covariate shift. Without drift detection,
model accuracy silently degrades and bad predictions reach production unnoticed.

This system detects drift continuously and triggers retraining automatically —
no human in the loop required.

## Two Metrics Used

### 1. Population Stability Index (PSI)

PSI measures how much a feature distribution has shifted between training
(reference) and live (current) data.

**Formula:**