"""Главный класс для обучения и предсказания."""

from __future__ import annotations

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sklearn.model_selection import train_test_split

from .data_preprocessor import DataPreprocessor
from .feature_engineering import FeatureEngineer
from .model import CoalFireModel
from .metrics import evaluate_model, print_metrics_report


class CoalCombustionPredictor:
    """Основной класс для работы с моделью прогнозирования самовозгорания."""
    
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
            except Exception:
                pass
    
    def train(self) -> Dict[str, Any]:
        """Обучить модель."""
        print("\n" + "="*60)
        print("🔥 ОБУЧЕНИЕ МОДЕЛИ (ФИНАЛЬНЫЙ ЗАПУСК)")
        print("="*60)
        
        # 1. Загрузка
        raw_df = self.preprocessor.prepare_full_dataset()
        if raw_df.empty: raise ValueError("Датасет пуст!")

        # 2. Фичи
        full_df = self.feature_engineer.create_features(raw_df)
        
        # 3. Фильтрация (60 дней)
        print("\n🔪 Фильтрация обучающей выборки (0 <= дней до пожара <= 60)...")
        train_df = full_df[
            (full_df['days_until_fire'] >= 0) & 
            (full_df['days_until_fire'] <= 60)
        ].copy()
        
        if len(train_df) < 10: raise ValueError("Мало данных (<10).")
            
        # 4. Подготовка X и y
        feature_cols = self.feature_engineer.get_feature_columns()
        for col in feature_cols:
            if col not in train_df.columns: train_df[col] = 0
        
        X = train_df[feature_cols].fillna(0)
        y = train_df['days_until_fire']
        
        print(f"  ✓ Всего строк: {len(X)}")
        
        # 5. ЧЕСТНОЕ РАЗДЕЛЕНИЕ (Hold-out)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=True)
        
        print(f"  ✓ Обучение на: {len(X_train)} строк")
        print(f"  ✓ Тест (проверка) на: {len(X_test)} строк")
        
        # Обучаем
        self.model.train(X_train, y_train, cv_splits=5)
        
        # Проверяем
        print("\n⚖️  ПРОВЕРКА НА ОТЛОЖЕННЫХ ДАННЫХ:")
        y_pred_test = self.model.predict(X_test)
        test_metrics = evaluate_model(y_test.values, y_pred_test)
        
        print_metrics_report(test_metrics)
        
        # === НОВОЕ: СОХРАНЯЕМ СРАВНЕНИЕ В CSV ===
        comparison_df = X_test.copy()
        comparison_df['REAL_DAYS'] = y_test.values
        comparison_df['PREDICTED_DAYS'] = np.round(y_pred_test, 1)
        comparison_df['ERROR'] = comparison_df['PREDICTED_DAYS'] - comparison_df['REAL_DAYS']
        
        # Оставляем только понятные колонки для просмотра
        view_cols = ['storage_id_encoded', 'max_temp', 'days_since_formation', 'REAL_DAYS', 'PREDICTED_DAYS', 'ERROR']
        # Если есть оригинальные ID, было бы круче, но они закодированы. Сохраняем как есть.
        
        save_path = self.artifacts_dir / "final_comparison.csv"
        comparison_df.to_csv(save_path, index=False)
        print(f"💾 Файл со сравнением сохранен: {save_path}")
        print("   (Открой его, чтобы увидеть реальные vs предсказанные даты!)")

        # === НОВОЕ: ПОКАЗЫВАЕМ ВАЖНОСТЬ ПРИЗНАКОВ ===
        print("\n🔍 ТОП-10 ПРИЧИН ВОЗГОРАНИЯ (Feature Importance):")
        imp = self.model.get_feature_importance(top_n=10)
        print(imp.to_string(index=False))
        
        # 6. Финальное переобучение
        print("\n💾 Сохранение финальной модели...")
        self.model.model.fit(X, y, verbose=False)
        self.model.save(self.model_path)
        self._save_metrics(test_metrics)
        
        return test_metrics
    
    def predict(self, input_df: pd.DataFrame) -> List[Dict[str, Any]]:
        if not self.model_path.exists(): raise FileNotFoundError("Модель не обучена!")
        df = input_df.copy()
        rename_map = {'max_temperature': 'max_temp', 'pile_age_days': 'days_since_formation', 'stack_mass_tons': 'coal_weight'}
        df = df.rename(columns=rename_map)
        
        if 'days_since_formation' not in df.columns: df['days_since_formation'] = 0
        for col in ['weather_temp', 'weather_humidity', 'wind_speed_avg']:
            if col not in df.columns: df[col] = 0
                
        df['temp_growth_rate'] = 0 
        df['thermal_stress_index'] = df['max_temp'] * (1 - df.get('weather_humidity', 50)/200)
        
        feature_cols = self.feature_engineer.get_feature_columns()
        for col in feature_cols:
            if col not in df.columns: df[col] = 0
        X = df[feature_cols].fillna(0)
        preds = self.model.predict_with_confidence(X)
        
        results = []
        for i, row in df.iterrows():
            p_days = preds.iloc[i]['predicted_days']
            results.append({
                'storage_id': str(row.get('storage_id', '')),
                'stack_id': str(row.get('stack_id', '')),
                'predicted_ttf_days': float(p_days),
                'risk_level': str(preds.iloc[i]['risk_level']),
                'confidence': float(preds.iloc[i]['confidence'])
            })
        return results

    def _save_metrics(self, metrics: Dict[str, Any]) -> None:
        def sanitize(obj):
            if isinstance(obj, dict): return {k: sanitize(v) for k, v in obj.items()}
            elif isinstance(obj, list): return [sanitize(v) for v in obj]
            elif isinstance(obj, np.integer): return int(obj)
            elif isinstance(obj, np.floating): return float(obj)
            elif isinstance(obj, np.ndarray): return sanitize(obj.tolist())
            elif isinstance(obj, np.bool_): return bool(obj)
            elif pd.isna(obj): return None
            else: return obj
        clean_metrics = sanitize(metrics)
        with open(self.metrics_path, 'w', encoding='utf-8') as f:
            json.dump(clean_metrics, f, indent=2, ensure_ascii=False)