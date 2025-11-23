"""Feature engineering (v4.0 - All Inclusive)."""
from __future__ import annotations
import pandas as pd
import numpy as np

class FeatureEngineer:
    @staticmethod
    def create_features(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df = df.sort_values(['storage_id', 'stack_id', 'measurement_date'])

        # 1. Обработка категорий (Хэширование для простоты)
        # Марка угля, Пикет, Смена, Код погоды
        cat_cols = ['coal_grade', 'picket', 'shift', 'weather_code']
        for col in cat_cols:
            if col in df.columns:
                # Превращаем строку в число (hash), чтобы модель могла это съесть
                df[f'{col}_encoded'] = df[col].astype(str).apply(lambda x: hash(x) % 1000)
            else:
                df[f'{col}_encoded'] = 0

        # 2. Ветер (Cyclical encoding)
        # 360 градусов и 0 градусов - это одно и то же, поэтому берем Sin/Cos
        if 'wind_dir' in df.columns:
            df['wind_dir'] = df['wind_dir'].fillna(0)
            df['wind_sin'] = np.sin(2 * np.pi * df['wind_dir'] / 360)
            df['wind_cos'] = np.cos(2 * np.pi * df['wind_dir'] / 360)
        else:
            df['wind_sin'] = 0
            df['wind_cos'] = 0

        # 3. Физические взаимодействия
        # Влажность + Ветер = Индекс испарения (сушки)
        h = df.get('weather_humidity', 50)
        w = df.get('wind_speed_avg', 2)
        df['drying_index'] = w * (100 - h)
        
        # 4. Заполнение пропусков в числовых полях
        num_cols = ['max_temp', 'coal_weight_storage', 'pressure', 'cloud_cover', 'visibility', 'wind_speed_max']
        for col in num_cols:
            if col in df.columns:
                df[col] = df.groupby(['storage_id', 'stack_id'])[col].ffill().fillna(0)

        # 5. Rolling Features (Динамика)
        grouped = df.groupby(['storage_id', 'stack_id'])['max_temp']
        df['temp_velocity'] = grouped.diff(3).fillna(0) / 3
        df['temp_acceleration'] = df.groupby(['storage_id', 'stack_id'])['temp_velocity'].diff().fillna(0)
        
        df['roll_max_7d'] = grouped.transform(lambda x: x.rolling(7, min_periods=1).max()).fillna(0)

        return df.fillna(0)

    @staticmethod
    def get_feature_columns() -> list[str]:
        return [
            'days_since_formation', 'coal_weight_storage',
            'max_temp', 'temp_velocity', 'temp_acceleration', 'roll_max_7d',
            # Категории
            'coal_grade_encoded', 'picket_encoded', 'shift_encoded', 'weather_code_encoded',
            # Погода
            'weather_temp', 'weather_humidity', 'weather_precipitation',
            'pressure', 'cloud_cover', 'visibility',
            'wind_speed_avg', 'wind_speed_max', 'wind_sin', 'wind_cos',
            # Производные
            'drying_index'
        ]