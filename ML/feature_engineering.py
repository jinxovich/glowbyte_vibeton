"""Feature engineering для прогнозирования самовозгорания угля."""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import List


class FeatureEngineer:
    """Класс для создания признаков из сырых данных."""
    
    @staticmethod
    def create_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Создать все признаки для модели.
        
        Входные данные: объединенный датафрейм со всеми CSV
        Выходные данные: датафрейм с новыми признаками
        """
        df = df.copy()
        
        print("\n🔧 Создание признаков...")
        
        # ===== 1. ЛОГИСТИЧЕСКИЕ ПРИЗНАКИ (из supplies) =====
        df['coal_weight'] = df['coal_weight_storage'].fillna(df['coal_weight_storage'].median())
        
        # ===== 2. ТЕМПЕРАТУРНЫЕ ПРИЗНАКИ (из temperature) =====
        # Базовый признак
        df['max_temp'] = df['max_temp'].fillna(df['max_temp'].mean())
        
        # Сортировка для правильного расчета rolling и lag
        df = df.sort_values(['storage_id', 'stack_id', 'measurement_date']).reset_index(drop=True)
        
        # Скорость роста температуры
        df['temp_growth_rate'] = df.groupby(['storage_id', 'stack_id'])['max_temp'].diff()
        df['temp_growth_rate'] = df['temp_growth_rate'].fillna(0)
        
        # Rolling статистика по температуре
        for window in [3, 7, 14]:
            df[f'temp_rolling_{window}d_max'] = df.groupby(['storage_id', 'stack_id'])['max_temp'].transform(
                lambda x: x.rolling(window, min_periods=1).max()
            )
            df[f'temp_rolling_{window}d_avg'] = df.groupby(['storage_id', 'stack_id'])['max_temp'].transform(
                lambda x: x.rolling(window, min_periods=1).mean()
            )
            df[f'temp_rolling_{window}d_std'] = df.groupby(['storage_id', 'stack_id'])['max_temp'].transform(
                lambda x: x.rolling(window, min_periods=1).std()
            )
        
        # Заполнить NaN в std
        for window in [3, 7, 14]:
            df[f'temp_rolling_{window}d_std'] = df[f'temp_rolling_{window}d_std'].fillna(0)
        
        # Количество дней с высокой температурой
        df['high_temp_indicator'] = (df['max_temp'] > 40).astype(int)
        df['high_temp_days_7d'] = df.groupby(['storage_id', 'stack_id'])['high_temp_indicator'].transform(
            lambda x: x.rolling(7, min_periods=1).sum()
        )
        df['high_temp_days_14d'] = df.groupby(['storage_id', 'stack_id'])['high_temp_indicator'].transform(
            lambda x: x.rolling(14, min_periods=1).sum()
        )
        
        # Экстремальные температуры (> 60°C - очень опасно)
        df['extreme_temp_indicator'] = (df['max_temp'] > 60).astype(int)
        df['extreme_temp_days_7d'] = df.groupby(['storage_id', 'stack_id'])['extreme_temp_indicator'].transform(
            lambda x: x.rolling(7, min_periods=1).sum()
        )
        
        # ===== 3. ПОГОДНЫЕ ПРИЗНАКИ (из weather) =====
        weather_cols = ['weather_temp', 'weather_humidity', 'weather_precipitation', 
                       'wind_speed_avg', 'wind_speed_max', 'weather_cloudcover']
        
        for col in weather_cols:
            if col in df.columns:
                df[col] = df[col].fillna(df[col].mean())
            else:
                df[col] = 0
        
        # Низкая влажность = выше риск
        df['low_humidity_indicator'] = (df['weather_humidity'] < 50).astype(int)
        
        # Высокая скорость ветра = ускоряет окисление
        df['high_wind_indicator'] = (df['wind_speed_avg'] > 10).astype(int)
        
        # ===== 4. КОМБИНИРОВАННЫЕ ПРИЗНАКИ =====
        
        # Тепловой индекс стресса
        # Учитывает температуру, влажность и ветер
        df['thermal_stress_index'] = (
            df['max_temp'] * 
            (1 - df['weather_humidity'] / 100) * 
            (1 + df['wind_speed_avg'] / 10)
        )
        
        # Индекс сухости (низкая влажность + мало осадков)
        df['dryness_index'] = (
            (100 - df['weather_humidity']) * 
            (1 / (df['weather_precipitation'] + 1))
        )
        
        # Окислительный индекс (температура + ветер - влажность)
        df['oxidation_index'] = (
            df['max_temp'] + 
            df['wind_speed_avg'] * 5 - 
            df['weather_humidity'] * 0.5
        )
        
        # Разница между внутренней и внешней температурой
        df['temp_diff_internal_external'] = df['max_temp'] - df['weather_temp']
        
        # ===== 5. ВРЕМЕННЫЕ ПРИЗНАКИ =====
        
        # Возраст штабеля
        if 'days_since_formation' in df.columns:
            df['days_since_formation'] = df['days_since_formation'].fillna(0)
        else:
            df['days_since_formation'] = 0
        
        # Дни в хранении
        if 'days_in_storage' not in df.columns:
            df['days_in_storage'] = df['days_since_formation']
        df['days_in_storage'] = df['days_in_storage'].fillna(df['days_since_formation'])
        
        # Сезонные признаки
        df['month'] = pd.to_datetime(df['measurement_date']).dt.month
        df['season'] = df['month'].map({
            12: 0, 1: 0, 2: 0,  # Зима
            3: 1, 4: 1, 5: 1,    # Весна
            6: 2, 7: 2, 8: 2,    # Лето (выше риск)
            9: 3, 10: 3, 11: 3   # Осень
        })
        
        # День недели (для цикличности работ)
        df['day_of_week'] = pd.to_datetime(df['measurement_date']).dt.dayofweek
        
        # ===== 6. КАТЕГОРИАЛЬНЫЕ ПРИЗНАКИ =====
        
        # Тип угля
        if 'coal_grade' in df.columns:
            df['coal_type_encoded'] = pd.factorize(df['coal_grade'])[0]
        else:
            df['coal_type_encoded'] = 0
        
        # Склад
        df['storage_id_encoded'] = pd.factorize(df['storage_id'])[0]
        
        # ===== 7. ЛАГИ (для учета истории) =====
        
        lag_features = {
            'max_temp': [1, 2, 3, 7, 14],
            'weather_humidity': [1, 3, 7],
            'wind_speed_avg': [1, 3],
            'thermal_stress_index': [1, 3, 7]
        }
        
        for feature, lags in lag_features.items():
            if feature in df.columns:
                for lag in lags:
                    col_name = f'{feature}_lag_{lag}d'
                    df[col_name] = df.groupby(['storage_id', 'stack_id'])[feature].shift(lag)
                    df[col_name] = df[col_name].fillna(df[feature])
        
        # ===== 8. СТАТИСТИКА ПО ШТАБЕЛЮ =====
        
        # Максимальная температура за всю историю штабеля
        df['stack_max_temp_ever'] = df.groupby(['storage_id', 'stack_id'])['max_temp'].transform('max')
        
        # Средняя температура штабеля
        df['stack_avg_temp'] = df.groupby(['storage_id', 'stack_id'])['max_temp'].transform('mean')
        
        # Количество измерений для штабеля (индикатор мониторинга)
        df['stack_measurement_count'] = df.groupby(['storage_id', 'stack_id']).cumcount() + 1
        
        print(f"  ✓ Создано признаков: {len([col for col in df.columns if col not in ['fire_date', 'days_until_fire']])}")
        
        return df
    
    @staticmethod
    def get_feature_columns() -> List[str]:
        """Получить список всех признаков для модели."""
        return [
            # Логистические
            'days_in_storage',
            'coal_weight',
            'days_since_formation',
            
            # Температурные
            'max_temp',
            'temp_growth_rate',
            'temp_rolling_3d_max',
            'temp_rolling_3d_avg',
            'temp_rolling_3d_std',
            'temp_rolling_7d_max',
            'temp_rolling_7d_avg',
            'temp_rolling_7d_std',
            'temp_rolling_14d_max',
            'temp_rolling_14d_avg',
            'temp_rolling_14d_std',
            'high_temp_days_7d',
            'high_temp_days_14d',
            'extreme_temp_days_7d',
            
            # Погодные
            'weather_temp',
            'weather_humidity',
            'weather_precipitation',
            'wind_speed_avg',
            'wind_speed_max',
            'weather_cloudcover',
            'low_humidity_indicator',
            'high_wind_indicator',
            
            # Комбинированные
            'thermal_stress_index',
            'dryness_index',
            'oxidation_index',
            'temp_diff_internal_external',
            
            # Временные
            'month',
            'season',
            'day_of_week',
            
            # Категориальные
            'coal_type_encoded',
            'storage_id_encoded',
            
            # Лаги
            'max_temp_lag_1d',
            'max_temp_lag_2d',
            'max_temp_lag_3d',
            'max_temp_lag_7d',
            'max_temp_lag_14d',
            'weather_humidity_lag_1d',
            'weather_humidity_lag_3d',
            'weather_humidity_lag_7d',
            'wind_speed_avg_lag_1d',
            'wind_speed_avg_lag_3d',
            'thermal_stress_index_lag_1d',
            'thermal_stress_index_lag_3d',
            'thermal_stress_index_lag_7d',
            
            # Статистика по штабелю
            'stack_max_temp_ever',
            'stack_avg_temp',
            'stack_measurement_count',
        ]


__all__ = ["FeatureEngineer"]

