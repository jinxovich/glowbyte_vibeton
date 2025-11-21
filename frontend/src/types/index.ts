export type UploadDataset = "supplies" | "temperature" | "weather" | "fires" | "current";

export type PredictionPayload = {
  storage_id: string;
  stack_id: string;
  measurement_date: string;
  max_temperature: number;
  pile_age_days?: number | null;
  stack_mass_tons?: number | null;
  weather_temp?: number | null;
  weather_humidity?: number | null;
  weather_pressure?: number | null;
  weather_precipitation?: number | null;
  weather_wind_avg?: number | null;
  weather_cloudcover?: number | null;
};

export type PredictionResponse = {
  storage_id: string;
  stack_id: string;
  measurement_date: string;
  predicted_ttf_days: number;
  predicted_combustion_date: string;
};

export type MetricsSnapshot = {
  train_mae?: number;
  test_mae?: number;
  accuracy_within_2_days?: number;
  dataset_size?: number;
  generated_at?: string;
  [key: string]: unknown;
};

export type HistoryResponse = {
  metrics: MetricsSnapshot;
  predictions: PredictionResponse[];
};

export type TrainResponse = {
  status: "ok";
  metrics: MetricsSnapshot;
};

