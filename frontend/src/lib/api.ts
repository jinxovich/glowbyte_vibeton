import axios from "axios";
import type {
  HistoryResponse,
  PredictionPayload,
  PredictionResponse,
  TrainResponse,
  UploadDataset,
} from "../types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
});

export async function uploadDataset(dataset: UploadDataset, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post<{ stored_as: string }>(
    `/upload?dataset=${dataset}`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return response.data;
}

export async function trainModel(): Promise<TrainResponse> {
  const response = await api.post<TrainResponse>("/train", { force: true });
  return response.data;
}

export async function predictStacks(
  payload: PredictionPayload,
): Promise<PredictionResponse[]> {
  const response = await api.post<PredictionResponse[]>("/predict", {
    records: [payload],
  });
  return response.data;
}

export async function fetchHistory(): Promise<HistoryResponse> {
  const response = await api.get<HistoryResponse>("/history");
  return response.data;
}

