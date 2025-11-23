"""XGBoost с авто-тюнингом (Optuna - Fast Version)."""
from __future__ import annotations
import xgboost as xgb
import optuna
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit

class CoalFireModel:
    def __init__(self):
        self.model = None
        self.feature_names = None
        # Дефолтные параметры (если Optuna упадет или будет отключена)
        self.best_params = {
            'n_estimators': 300, 
            'max_depth': 5, 
            'learning_rate': 0.05,
            'objective': 'reg:squarederror', 
            'n_jobs': -1
        }

    def optimize(self, X: pd.DataFrame, y: pd.Series, n_trials=10):
        """Поиск идеальных гиперпараметров (УСКОРЕННЫЙ)."""
        print(f"🎯 Запуск оптимизации Optuna ({n_trials} попыток)...")
        
        def objective(trial):
            param = {
                'objective': 'reg:squarederror',
                # УМЕНЬШИЛИ ДИАПАЗОНЫ: Меньше деревьев = быстрее
                'n_estimators': trial.suggest_int('n_estimators', 100, 400),
                'max_depth': trial.suggest_int('max_depth', 3, 6),
                'learning_rate': trial.suggest_float('learning_rate', 0.03, 0.15),
                'subsample': trial.suggest_float('subsample', 0.7, 0.9),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.7, 0.9),
                # Регуляризация
                'reg_alpha': trial.suggest_float('reg_alpha', 0, 5),
                'reg_lambda': trial.suggest_float('reg_lambda', 0, 5),
                'n_jobs': -1,
                'random_state': 42
            }
            
            # 3 фолда - оптимально для скорости
            tscv = TimeSeriesSplit(n_splits=3)
            scores = []
            
            for train_idx, val_idx in tscv.split(X):
                X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
                y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]
                
                model = xgb.XGBRegressor(**param)
                model.fit(X_tr, y_tr, verbose=False)
                preds = model.predict(X_val)
                scores.append(mean_absolute_error(y_val, preds))
            
            return np.mean(scores)

        # Ограничиваем время (не больше 60 секунд на поиск) или количество попыток
        study = optuna.create_study(direction='minimize')
        study.optimize(objective, n_trials=n_trials, timeout=60)
        
        print(f"✅ Лучшие параметры: {study.best_params}")
        self.best_params = study.best_params
        self.best_params['objective'] = 'reg:squarederror'
        self.best_params['n_jobs'] = -1

    def train_final(self, X: pd.DataFrame, y: pd.Series):
        self.feature_names = X.columns.tolist()
        
        print(f"⚙️ Применяем параметры: {self.best_params}")
        self.model = xgb.XGBRegressor(**self.best_params)
        self.model.fit(X, y, verbose=False)
        
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self.feature_names:
            # Гарантируем порядок колонок как при обучении
            # Если какой-то колонки нет - ошибка (или заполним 0)
            missing = set(self.feature_names) - set(X.columns)
            if missing:
                for c in missing: X[c] = 0
            X = X[self.feature_names]
            
        return np.maximum(self.model.predict(X), 0) 

    def save(self, path: str | Path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({'model': self.model, 'feat': self.feature_names}, path)

    def load(self, path: str | Path):
        data = joblib.load(path)
        self.model = data['model']
        self.feature_names = data['feat']
    
    def get_feature_importance(self, top_n: int = 20) -> pd.DataFrame:
        if self.feature_names is None: return pd.DataFrame()
        return pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False).head(top_n)