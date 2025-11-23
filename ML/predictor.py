"""Главный класс для обучения и предсказания (v3.0 - Full Data Training)."""

from __future__ import annotations

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List

# Импорты из соседних модулей
from .data_preprocessor import DataPreprocessor
from .feature_engineering import FeatureEngineer
from .model import CoalFireModel
from .metrics import evaluate_model, print_metrics_report
from sklearn.model_selection import TimeSeriesSplit

class CoalCombustionPredictor:
    """
    Orchestrator: Data -> Features -> Model -> Predictions.
    Обучается на 100% доступных данных.
    """
    
    def __init__(self, data_dir: str | Path, artifacts_dir: str | Path):
        self.data_dir = Path(data_dir)
        self.artifacts_dir = Path(artifacts_dir)
        
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        (self.artifacts_dir / "models").mkdir(parents=True, exist_ok=True)
        
        self.preprocessor = DataPreprocessor(self.data_dir)
        self.feature_engineer = FeatureEngineer()
        self.model = CoalFireModel()
        
        self.model_path = self.artifacts_dir / "models" / "coal_fire_model.pkl"
        self.metrics_path = self.artifacts_dir / "training_metrics.json"
        
        if self.model_path.exists():
            try:
                self.model.load(self.model_path)
            except Exception as e:
                print(f"⚠️ Ошибка загрузки модели: {e}")
    
    def train(self) -> Dict[str, Any]:
        """
        Обучение на ПОЛНОМ датасете без потери 20% данных.
        """
        print("\n" + "="*60)
        print("🔥 ЗАПУСК ОБУЧЕНИЯ НА 100% ДАННЫХ")
        print("="*60)
        
        # 1. Загрузка
        raw_df = self.preprocessor.prepare_full_dataset()
        if raw_df.empty: raise ValueError("❌ Датасет пуст!")

        # 2. Фичи
        full_df = self.feature_engineer.create_features(raw_df)
        
        # 3. Фильтрация (0-60 дней до пожара)
        print("\n🔪 Фильтрация выборки (0 <= дней до пожара <= 60)...")
        df_model = full_df[
            (full_df['days_until_fire'] >= 0) & 
            (full_df['days_until_fire'] <= 60)
        ].copy()
        
        # Сортировка по времени обязательна
        df_model = df_model.sort_values('measurement_date')
        
        if len(df_model) < 10: raise ValueError("❌ Критически мало данных (<10).")
            
        # 4. Подготовка X и y (ВСЕ ДАННЫЕ)
        feature_cols = self.feature_engineer.get_feature_columns()
        for c in feature_cols:
            if c not in df_model.columns: df_model[c] = 0

        X = df_model[feature_cols].fillna(0)
        y = df_model['days_until_fire']
        
        print(f"  🚀 Используем все данные для обучения: {len(X)} строк")
        print(f"  📅 Период: {df_model['measurement_date'].min().date()} -> {df_model['measurement_date'].max().date()}")

        # 5. Оптимизация (Optuna) на всем датасете
        # Внутри Optuna используется Cross-Validation, так что переобучения на подборе параметров не будет
        if hasattr(self.model, 'optimize'):
                    try:
                        print("\n⚙️  Подбор параметров (Optuna) - БЫСТРЫЙ РЕЖИМ...")
                        # СТАВИМ 5 ВМЕСТО 20
                        self.model.optimize(X, y, n_trials=5) 
                    except Exception as e:
                        print(f"⚠️ Ошибка Optuna: {e}")

        # 6. ФИНАЛЬНОЕ ОБУЧЕНИЕ (FIT) НА 100% ДАННЫХ
        print("\n💪 Финальное обучение модели на полном объеме...")
        self.model.train_final(X, y)
        
        # 7. Оценка (Self-Check)
        # Так как мы обучились на всем, смотрим метрики на том же train-сете.
        # Это покажет, насколько хорошо модель "выучила уроки".
        print("\n📊 МЕТРИКИ (TRAINING SCORE - Насколько хорошо модель запомнила данные):")
        y_pred = self.model.predict(X)
        metrics = evaluate_model(y.values, y_pred)
        
        print_metrics_report(metrics)
        
        # 8. Попытка достать важность признаков
        print("\n🔍 ТОП-10 ПРИЗНАКОВ (Feature Importance):")
        try:
            # Пытаемся достать из XGBoost напрямую
            booster = self.model.model
            if hasattr(booster, 'feature_importances_'):
                imps = booster.feature_importances_
                feats = feature_cols
                fi_df = pd.DataFrame({'feature': feats, 'importance': imps})
                print(fi_df.sort_values('importance', ascending=False).head(10).to_string(index=False))
            else:
                print("  (Не поддерживается текущей версией модели)")
        except Exception as e:
            print(f"  (Ошибка получения важности: {e})")

        # 9. Сохранение
        print(f"\n💾 Сохранение модели в {self.model_path}...")
        self.model.save(self.model_path)
        self._save_metrics(metrics)
        
        return metrics
    
    def predict(self, input_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Инференс."""
        if not self.model_path.exists(): raise FileNotFoundError("❌ Модель не обучена!")
        df = input_df.copy()
        
        rename_map = {'max_temperature': 'max_temp', 'pile_age_days': 'days_since_formation', 'stack_mass_tons': 'coal_weight'}
        df = df.rename(columns=rename_map)
        
        # Заглушки для отсутствующих данных
        defaults = {'days_since_formation': 0, 'weather_temp': 10, 'weather_humidity': 70, 'wind_speed_avg': 3, 'coal_weight': 5000}
        for c, v in defaults.items():
            if c not in df.columns: df[c] = v
            
        df_features = self.feature_engineer.create_features(df)
        feature_cols = self.feature_engineer.get_feature_columns()
        for c in feature_cols:
            if c not in df_features.columns: df_features[c] = 0
            
        X = df_features[feature_cols].fillna(0)
        preds_df = self.predict_with_confidence(X)
        
        results = []
        for i, row in df.iterrows():
            results.append({
                'storage_id': str(row.get('storage_id', 'unknown')),
                'stack_id': str(row.get('stack_id', 'unknown')),
                'predicted_ttf_days': float(preds_df.iloc[i]['predicted_days']),
                'risk_level': str(preds_df.iloc[i]['risk_level']),
                'confidence': float(preds_df.iloc[i]['confidence'])
            })
        return results

    def predict_with_confidence(self, X: pd.DataFrame) -> pd.DataFrame:
        predictions = self.model.predict(X)
        predictions = np.maximum(predictions, 0)
        
        # Расчет уверенности от температуры (физика)
        if 'max_temp' in X.columns:
            temps = X['max_temp'].reset_index(drop=True)
            confidence = 1 / (1 + np.exp(-(temps - 45) / 10))
            confidence = 0.4 + (confidence * 0.55)
        else:
            confidence = pd.Series([0.7] * len(predictions))
            
        risk_level = pd.cut(
            predictions,
            bins=[-1, 7, 14, 30, 60, 10000],
            labels=['критический', 'высокий', 'средний', 'низкий', 'минимальный']
        )
        return pd.DataFrame({'predicted_days': predictions, 'confidence': confidence, 'risk_level': risk_level})

    def _save_metrics(self, metrics: Dict[str, Any]) -> None:
        def sanitize(obj):
            if isinstance(obj, (np.integer, int)): return int(obj)
            elif isinstance(obj, (np.floating, float)): return float(obj)
            elif isinstance(obj, np.ndarray): return sanitize(obj.tolist())
            elif isinstance(obj, dict): return {k: sanitize(v) for k, v in obj.items()}
            return str(obj)
        with open(self.metrics_path, 'w', encoding='utf-8') as f:
            json.dump(sanitize(metrics), f, indent=2, ensure_ascii=False)