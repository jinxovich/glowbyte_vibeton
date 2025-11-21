"""Загрузка и объединение CSV данных."""

from __future__ import annotations

import pandas as pd
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')


class DataPreprocessor:
    """Класс для загрузки и объединения всех CSV файлов."""
    
    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)

    def _normalize_ids(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        """Приводит строковые ID к единому формату."""
        for col in cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.lower()
        return df
        
    def load_fires(self) -> pd.DataFrame:
        path = self.data_dir / "fires.csv"
        df = pd.read_csv(path, encoding='utf-8')
        
        df['Дата начала'] = pd.to_datetime(df['Дата начала'])
        df['Дата оконч.'] = pd.to_datetime(df['Дата оконч.'])
        df['Нач.форм.штабеля'] = pd.to_datetime(df['Нач.форм.штабеля'])
        
        # ВАЖНО: Целевая переменная - начало пожара, а не конец
        df['fire_date'] = df['Дата начала']
        
        df = df.rename(columns={
            'Склад': 'storage_id',
            'Штабель': 'stack_id',
            'Груз': 'cargo_code',
            'Вес по акту, тн': 'fire_weight',
            'Нач.форм.штабеля': 'stack_formation_date'
        })
        
        df = self._normalize_ids(df, ['storage_id', 'stack_id', 'cargo_code'])
        # Сортировка важна для merge_asof
        return df.sort_values('fire_date')
    
    def load_supplies(self) -> pd.DataFrame:
        path = self.data_dir / "supplies.csv"
        df = pd.read_csv(path, encoding='utf-8')
        
        df['ВыгрузкаНаСклад'] = pd.to_datetime(df['ВыгрузкаНаСклад'])
        df['ПогрузкаНаСудно'] = pd.to_datetime(df['ПогрузкаНаСудно'])
        df['days_in_storage'] = (df['ПогрузкаНаСудно'] - df['ВыгрузкаНаСклад']).dt.days
        
        df = df.rename(columns={
            'Склад': 'storage_id',
            'Штабель': 'stack_id',
            'Наим. ЕТСНГ': 'cargo_code',
            'На склад, тн': 'coal_weight_storage',
            'На судно, тн': 'coal_weight_ship',
            'ВыгрузкаНаСклад': 'unload_date',
            'ПогрузкаНаСудно': 'load_date'
        })
        
        df = self._normalize_ids(df, ['storage_id', 'stack_id', 'cargo_code'])
        return df
    
    def load_temperature(self) -> pd.DataFrame:
        path = self.data_dir / "temperature.csv"
        df = pd.read_csv(path, encoding='utf-8')
        df['Дата акта'] = pd.to_datetime(df['Дата акта'])
        
        df = df.rename(columns={
            'Склад': 'storage_id',
            'Штабель': 'stack_id',
            'Марка': 'coal_grade',
            'Максимальная температура': 'max_temp',
            'Дата акта': 'measurement_date',
            'Смена': 'shift',
            'Пикет': 'picket'
        })
        
        df = self._normalize_ids(df, ['storage_id', 'stack_id', 'coal_grade'])
        # Сортировка важна для merge_asof
        return df.sort_values('measurement_date')
    
    def load_weather(self) -> pd.DataFrame:
        weather_files = sorted(self.data_dir.glob("weather_data_*.csv"))
        if not weather_files:
            return pd.DataFrame()

        dfs = []
        for file in weather_files:
            df = pd.read_csv(file, encoding='utf-8')
            dfs.append(df)
        
        df = pd.concat(dfs, ignore_index=True)
        df['date'] = pd.to_datetime(df['date'])
        df['weather_date'] = df['date'].dt.date
        
        agg_df = df.groupby('weather_date').agg({
            't': 'mean', 'humidity': 'mean', 'precipitation': 'sum',
            'v_avg': 'mean', 'v_max': 'max'
        }).reset_index()
        
        agg_df['weather_date'] = pd.to_datetime(agg_df['weather_date'])
        
        return agg_df.rename(columns={
            't': 'weather_temp', 'humidity': 'weather_humidity',
            'precipitation': 'weather_precipitation',
            'v_avg': 'wind_speed_avg', 'v_max': 'wind_speed_max'
        })
    
    def merge_all_data(self) -> pd.DataFrame:
        print("📊 Загрузка данных (Smart Merge)...")
        
        fires_df = self.load_fires()
        supplies_df = self.load_supplies()
        temperature_df = self.load_temperature()
        weather_df = self.load_weather()
        
        # 1. Привязка Supplies
        supplies_agg = supplies_df.groupby(['storage_id', 'stack_id']).agg({
            'coal_weight_storage': 'sum',
            'days_in_storage': 'max',
            'unload_date': 'min',
            'cargo_code': 'first'
        }).reset_index()
        
        df = temperature_df.merge(supplies_agg, on=['storage_id', 'stack_id'], how='left')
        
        # 2. Привязка Погоды
        if not weather_df.empty:
            df['weather_date'] = pd.to_datetime(df['measurement_date'].dt.date)
            df = df.merge(weather_df, on='weather_date', how='left')
        
        # 3. УМНАЯ ПРИВЯЗКА ПОЖАРОВ (merge_asof)
        df = df.sort_values('measurement_date')
        fires_df = fires_df.sort_values('fire_date')
        
        merged_df = pd.merge_asof(
            df,
            fires_df[['storage_id', 'stack_id', 'fire_date', 'stack_formation_date']],
            left_on='measurement_date',
            right_on='fire_date',
            by=['storage_id', 'stack_id'],
            direction='forward',
            tolerance=pd.Timedelta(days=180)
        )
        
        merged_df['days_until_fire'] = (merged_df['fire_date'] - merged_df['measurement_date']).dt.days
        
        if 'stack_formation_date_y' in merged_df.columns:
             merged_df['stack_formation_date'] = merged_df['stack_formation_date_y'].fillna(merged_df['unload_date'])
        else:
             merged_df['stack_formation_date'] = merged_df['unload_date']
             
        merged_df['days_since_formation'] = (merged_df['measurement_date'] - merged_df['stack_formation_date']).dt.days
        
        print(f"✓ Всего замеров: {len(df)}")
        print(f"✓ Замеров, привязанных к будущим пожарам: {merged_df['days_until_fire'].notna().sum()}")
        
        return merged_df
    
    def prepare_full_dataset(self) -> pd.DataFrame:
        """Возвращает датасет для ML."""
        df = self.merge_all_data()
        
        # Берем только те, где есть привязка к пожару
        df_train = df[df['days_until_fire'].notna()].copy()
        
        # Очистка дубликатов
        df_train['measurement_day'] = df_train['measurement_date'].dt.date
        
        # ВАЖНО: Добавил 'coal_grade' в агрегацию
        agg_dict = {
            'max_temp': 'max',
            'days_until_fire': 'min',
            'days_since_formation': 'first',
            'fire_date': 'first',
            'coal_weight_storage': 'first',
            'weather_temp': 'mean',
            'weather_humidity': 'mean',
            'wind_speed_avg': 'mean',
            'coal_grade': 'first' 
        }
        
        # Добавляем отсутствующие колонки
        for col in agg_dict:
            if col not in df_train.columns:
                # Для строк ставим unknown, для чисел 0
                if col == 'coal_grade':
                    df_train[col] = 'unknown'
                else:
                    df_train[col] = 0
                
        grouped = df_train.groupby(['storage_id', 'stack_id', 'measurement_day']).agg(agg_dict).reset_index()
        
        # Возвращаем имя measurement_date
        grouped = grouped.rename(columns={'measurement_day': 'measurement_date'})
        grouped['measurement_date'] = pd.to_datetime(grouped['measurement_date'])
        
        return grouped