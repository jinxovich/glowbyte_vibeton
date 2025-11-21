"""Модуль подготовки данных и обучения модели для прогнозирования самовозгорания угольных штабелей."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
LOGGER = logging.getLogger("CoalCombustionPredictor")

RANDOM_STATE: int = 42
FEATURE_COLUMNS: list[str] = [
    "pile_age_days",
    "stack_mass_tons",
    "max_temperature",
    "rolling_temperature_mean_3",
    "rolling_temperature_std_3",
    "weather_temp",
    "weather_humidity",
    "weather_pressure",
    "weather_precipitation",
    "weather_wind_avg",
    "weather_cloudcover",
]


class CoalCombustionPredictor:
    """Класс, инкапсулирующий подготовку данных, обучение и инференс модели."""

    def __init__(self, data_dir: Path | str, artifacts_dir: Path | str) -> None:
        self.data_dir = Path(data_dir)
        self.artifacts_dir = Path(artifacts_dir)
        self.datasets_dir = self.artifacts_dir / "datasets"
        self.models_dir = self.artifacts_dir / "models"
        self.metrics_path = self.artifacts_dir / "training_metrics.json"
        self.dataset_path = self.datasets_dir / "training_dataset.parquet"
        self.model_path = self.models_dir / "coal_rf_model.pkl"
        self.history_path = self.artifacts_dir / "prediction_history.json"
        self.pipeline: Pipeline | None = None
        self._ensure_directories()

    # --------------------------------------------------------------------- #
    # --------------------------- Публичные методы ------------------------ #
    # --------------------------------------------------------------------- #

    def train(self) -> dict[str, Any]:
        """Готовит датасет, обучает модель и сохраняет артефакты."""
        dataset = self._prepare_training_frame()
        if dataset.empty:
            msg = "Не удалось построить обучающий датасет: нет наблюдений."
            LOGGER.error(msg)
            raise ValueError(msg)

        X = dataset[FEATURE_COLUMNS]
        y = dataset["ttf_days"]

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=RANDOM_STATE,
        )

        pipeline = self._build_pipeline()
        pipeline.fit(X_train, y_train)

        train_pred = pipeline.predict(X_train)
        test_pred = pipeline.predict(X_test)

        metrics = {
            "train_mae": float(mean_absolute_error(y_train, train_pred)),
            "test_mae": float(mean_absolute_error(y_test, test_pred)),
            "accuracy_within_2_days": float(
                np.mean(np.abs(test_pred - y_test) <= 2)
            ),
            "dataset_size": int(len(dataset)),
            "generated_at": datetime.utcnow().isoformat(),
        }

        joblib.dump(pipeline, self.model_path)
        dataset.to_parquet(self.dataset_path, index=False)
        self._save_metrics(metrics)
        self.pipeline = pipeline

        LOGGER.info(
            "Модель обучена. Test MAE=%.2f, точность ±2 дня=%.2f",
            metrics["test_mae"],
            metrics["accuracy_within_2_days"],
        )
        return metrics

    def predict(self, current_data: pd.DataFrame | Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        """Возвращает список прогнозов по входным данным."""
        frame = self.prepare_inference_frame(current_data)
        if frame.empty:
            return []

        pipeline = self._load_model()
        raw_predictions = pipeline.predict(frame[FEATURE_COLUMNS])

        results: list[dict[str, Any]] = []
        for record, prediction in zip(frame.to_dict(orient="records"), raw_predictions, strict=False):
            predicted_days = max(3.0, float(prediction))
            measurement_dt = pd.to_datetime(record["measurement_date"])
            combustion_date = measurement_dt + pd.to_timedelta(round(predicted_days), unit="D")

            result = {
                "storage_id": record.get("storage_id"),
                "stack_id": record.get("stack_id"),
                "measurement_date": measurement_dt.date().isoformat(),
                "predicted_ttf_days": round(predicted_days, 2),
                "predicted_combustion_date": combustion_date.date().isoformat(),
            }
            results.append(result)

        self._append_history(results)
        return results

    def prepare_inference_frame(
        self,
        current_data: pd.DataFrame | Iterable[dict[str, Any]],
    ) -> pd.DataFrame:
        """Преобразует произвольные данные в формат, совместимый с моделью."""
        if isinstance(current_data, pd.DataFrame):
            frame = current_data.copy()
        else:
            frame = pd.DataFrame(list(current_data))

        if frame.empty:
            return frame

        required_columns = {"stack_id", "storage_id", "measurement_date", "max_temperature"}
        missing = required_columns.difference(frame.columns)
        if missing:
            raise ValueError(f"Отсутствуют обязательные поля для инференса: {missing}")

        frame["stack_id"] = frame["stack_id"].astype(str)
        frame["storage_id"] = frame["storage_id"].astype(str)
        frame["measurement_date"] = pd.to_datetime(frame["measurement_date"])
        frame["measurement_date"] = self._strip_timezone(frame["measurement_date"])
        frame["max_temperature"] = pd.to_numeric(frame["max_temperature"], errors="coerce")
        if "pile_age_days" not in frame.columns:
            frame["pile_age_days"] = np.nan

        supplies = self._load_supplies()
        supplies_subset = supplies[
            ["stack_id", "storage_id", "supply_date", "stack_mass_tons"]
        ].rename(
            columns={
                "supply_date": "supply_date_source",
                "stack_mass_tons": "stack_mass_tons_source",
            }
        )
        frame = frame.merge(
            supplies_subset,
            on=["stack_id", "storage_id"],
            how="left",
        )
        if "supply_date_source" in frame.columns:
            frame["supply_date_source"] = self._strip_timezone(frame["supply_date_source"])
        if "supply_date_source" in frame.columns:
            derived_age = (frame["measurement_date"] - frame["supply_date_source"]).dt.days
            frame["pile_age_days"] = frame["pile_age_days"].fillna(derived_age)
        else:
            frame["pile_age_days"] = frame["pile_age_days"].fillna(np.nan)
        frame["pile_age_days"] = frame["pile_age_days"].clip(lower=0)
        frame = frame.drop(columns=["supply_date_source"], errors="ignore")

        if "stack_mass_tons" not in frame.columns:
            frame["stack_mass_tons"] = np.nan
        frame["stack_mass_tons"] = pd.to_numeric(frame["stack_mass_tons"], errors="coerce")

        if "stack_mass_tons_source" in frame.columns:
            frame["stack_mass_tons_source"] = pd.to_numeric(
                frame["stack_mass_tons_source"], errors="coerce"
            )
            frame["stack_mass_tons"] = frame["stack_mass_tons"].fillna(
                frame["stack_mass_tons_source"]
            )
            frame = frame.drop(columns=["stack_mass_tons_source"], errors="ignore")

        frame = self._compute_rolling_features(frame)

        for column in FEATURE_COLUMNS:
            if column not in frame.columns:
                frame[column] = np.nan

        return frame

    def load_metrics(self) -> dict[str, Any]:
        """Возвращает последние сохранённые метрики обучения."""
        if not self.metrics_path.exists():
            return {}
        return json.loads(self.metrics_path.read_text(encoding="utf-8"))

    # --------------------------------------------------------------------- #
    # ------------------------- Внутренние методы ------------------------- #
    # --------------------------------------------------------------------- #

    def _load_model(self) -> Pipeline:
        if self.pipeline is not None:
            return self.pipeline
        if not self.model_path.exists():
            msg = "Не найден сохранённый артефакт модели. Сначала вызовите train()."
            LOGGER.error(msg)
            raise FileNotFoundError(msg)
        self.pipeline = joblib.load(self.model_path)
        return self.pipeline

    def _prepare_training_frame(self) -> pd.DataFrame:
        supplies = self._load_supplies()
        temperature = self._load_temperature()
        weather = self._load_weather()
        fires = self._load_fires()

        supplies_subset = supplies[
            ["stack_id", "storage_id", "supply_date", "stack_mass_tons"]
        ].rename(
            columns={
                "supply_date": "supply_date_source",
                "stack_mass_tons": "stack_mass_tons_source",
            }
        )

        base = temperature.merge(
            supplies_subset,
            on=["stack_id", "storage_id"],
            how="left",
        )
        base["pile_age_days"] = (
            base["measurement_date"] - base["supply_date_source"]
        ).dt.days
        base["pile_age_days"] = base["pile_age_days"].clip(lower=0)
        if "stack_mass_tons_source" in base.columns:
            base["stack_mass_tons"] = base["stack_mass_tons_source"]
        base = base.drop(columns=["stack_mass_tons_source", "supply_date_source"], errors="ignore")
        base["measurement_day"] = base["measurement_date"].dt.date

        base = base.merge(
            weather,
            left_on="measurement_day",
            right_on="weather_date",
            how="left",
        )

        base = base.merge(fires, on=["stack_id", "storage_id"], how="left")
        base["ttf_days"] = (
            base["fire_start"] - base["measurement_date"]
        ).dt.days

        base = base[base["ttf_days"].notna()]
        base = base[base["ttf_days"] >= 0]

        base = self._compute_rolling_features(base)
        base = base.drop(columns=["measurement_day", "weather_date", "fire_start"], errors="ignore")
        base = base.dropna(subset=["ttf_days"])

        base = base.reset_index(drop=True)
        return base

    def _load_supplies(self) -> pd.DataFrame:
        path = self.data_dir / "supplies.csv"
        df = pd.read_csv(
            path,
            parse_dates=["ВыгрузкаНаСклад", "ПогрузкаНаСудно"],
        )
        df = df.rename(
            columns={
                "ВыгрузкаНаСклад": "supply_date",
                "ПогрузкаНаСудно": "shipment_date",
                "Штабель": "stack_id",
                "Склад": "storage_id",
                "На склад, тн": "stack_mass_tons",
                "На судно, тн": "shipped_mass_tons",
                "Наим. ЕТСНГ": "cargo_type",
            }
        )
        df["stack_id"] = df["stack_id"].astype(str)
        df["storage_id"] = df["storage_id"].astype(str)
        df["stack_mass_tons"] = pd.to_numeric(df["stack_mass_tons"], errors="coerce")
        df = (
            df.sort_values("supply_date")
            .groupby(["storage_id", "stack_id"], as_index=False)
            .last()
        )
        return df

    def _load_temperature(self) -> pd.DataFrame:
        path = self.data_dir / "temperature.csv"
        df = pd.read_csv(path, parse_dates=["Дата акта"])
        df = df.rename(
            columns={
                "Склад": "storage_id",
                "Штабель": "stack_id",
                "Марка": "grade",
                "Максимальная температура": "max_temperature",
                "Дата акта": "measurement_date",
            }
        )
        df["stack_id"] = df["stack_id"].astype(str)
        df["storage_id"] = df["storage_id"].astype(str)
        df["max_temperature"] = pd.to_numeric(df["max_temperature"], errors="coerce")
        df = df.sort_values("measurement_date")
        return df

    def _load_weather(self) -> pd.DataFrame:
        frames: list[pd.DataFrame] = []
        for file_path in sorted(self.data_dir.glob("weather_data_*.csv")):
            item = pd.read_csv(file_path, parse_dates=["date"])
            frames.append(item)
        if not frames:
            raise FileNotFoundError("Не найдены файлы weather_data_*.csv")
        df = pd.concat(frames, ignore_index=True)
        for column in ["t", "p", "humidity", "precipitation", "v_avg", "cloudcover"]:
            if column in df.columns:
                df[column] = pd.to_numeric(df[column], errors="coerce")
        df["weather_date"] = pd.to_datetime(df["date"]).dt.date
        aggregated = (
            df.groupby("weather_date")
            .agg(
                weather_temp=("t", "mean"),
                weather_pressure=("p", "mean"),
                weather_humidity=("humidity", "mean"),
                weather_precipitation=("precipitation", "mean"),
                weather_wind_avg=("v_avg", "mean"),
                weather_cloudcover=("cloudcover", "mean"),
            )
            .reset_index()
        )
        return aggregated

    def _load_fires(self) -> pd.DataFrame:
        path = self.data_dir / "fires.csv"
        df = pd.read_csv(
            path,
            parse_dates=["Дата начала"],
        )
        df = df.rename(
            columns={
                "Склад": "storage_id",
                "Штабель": "stack_id",
                "Дата начала": "fire_start",
            }
        )
        df["stack_id"] = df["stack_id"].astype(str)
        df["storage_id"] = df["storage_id"].astype(str)
        df = (
            df.sort_values("fire_start")
            .groupby(["storage_id", "stack_id"], as_index=False)
            .first()
        )
        return df[["storage_id", "stack_id", "fire_start"]]

    def _compute_rolling_features(self, frame: pd.DataFrame) -> pd.DataFrame:
        sorted_frame = frame.sort_values(["stack_id", "measurement_date"])
        grouped = sorted_frame.groupby("stack_id")["max_temperature"]
        sorted_frame["rolling_temperature_mean_3"] = grouped.transform(
            lambda s: s.rolling(window=3, min_periods=1).mean()
        )
        sorted_frame["rolling_temperature_std_3"] = grouped.transform(
            lambda s: s.rolling(window=3, min_periods=1).std().fillna(0.0)
        )
        return sorted_frame

    def _build_pipeline(self) -> Pipeline:
        numeric_processor = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
            ]
        )
        transformer = ColumnTransformer(
            transformers=[("numeric", numeric_processor, FEATURE_COLUMNS)],
            remainder="drop",
        )
        model = RandomForestRegressor(
            n_estimators=300,
            max_depth=10,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )
        return Pipeline(
            steps=[
                ("transformer", transformer),
                ("model", model),
            ]
        )

    def _ensure_directories(self) -> None:
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def _save_metrics(self, metrics: dict[str, Any]) -> None:
        self.metrics_path.write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _append_history(self, rows: list[dict[str, Any]]) -> None:
        history: list[dict[str, Any]] = []
        if self.history_path.exists():
            history = json.loads(self.history_path.read_text(encoding="utf-8"))
        history.extend(rows)
        self.history_path.write_text(
            json.dumps(history[-500:], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _strip_timezone(series: pd.Series) -> pd.Series:
        """Удаляет информацию о временной зоне, если она присутствует."""
        if pd.api.types.is_datetime64tz_dtype(series):
            return series.dt.tz_localize(None)
        return series


def main() -> None:
    """CLI-точка входа для быстрого обучения модели из каталога data/."""
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"
    artifacts_dir = Path(__file__).resolve().parent / "artifacts"
    predictor = CoalCombustionPredictor(data_dir=data_dir, artifacts_dir=artifacts_dir)
    metrics = predictor.train()
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

