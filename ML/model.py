"""XGBoost модель для прогнозирования самовозгорания угля."""

from __future__ import annotations

import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import Optional, Dict, Any
from sklearn.model_selection import TimeSeriesSplit
import xgboost as xgb
import sys

class CoalFireModel:
    """Модель для предсказания дней до самовозгорания."""
    
    def __init__(self, model_params: Optional[Dict[str, Any]] = None):
        """Инициализация модели."""
        if model_params is None:
            # МАКСИМАЛЬНОЕ КАЧЕСТВО (CPU MODE)
            model_params = {
                'n_estimators': 1000,
                'learning_rate': 0.01,
                'max_depth': 5,
                'min_child_weight': 2,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'gamma': 0.1,
                'reg_lambda': 2.0,
                'random_state': 42,
                'n_jobs': -1,
                'objective': 'reg:squarederror',
                'eval_metric': 'rmse',
                # ВАЖНО: Перенесли early_stopping сюда (для новых версий XGBoost)
                'early_stopping_rounds': 50 
            }
        
        self.model = xgb.XGBRegressor(**model_params)
        self.feature_names = None
        self.cv_scores = []
        
    def train(self, X: pd.DataFrame, y: pd.Series, cv_splits: int = 5) -> Dict[str, float]:
        """Обучить модель."""
        self.feature_names = X.columns.tolist()
        
        print(f"\n🤖 Обучение модели XGBoost (High Quality CPU)...", flush=True)
        print(f"   Размер данных: {X.shape}", flush=True)
        
        real_splits = min(cv_splits, len(X) // 20)
        if real_splits < 2:
            print("⚠️ Мало данных для кросс-валидации, обучаем на всем датасете.", flush=True)
            tscv = []
        else:
            tscv = TimeSeriesSplit(n_splits=real_splits)
        
        cv_accuracy_2d = []
        cv_mae = []
        
        if real_splits >= 2:
            for fold, (train_idx, val_idx) in enumerate(tscv.split(X), 1):
                X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
                y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
                
                # Обучаем (early_stopping теперь внутри self.model)
                self.model.fit(
                    X_train, y_train, 
                    eval_set=[(X_val, y_val)], 
                    verbose=False
                )
                y_pred = self.model.predict(X_val)
                
                # Считаем метрики
                acc = self._accuracy_2days(y_pred, y_val.values)
                mae = np.mean(np.abs(y_pred - y_val.values))
                cv_accuracy_2d.append(acc)
                cv_mae.append(mae)
                
                print(f"  🚀 Fold {fold}: Accuracy ±2d={acc:.2%}, MAE={mae:.2f}", flush=True)

            print(f"  ✓ Средняя CV Accuracy: {np.mean(cv_accuracy_2d):.2%}", flush=True)
        
        self.cv_scores = cv_accuracy_2d
        
        # Финальное обучение
        print("  🏁 Финальная сборка модели...", flush=True)
        # Для финального обучения early_stopping не нужен (нет валидации),
        # но он не помешает, просто не сработает без eval_set.
        self.model.fit(X, y, verbose=False)
        
        mean_acc = np.mean(cv_accuracy_2d) if cv_accuracy_2d else 0.0
        mean_mae = np.mean(cv_mae) if cv_mae else 0.0
        
        return {
            'accuracy_2days': mean_acc,
            'mae': mean_mae,
            'n_features': len(self.feature_names),
            'n_samples': len(X)
        }
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self.feature_names is not None:
            X = X[self.feature_names]
        preds = self.model.predict(X)
        return np.maximum(preds, 0)
    
    def predict_with_confidence(self, X: pd.DataFrame) -> pd.DataFrame:
        predictions = self.predict(X)
        confidence = 1 / (1 + predictions / 20) 
        risk_level = pd.cut(
            predictions,
            bins=[-1, 5, 10, 20, 1000],
            labels=['критический', 'высокий', 'средний', 'низкий']
        )
        return pd.DataFrame({
            'predicted_days': predictions,
            'confidence': confidence,
            'risk_level': risk_level
        })
    
    def get_feature_importance(self, top_n: int = 20) -> pd.DataFrame:
        if self.feature_names is None: return pd.DataFrame()
        return pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False).head(top_n)
    
    @staticmethod
    def _accuracy_2days(y_pred: np.ndarray, y_true: np.ndarray) -> float:
        return float(np.mean(np.abs(y_pred - y_true) <= 2))
    
    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({'model': self.model, 'feature_names': self.feature_names}, path)
        print(f"✓ Модель сохранена: {path}", flush=True)
    
    def load(self, path: str | Path) -> CoalFireModel:
        data = joblib.load(path)
        self.model = data['model']
        self.feature_names = data['feature_names']
        return self