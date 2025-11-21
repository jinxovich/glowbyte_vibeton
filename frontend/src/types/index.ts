export interface PredictionRequest {
  storage_id: string;
  stack_id: string;
  measurement_date: string;
  max_temperature: number;
  pile_age_days?: number;
  stack_mass_tons?: number;
  weather_humidity?: number;
  weather_temp?: number;
}

export interface PredictionResponse {
  storage_id: string;
  stack_id: string;
  measurement_date: string;
  predicted_ttf_days: number;
  predicted_combustion_date: string;
  confidence: number;
  risk_level: RiskLevel;
  max_temperature: number;
}

export type RiskLevel = 'критический' | 'высокий' | 'средний' | 'низкий' | 'минимальный';

export interface Metrics {
  accuracy_2days: number;
  mae: number;
  rmse: number;
  kpi_achieved: boolean;
  total_predictions?: number;
  trained_at?: string;
}

export interface DashboardData {
  metrics: Metrics;
  statistics: {
    total_predictions: number;
    risk_distribution: Record<RiskLevel, number>;
    storages: Record<string, number>;
    at_risk_count: number;
  };
  upcoming_fires: UpcomingFire[];
  trained_at?: string;
}

export interface UpcomingFire {
  storage_id: string;
  stack_id: string;
  date: string;
  days_until: number;
  risk_level: RiskLevel;
  confidence: number;
}

export interface CalendarItem {
  date: string;
  count: number;
  risk_level: RiskLevel;
  stockpiles: Array<{
    storage_id: string;
    stack_id: string;
    confidence: number;
  }>;
}

export interface HealthResponse {
  status: string;
  model_loaded: boolean;
  model_path: string;
  data_dir: string;
}

