"""Feature engineering для прогнозирования самовозгорания угля."""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import List


class FeatureEngineer:
    """Класс для создания признаков из сырых данных."""
    
    @staticmethod
    def create_features(df: pd.DataFrame) -> pd.DataFrame:
        """Создать все признаки для модели."""
        df = df.copy()
        
        print("\n🔧 Создание признаков...")
        
        # Сортировка
        df = df.sort_values(['storage_id', 'stack_id', 'measurement_date']).reset_index(drop=True)
        
        # ===== 1. ЗАПОЛНЕНИЕ ПРОПУСКОВ (УМНОЕ) =====
        df['max_temp'] = df.groupby(['storage_id', 'stack_id'])['max_temp'].ffill()
        df['max_temp'] = df['max_temp'].fillna(df['max_temp'].median())
        
        df['coal_weight'] = df.get('coal_weight_storage', pd.Series([0]*len(df)))
        df['coal_weight'] = df['coal_weight'].fillna(df['coal_weight'].median())
        
        # ===== 2. ТЕМПЕРАТУРНЫЕ ПРИЗНАКИ =====
        df['temp_growth_rate'] = df.groupby(['storage_id', 'stack_id'])['max_temp'].diff().fillna(0)
        
        grouped = df.groupby(['storage_id', 'stack_id'])['max_temp']
        for window in [3, 7, 14]:
            df[f'temp_rolling_{window}d_max'] = grouped.transform(lambda x: x.rolling(window, min_periods=1).max())
            df[f'temp_rolling_{window}d_avg'] = grouped.transform(lambda x: x.rolling(window, min_periods=1).mean())
            df[f'temp_rolling_{window}d_std'] = grouped.transform(lambda x: x.rolling(window, min_periods=1).std()).fillna(0)
        
        df['high_temp_indicator'] = (df['max_temp'] > 40).astype(int)
        df['extreme_temp_indicator'] = (df['max_temp'] > 60).astype(int)
        
        df['high_temp_days_7d'] = df.groupby(['storage_id', 'stack_id'])['high_temp_indicator'].transform(
            lambda x: x.rolling(7, min_periods=1).sum()
        )
        
        # ===== 3. ПОГОДНЫЕ ПРИЗНАКИ =====
        weather_cols = ['weather_temp', 'weather_humidity', 'wind_speed_avg', 'weather_precipitation']
        for col in weather_cols:
            if col not in df.columns:
                df[col] = 0
            else:
                df[col] = df[col].fillna(df[col].mean())
                
        df['low_humidity_indicator'] = (df['weather_humidity'] < 50).astype(int)
        df['high_wind_indicator'] = (df['wind_speed_avg'] > 8).astype(int)
        
        # ===== 4. КОМБИНИРОВАННЫЕ ИНДЕКСЫ =====
        df['thermal_stress_index'] = (
            df['max_temp'] * 
            (1 - df['weather_humidity'] / 200) * 
            (1 + df['wind_speed_avg'] / 20)
        )
        df['temp_diff_internal_external'] = df['max_temp'] - df['weather_temp']
        
        # ===== 5. ВРЕМЕННЫЕ ПРИЗНАКИ =====
        df['days_since_formation'] = df['days_since_formation'].fillna(0)
        df['days_in_storage'] = df['days_since_formation']
        
        if 'measurement_date' in df.columns:
            df['month'] = pd.to_datetime(df['measurement_date']).dt.month
            df['season'] = df['month'].map({12:0, 1:0, 2:0, 3:1, 4:1, 5:1, 6:2, 7:2, 8:2, 9:3, 10:3, 11:3})
        else:
            df['month'] = 6
            df['season'] = 2
            
        # ===== 6. ЛАГИ (ИСТОРИЯ) =====
        lag_features = ['max_temp', 'thermal_stress_index']
        lags = [1, 3, 7]
        
        for feature in lag_features:
            for lag in lags:
                col_name = f'{feature}_lag_{lag}d'
                df[col_name] = df.groupby(['storage_id', 'stack_id'])[feature].shift(lag)
                # Заполняем медианой, а не текущим значением (избегаем data leakage)
                df[col_name] = df[col_name].fillna(df[feature].median())

        # ===== 7. FEATURE INTERACTIONS (НОВОЕ) =====
        # Взаимодействия признаков
        df['temp_x_days'] = df['max_temp'] * df['days_since_formation']
        df['temp_x_humidity'] = df['max_temp'] * (100 - df['weather_humidity'])
        df['temp_x_weight'] = df['max_temp'] * np.log1p(df['coal_weight'])
        
        # Нелинейные трансформации
        df['max_temp_squared'] = df['max_temp'] ** 2
        df['max_temp_log'] = np.log1p(df['max_temp'])
        df['days_storage_log'] = np.log1p(df['days_since_formation'])
        
        # Температурные пороги (domain knowledge)
        df['critical_temp_indicator'] = (df['max_temp'] > 70).astype(int)
        df['danger_zone_indicator'] = ((df['max_temp'] > 50) & (df['max_temp'] <= 70)).astype(int)
        
        # Скорость изменения (второй порядок)
        df['temp_acceleration'] = df.groupby(['storage_id', 'stack_id'])['temp_growth_rate'].diff().fillna(0)
        
        # Cumulative features
        df['cumulative_high_temp_days'] = df.groupby(['storage_id', 'stack_id'])['high_temp_indicator'].cumsum()
        
        # Ratio features
        df['temp_to_avg_ratio'] = df['max_temp'] / (df['temp_rolling_7d_avg'] + 1e-10)
        df['humidity_wind_ratio'] = df['weather_humidity'] / (df['wind_speed_avg'] + 1)
        
        # ===== 8. КАТЕГОРИАЛЬНЫЕ ПРИЗНАКИ (ИСПРАВЛЕНО) =====
        # Безопасная обработка, если колонки исчезли
        if 'coal_grade' not in df.columns:
            df['coal_grade'] = 'unknown'
        df['coal_type_encoded'] = pd.factorize(df['coal_grade'])[0]
        
        df['storage_id_encoded'] = pd.factorize(df['storage_id'])[0]
        
        # Статистика (без data leakage - используем cummax)
        df = df.sort_values(['storage_id', 'stack_id', 'measurement_date']).reset_index(drop=True)
        df['stack_max_temp_ever'] = df.groupby(['storage_id', 'stack_id'])['max_temp'].transform('cummax')
        
        print(f"  ✓ Признаки созданы. Размер: {df.shape}")
        return df
    
    @staticmethod
    def get_feature_columns() -> List[str]:
        return [
            # Базовые признаки
            'days_in_storage', 'coal_weight', 'days_since_formation',
            'max_temp', 'temp_growth_rate',
            
            # Rolling features
            'temp_rolling_3d_avg', 'temp_rolling_7d_avg', 'temp_rolling_7d_max',
            'high_temp_days_7d', 'extreme_temp_indicator',
            
            # Погодные признаки
            'weather_temp', 'weather_humidity', 'wind_speed_avg',
            'thermal_stress_index', 'temp_diff_internal_external',
            
            # Временные признаки
            'season', 'coal_type_encoded', 'storage_id_encoded',
            
            # Лаги
            'max_temp_lag_1d', 'max_temp_lag_3d', 'max_temp_lag_7d',
            'thermal_stress_index_lag_1d', 'thermal_stress_index_lag_3d', 'thermal_stress_index_lag_7d',
            
            # Статистика
            'stack_max_temp_ever',
            
            # Новые взаимодействия и трансформации
            'temp_x_days', 'temp_x_humidity', 'temp_x_weight',
            'max_temp_squared', 'max_temp_log', 'days_storage_log',
            'critical_temp_indicator', 'danger_zone_indicator',
            'temp_acceleration', 'cumulative_high_temp_days',
            'temp_to_avg_ratio', 'humidity_wind_ratio'
        ]