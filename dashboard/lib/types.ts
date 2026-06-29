export interface HealthResponse {
  status: string;
  timestamp: string;
  redis: string;
  offline_store_rows: number;
  registry_features: number;
}

export interface StatsResponse {
  offline_store_rows: number;
  registry_features: number;
  retraining_runs: number;
  timestamp: string;
}

export interface DriftReport {
  checked_at: string;
  window_minutes: number;
  n_samples: number;
  n_features_checked: number;
  n_features_drifted: number;
  max_psi: number;
  avg_psi: number;
  drift_detected: boolean;
  trigger_retraining: boolean;
  drifted_features?: string[];
  feature_results?: FeatureDriftResult[];
}

export interface FeatureDriftResult {
  feature: string;
  skipped: boolean;
  psi?: number;
  psi_label?: string;
  ks_statistic?: number;
  ks_p_value?: number;
  ks_drift_detected?: boolean;
  drift_detected?: boolean;
  current_mean?: number;
  current_std?: number;
}

export interface DriftHistoryRow {
  id: number;
  checked_at: string;
  n_samples: number;
  n_features_checked: number;
  n_features_drifted: number;
  max_psi: number;
  avg_psi: number;
  drift_detected: boolean;
  trigger_retraining: boolean;
}

export interface ModelVersion {
  run_id: string;
  version: string;
  accuracy: number;
  n_train: number;
  started_at: string;
  status: string;
}

export interface ActiveModel {
  version: string;
  run_id: string;
  accuracy: number;
  registered_at: string;
  artifact_dir: string;
}

export interface RetrainingEvent {
  id: number;
  triggered_at: string;
  trigger_reason: string;
  samples_used: number;
  accuracy_before: number;
  accuracy_after: number;
  model_version: string;
  status: string;
}