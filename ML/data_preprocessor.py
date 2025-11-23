"""Загрузка ВСЕХ доступных данных (Type Safe Version)."""
from __future__ import annotations
import pandas as pd
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

class DataPreprocessor:
    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)

    def _normalize_ids(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        for col in cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.lower()
        return df
        
    def load_fires(self) -> pd.DataFrame:
        path = self.data_dir / "fires.csv"
        df = pd.read_csv(path, encoding='utf-8')
        # errors='coerce' превратит битые даты в NaT, а не оставит строками
        df['fire_date'] = pd.to_datetime(df['Дата начала'], errors='coerce')
        
        df = df.rename(columns={
            'Склад': 'storage_id', 'Штабель': 'stack_id',
            'Нач.форм.штабеля': 'stack_formation_date'
        })
        # Удаляем строки, где дата пожара не распозналась
        df = df.dropna(subset=['fire_date'])
        return self._normalize_ids(df, ['storage_id', 'stack_id']).sort_values('fire_date')
    
    def load_supplies(self) -> pd.DataFrame:
        path = self.data_dir / "supplies.csv"
        df = pd.read_csv(path, encoding='utf-8')
        
        df['unload_date'] = pd.to_datetime(df['ВыгрузкаНаСклад'], errors='coerce')
        
        df = df.rename(columns={
            'Склад': 'storage_id', 'Штабель': 'stack_id',
            'Наим. ЕТСНГ': 'coal_grade',
            'На склад, тн': 'weight_in'
        })
        return self._normalize_ids(df, ['storage_id', 'stack_id', 'coal_grade'])
    
    def load_temperature(self) -> pd.DataFrame:
        path = self.data_dir / "temperature.csv"
        df = pd.read_csv(path, encoding='utf-8')
        df['measurement_date'] = pd.to_datetime(df['Дата акта'], errors='coerce')
        
        df = df.rename(columns={
            'Склад': 'storage_id', 'Штабель': 'stack_id',
            'Максимальная температура': 'max_temp',
            'Пикет': 'picket', 'Смена': 'shift'
        })
        return self._normalize_ids(df, ['storage_id', 'stack_id']).sort_values('measurement_date')
    
    def load_weather(self) -> pd.DataFrame:
        dfs = []
        for file in sorted(self.data_dir.glob("weather_data_*.csv")):
            dfs.append(pd.read_csv(file, encoding='utf-8'))
        if not dfs: return pd.DataFrame()
        
        df = pd.concat(dfs, ignore_index=True)
        df['weather_date'] = pd.to_datetime(pd.to_datetime(df['date'], errors='coerce').dt.date)
        
        # Агрегируем по дням
        agg_df = df.groupby('weather_date').agg({
            't': 'mean', 'humidity': 'mean', 'precipitation': 'sum',
            'p': 'mean', 'cloudcover': 'mean', 'visibility': 'mean',
            'v_avg': 'mean', 'v_max': 'max', 
            'wind_dir': 'mean',
            'weather_code': lambda x: x.mode()[0] if not x.mode().empty else 0 
        }).reset_index()
        
        return agg_df.rename(columns={
            't': 'weather_temp', 'humidity': 'weather_humidity',
            'precipitation': 'weather_precipitation',
            'p': 'pressure', 'cloudcover': 'cloud_cover',
            'v_avg': 'wind_speed_avg', 'v_max': 'wind_speed_max'
        })
    
    def prepare_full_dataset(self) -> pd.DataFrame:
        print("📊 Загрузка FULL DATASET (Safe Mode)...")
        fires = self.load_fires()
        supplies = self.load_supplies()
        temp = self.load_temperature()
        weather = self.load_weather()
        
        # 1. Агрегация поставок
        supplies_agg = supplies.groupby(['storage_id', 'stack_id']).agg({
            'weight_in': 'sum',
            'unload_date': 'min',
            'coal_grade': 'first'
        }).rename(columns={'weight_in': 'coal_weight_storage'}).reset_index()
        
        # 2. Основной мердж
        df = temp.merge(supplies_agg, on=['storage_id', 'stack_id'], how='left')
        
        # 3. Мердж погоды
        if not weather.empty:
            df['weather_date'] = pd.to_datetime(df['measurement_date'].dt.date)
            df = df.merge(weather, on='weather_date', how='left')
            
        # 4. Мердж целевой переменной
        df = df.sort_values('measurement_date')
        fires = fires.sort_values('fire_date')
        
        merged = pd.merge_asof(
            df,
            fires[['storage_id', 'stack_id', 'fire_date', 'stack_formation_date']],
            left_on='measurement_date', right_on='fire_date',
            by=['storage_id', 'stack_id'],
            direction='forward', tolerance=pd.Timedelta(days=120)
        )
        
        merged['days_until_fire'] = (merged['fire_date'] - merged['measurement_date']).dt.days
        
        # --- БЕЗОПАСНОЕ ОПРЕДЕЛЕНИЕ ВОЗРАСТА ---
        
        # 1. Ищем колонку с датой формирования
        if 'stack_formation_date_y' in merged.columns:
            formation_col = 'stack_formation_date_y'
        elif 'stack_formation_date' in merged.columns:
            formation_col = 'stack_formation_date'
        else:
            merged['stack_formation_date_temp'] = pd.NaT
            formation_col = 'stack_formation_date_temp'

        # 2. Собираем дату: Пожары -> Поставки -> Замер
        start_date_series = merged[formation_col].fillna(merged['unload_date'])
        start_date_series = start_date_series.fillna(merged['measurement_date'])
        
        # 3. ПРИНУДИТЕЛЬНАЯ КОНВЕРТАЦИЯ В DATETIME (FIX TYPE ERROR)
        start_date_series = pd.to_datetime(start_date_series, errors='coerce')
        measurement_date_series = pd.to_datetime(merged['measurement_date'], errors='coerce')
        
        # 4. Вычитание (теперь точно Timestamp - Timestamp)
        merged['days_since_formation'] = (measurement_date_series - start_date_series).dt.days
        
        # Заполняем возможные NaN в днях нулями (если даты были битые)
        merged['days_since_formation'] = merged['days_since_formation'].fillna(0)

        cols = [
            'storage_id', 'stack_id', 'measurement_date', 'days_until_fire',
            'max_temp', 'days_since_formation', 'coal_weight_storage', 'coal_grade',
            'picket', 'shift',
            'weather_temp', 'weather_humidity', 'weather_precipitation', 'pressure', 
            'cloud_cover', 'visibility', 'wind_speed_avg', 'wind_speed_max', 
            'wind_dir', 'weather_code'
        ]
        
        for c in cols:
            if c not in merged.columns: merged[c] = 0
                
        return merged[cols].dropna(subset=['measurement_date'])