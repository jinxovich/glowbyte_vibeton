"""XGBoost модель для прогнозирования самовозгорания угля."""

from __future__ import annotations

import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import Optional, Dict, Any
from sklearn.model_selection import TimeSeriesSplit
import xgboost as xgb


class CoalFireModel:
    """Модель для предсказания дней до самовозгорания."""
    
    def __init__(self, model_params: Optional[Dict[str, Any]] = None):
        """
        Инициализация модели.
        
        Args:
            model_params: Параметры для XGBoost. Если None, используются оптимальные.
        """
        if model_params is None:
            model_params = {
                'n_estimators': 500,
                'learning_rate': 0.03,
                'max_depth': 10,
                'min_child_weight': 1,
                'subsample': 0.9,
                'colsample_bytree': 0.9,
                'gamma': 0.05,
                'reg_alpha': 0.05,
                'reg_lambda': 0.5,
                'random_state': 42,
                'n_jobs': -1,
                'objective': 'reg:squarederror',
                'eval_metric': 'rmse'
            }
        
        self.model = xgb.XGBRegressor(**model_params)
        self.feature_names = None
        self.cv_scores = []
        
    def train(self, X: pd.DataFrame, y: pd.Series, cv_splits: int = 5) -> Dict[str, float]:
        """
        Обучить модель с кросс-валидацией временных рядов.
        
        Args:
            X: DataFrame с признаками
            y: Series с целевой переменной (days_until_fire)
            cv_splits: Количество фолдов для кросс-валидации
            
        Returns:
            Dict с метриками
        """
        self.feature_names = X.columns.tolist()
        
        print(f"\n🤖 Обучение модели XGBoost...")
        print(f"  ✓ Признаков: {len(self.feature_names)}")
        print(f"  ✓ Обучающих примеров: {len(X)}")
        print(f"  ✓ CV фолдов: {cv_splits}")
        
        # Кросс-валидация временных рядов
        tscv = TimeSeriesSplit(n_splits=cv_splits)
        
        cv_accuracy_2d = []
        cv_mae = []
        cv_rmse = []
        
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X), 1):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            # Обучение на фолде
            self.model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose=False
            )
            
            # Предсказание
            y_pred = self.model.predict(X_val)
            
            # Метрики
            accuracy_2d = self._accuracy_2days(y_pred, y_val.values)
            mae = np.mean(np.abs(y_pred - y_val.values))
            rmse = np.sqrt(np.mean((y_pred - y_val.values) ** 2))
            
            cv_accuracy_2d.append(accuracy_2d)
            cv_mae.append(mae)
            cv_rmse.append(rmse)
            
            print(f"  Fold {fold}: Accuracy ±2d={accuracy_2d:.2%}, MAE={mae:.2f}, RMSE={rmse:.2f}")
        
        self.cv_scores = cv_accuracy_2d
        
        # Финальное обучение на всех данных
        print(f"\n  📈 Финальное обучение на всех данных...")
        self.model.fit(X, y, verbose=False)
        
        # Итоговые метрики
        mean_accuracy = np.mean(cv_accuracy_2d)
        mean_mae = np.mean(cv_mae)
        mean_rmse = np.mean(cv_rmse)
        
        print(f"\n✅ Обучение завершено!")
        print(f"  ✓ Средняя Accuracy (±2 дня): {mean_accuracy:.2%}")
        print(f"  ✓ Средний MAE: {mean_mae:.2f} дней")
        print(f"  ✓ Средний RMSE: {mean_rmse:.2f} дней")
        
        if mean_accuracy >= 0.70:
            print(f"  🎉 KPI достигнут! Точность >= 70%")
        else:
            print(f"  ⚠️  KPI не достигнут. Требуется >= 70%, получено {mean_accuracy:.2%}")
        
        return {
            'accuracy_2days': mean_accuracy,
            'accuracy_2days_std': np.std(cv_accuracy_2d),
            'mae': mean_mae,
            'mae_std': np.std(cv_mae),
            'rmse': mean_rmse,
            'rmse_std': np.std(cv_rmse),
            'cv_scores': cv_accuracy_2d,
            'n_features': len(self.feature_names),
            'n_samples': len(X)
        }
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Предсказать количество дней до возгорания.
        
        Args:
            X: DataFrame с признаками
            
        Returns:
            Массив с предсказанными днями до возгорания
        """
        if self.feature_names is not None:
            # Убедимся что используются правильные признаки
            X = X[self.feature_names]
        
        predictions = self.model.predict(X)
        
        # Обрезаем отрицательные значения (не может быть меньше 0)
        predictions = np.maximum(predictions, 0)
        
        return predictions
    
    def predict_with_confidence(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Предсказать с оценкой уверенности.
        
        Returns:
            DataFrame с колонками: prediction, confidence, risk_level
        """
        predictions = self.predict(X)
        
        # Confidence = 1 / (1 + predicted_days/30)
        # Чем меньше дней, тем выше confidence
        confidence = 1 / (1 + predictions / 30)
        
        # Уровень риска
        risk_level = pd.cut(
            predictions,
            bins=[-1, 3, 7, 14, 30, np.inf],
            labels=['критический', 'высокий', 'средний', 'низкий', 'минимальный']
        )
        
        return pd.DataFrame({
            'predicted_days': predictions,
            'confidence': confidence,
            'risk_level': risk_level
        })
    
    def get_feature_importance(self, top_n: int = 20) -> pd.DataFrame:
        """
        Получить важность признаков.
        
        Args:
            top_n: Сколько топовых признаков вернуть
            
        Returns:
            DataFrame с важностью признаков
        """
        if self.feature_names is None:
            return pd.DataFrame()
        
        importance = self.model.feature_importances_
        
        df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        return df.head(top_n)
    
    @staticmethod
    def _accuracy_2days(y_pred: np.ndarray, y_true: np.ndarray) -> float:
        """
        KPI: точность в пределах ±2 дней.
        
        Args:
            y_pred: Предсказанные значения
            y_true: Реальные значения
            
        Returns:
            Доля правильных предсказаний (от 0 до 1)
        """
        return float(np.mean(np.abs(y_pred - y_true) <= 2))
    
    def save(self, path: str | Path) -> None:
        """Сохранить модель."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'cv_scores': self.cv_scores
        }
        
        joblib.dump(model_data, path)
        print(f"✓ Модель сохранена: {path}")
    
    def load(self, path: str | Path) -> CoalFireModel:
        """Загрузить модель."""
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Модель не найдена: {path}")
        
        model_data = joblib.load(path)
        
        self.model = model_data['model']
        self.feature_names = model_data['feature_names']
        self.cv_scores = model_data.get('cv_scores', [])
        
        print(f"✓ Модель загружена: {path}")
        return self


__all__ = ["CoalFireModel"]

