"""Главный класс для обучения и предсказания."""

from __future__ import annotations

import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from .data_preprocessor import DataPreprocessor
from .feature_engineering import FeatureEngineer
from .model import CoalFireModel
from .metrics import evaluate_model, print_metrics_report


class CoalCombustionPredictor:
    """Основной класс для работы с моделью прогнозирования самовозгорания."""
    
    def __init__(self, data_dir: str | Path, artifacts_dir: str | Path):
        """
        Инициализация предиктора.
        
        Args:
            data_dir: Папка с CSV файлами
            artifacts_dir: Папка для сохранения артефактов (модели, метрики)
        """
        self.data_dir = Path(data_dir)
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        self.preprocessor = DataPreprocessor(self.data_dir)
        self.feature_engineer = FeatureEngineer()
        self.model = CoalFireModel()
        
        self.model_path = self.artifacts_dir / "models" / "coal_fire_model.pkl"
        self.metrics_path = self.artifacts_dir / "training_metrics.json"
        self.history_path = self.artifacts_dir / "prediction_history.json"
        self.dataset_path = self.artifacts_dir / "datasets" / "training_dataset.parquet"
        
        # Загрузить модель если существует
        if self.model_path.exists():
            try:
                self.model.load(self.model_path)
                print(f"✓ Модель загружена из: {self.model_path}")
            except Exception as e:
                print(f"⚠️ Не удалось загрузить модель: {e}")
    
    def train(self) -> Dict[str, Any]:
        """
        Обучить модель на всех данных.
        
        Returns:
            Словарь с метриками обучения
        """
        print("\n" + "="*60)
        print("🔥 ОБУЧЕНИЕ МОДЕЛИ ПРОГНОЗИРОВАНИЯ САМОВОЗГОРАНИЯ УГЛЯ")
        print("="*60)
        
        # 1. Загрузка и подготовка данных
        df, y = self.preprocessor.prepare_training_data()
        
        # 2. Feature engineering
        df = self.feature_engineer.create_features(df)
        
        # 3. Выбрать нужные признаки
        feature_cols = self.feature_engineer.get_feature_columns()
        X = df[feature_cols].copy()
        
        # Заполнить оставшиеся NaN
        X = X.fillna(X.mean())
        
        print(f"\n📊 Финальный датасет:")
        print(f"  ✓ Признаков: {X.shape[1]}")
        print(f"  ✓ Примеров: {X.shape[0]}")
        print(f"  ✓ Target (y) min/max: {y.min():.0f} / {y.max():.0f} дней")
        
        # 4. Обучение модели
        metrics = self.model.train(X, y, cv_splits=5)
        
        # 5. Оценка на всех данных
        y_pred = self.model.predict(X)
        full_metrics = evaluate_model(y.values, y_pred)
        
        # Объединить метрики
        metrics.update(full_metrics)
        metrics['trained_at'] = datetime.now().isoformat()
        
        # 6. Feature importance
        importance_df = self.model.get_feature_importance(top_n=15)
        print(f"\n📊 ТОП-15 ВАЖНЫХ ПРИЗНАКОВ:")
        for idx, row in importance_df.iterrows():
            print(f"  {row['feature']:40s}: {row['importance']:.4f}")
        
        metrics['feature_importance'] = importance_df.to_dict('records')
        
        # 7. Сохранить модель и метрики
        self.model.save(self.model_path)
        self._save_metrics(metrics)
        
        # 8. Сохранить датасет
        self.dataset_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(self.dataset_path, index=False)
        print(f"✓ Датасет сохранен: {self.dataset_path}")
        
        # 9. Вывести отчет
        print_metrics_report(metrics)
        
        return metrics
    
    def predict(self, input_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Сделать предсказания для новых данных.
        
        Args:
            input_df: DataFrame с колонками:
                - storage_id: ID склада
                - stack_id: ID штабеля
                - measurement_date: дата измерения
                - max_temperature: максимальная температура
                - pile_age_days: возраст штабеля (опционально)
                - stack_mass_tons: масса штабеля (опционально)
                - weather_*: погодные данные (опционально)
                
        Returns:
            Список предсказаний с метаданными
        """
        if not self.model_path.exists():
            raise FileNotFoundError(
                "Модель не обучена. Сначала вызовите метод train()."
            )
        
        # Подготовить данные
        df = input_df.copy()
        
        # Маппинг названий колонок
        column_mapping = {
            'max_temperature': 'max_temp',
            'pile_age_days': 'days_since_formation',
            'stack_mass_tons': 'coal_weight'
        }
        df = df.rename(columns=column_mapping)
        
        # Заполнить missing значения разумными дефолтами
        if 'days_since_formation' not in df.columns:
            df['days_since_formation'] = 30  # Средний возраст
        if 'coal_weight' not in df.columns:
            df['coal_weight'] = 5000  # Средний вес
        
        # Feature engineering (упрощенный для инференса)
        df = self._prepare_inference_features(df)
        
        # Получить признаки для модели
        feature_cols = self.feature_engineer.get_feature_columns()
        
        # Добавить отсутствующие колонки с дефолтными значениями
        for col in feature_cols:
            if col not in df.columns:
                df[col] = 0
        
        X = df[feature_cols].fillna(0)
        
        # Предсказать
        predictions_with_conf = self.model.predict_with_confidence(X)
        
        # Сформировать результат
        results = []
        for idx, row in input_df.iterrows():
            pred_row = predictions_with_conf.iloc[idx]
            
            predicted_days = pred_row['predicted_days']
            confidence = pred_row['confidence']
            risk_level = pred_row['risk_level']
            
            # Вычислить дату возгорания
            measurement_date = pd.to_datetime(row['measurement_date'])
            predicted_date = measurement_date + timedelta(days=float(predicted_days))
            
            result = {
                'storage_id': str(row['storage_id']),
                'stack_id': str(row['stack_id']),
                'measurement_date': measurement_date.strftime('%Y-%m-%d %H:%M:%S'),
                'predicted_ttf_days': float(predicted_days),
                'predicted_combustion_date': predicted_date.strftime('%Y-%m-%d'),
                'confidence': float(confidence),
                'risk_level': str(risk_level),
                'max_temperature': float(row.get('max_temperature', 0))
            }
            
            results.append(result)
        
        # Сохранить в историю
        self._save_prediction_history(results)
        
        return results
    
    def _prepare_inference_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Подготовить признаки для инференса (без таргета)."""
        df = df.copy()
        
        # Базовые признаки
        if 'max_temp' not in df.columns and 'max_temperature' in df.columns:
            df['max_temp'] = df['max_temperature']
        
        # Временные признаки
        if 'measurement_date' in df.columns:
            df['measurement_date'] = pd.to_datetime(df['measurement_date'])
            df['month'] = df['measurement_date'].dt.month
            df['season'] = df['month'].map({
                12: 0, 1: 0, 2: 0,
                3: 1, 4: 1, 5: 1,
                6: 2, 7: 2, 8: 2,
                9: 3, 10: 3, 11: 3
            })
            df['day_of_week'] = df['measurement_date'].dt.dayofweek
        
        # Заполнить погодные данные средними если отсутствуют
        weather_defaults = {
            'weather_temp': 15.0,
            'weather_humidity': 60.0,
            'weather_precipitation': 0.0,
            'wind_speed_avg': 5.0,
            'wind_speed_max': 10.0,
            'weather_cloudcover': 50.0
        }
        
        for col, default_val in weather_defaults.items():
            if col not in df.columns:
                df[col] = default_val
        
        # Простые комбинированные признаки
        df['thermal_stress_index'] = (
            df['max_temp'] * 
            (1 - df['weather_humidity'] / 100) * 
            (1 + df['wind_speed_avg'] / 10)
        )
        
        df['temp_diff_internal_external'] = df['max_temp'] - df['weather_temp']
        
        df['dryness_index'] = (
            (100 - df['weather_humidity']) * 
            (1 / (df['weather_precipitation'] + 1))
        )
        
        df['oxidation_index'] = (
            df['max_temp'] + 
            df['wind_speed_avg'] * 5 - 
            df['weather_humidity'] * 0.5
        )
        
        # Категориальные
        df['coal_type_encoded'] = 0
        df['storage_id_encoded'] = pd.factorize(df['storage_id'])[0]
        
        # Индикаторы
        df['low_humidity_indicator'] = (df['weather_humidity'] < 50).astype(int)
        df['high_wind_indicator'] = (df['wind_speed_avg'] > 10).astype(int)
        df['high_temp_indicator'] = (df['max_temp'] > 40).astype(int)
        df['extreme_temp_indicator'] = (df['max_temp'] > 60).astype(int)
        
        # Для упрощения, rolling и lag features = 0 (в продакшене нужна история)
        rolling_features = [
            'temp_growth_rate', 'temp_rolling_3d_max', 'temp_rolling_3d_avg', 'temp_rolling_3d_std',
            'temp_rolling_7d_max', 'temp_rolling_7d_avg', 'temp_rolling_7d_std',
            'temp_rolling_14d_max', 'temp_rolling_14d_avg', 'temp_rolling_14d_std',
            'high_temp_days_7d', 'high_temp_days_14d', 'extreme_temp_days_7d'
        ]
        
        lag_features = [
            'max_temp_lag_1d', 'max_temp_lag_2d', 'max_temp_lag_3d', 
            'max_temp_lag_7d', 'max_temp_lag_14d',
            'weather_humidity_lag_1d', 'weather_humidity_lag_3d', 'weather_humidity_lag_7d',
            'wind_speed_avg_lag_1d', 'wind_speed_avg_lag_3d',
            'thermal_stress_index_lag_1d', 'thermal_stress_index_lag_3d', 'thermal_stress_index_lag_7d'
        ]
        
        for feat in rolling_features + lag_features:
            if feat not in df.columns:
                df[feat] = 0
        
        # Статистика по штабелю
        df['stack_max_temp_ever'] = df['max_temp']
        df['stack_avg_temp'] = df['max_temp']
        df['stack_measurement_count'] = 1
        
        return df
    
    def load_metrics(self) -> Dict[str, Any]:
        """Загрузить сохраненные метрики."""
        if not self.metrics_path.exists():
            return {}
        
        with open(self.metrics_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_metrics(self, metrics: Dict[str, Any]) -> None:
        """Сохранить метрики в JSON."""
        # Convert numpy types to Python types
        def convert_types(obj):
            import numpy as np
            if isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, dict):
                return {k: convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_types(item) for item in obj]
            return obj
        
        metrics = convert_types(metrics)
        
        with open(self.metrics_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Метрики сохранены: {self.metrics_path}")
    
    def _save_prediction_history(self, predictions: List[Dict[str, Any]]) -> None:
        """Сохранить историю предсказаний."""
        history = []
        
        if self.history_path.exists():
            with open(self.history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
        
        # Добавить timestamp
        for pred in predictions:
            pred['predicted_at'] = datetime.now().isoformat()
        
        history.extend(predictions)
        
        # Ограничить размер истории (последние 1000)
        history = history[-1000:]
        
        with open(self.history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)


__all__ = ["CoalCombustionPredictor"]

