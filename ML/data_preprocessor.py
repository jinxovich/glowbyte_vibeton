"""Загрузка и объединение CSV данных."""

from __future__ import annotations

import pandas as pd
from pathlib import Path
from typing import Optional
import warnings

warnings.filterwarnings('ignore')


class DataPreprocessor:
    """Класс для загрузки и объединения всех CSV файлов."""
    
    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)
        
    def load_fires(self) -> pd.DataFrame:
        """Загрузить fires.csv с парсингом русских столбцов."""
        path = self.data_dir / "fires.csv"
        df = pd.read_csv(path, encoding='utf-8')
        
        # Конвертировать даты
        df['Дата составления'] = pd.to_datetime(df['Дата составления'])
        df['Дата начала'] = pd.to_datetime(df['Дата начала'])
        df['Дата оконч.'] = pd.to_datetime(df['Дата оконч.'])
        df['Нач.форм.штабеля'] = pd.to_datetime(df['Нач.форм.штабеля'])
        
        # Target: дата окончания возгорания
        df['fire_date'] = df['Дата оконч.']
        
        # Переименовать для удобства
        df = df.rename(columns={
            'Склад': 'storage_id',
            'Штабель': 'stack_id',
            'Груз': 'cargo_code',
            'Вес по акту, тн': 'fire_weight',
            'Нач.форм.штабеля': 'stack_formation_date'
        })
        
        return df[['storage_id', 'stack_id', 'fire_date', 'cargo_code', 'fire_weight', 'stack_formation_date']]
    
    def load_supplies(self) -> pd.DataFrame:
        """Загрузить supplies.csv."""
        path = self.data_dir / "supplies.csv"
        df = pd.read_csv(path, encoding='utf-8')
        
        # Конвертировать даты
        df['ВыгрузкаНаСклад'] = pd.to_datetime(df['ВыгрузкаНаСклад'])
        df['ПогрузкаНаСудно'] = pd.to_datetime(df['ПогрузкаНаСудно'])
        
        # Вычислить дни хранения
        df['days_in_storage'] = (df['ПогрузкаНаСудно'] - df['ВыгрузкаНаСклад']).dt.days
        
        # Переименовать
        df = df.rename(columns={
            'Склад': 'storage_id',
            'Штабель': 'stack_id',
            'Наим. ЕТСНГ': 'cargo_code',
            'На склад, тн': 'coal_weight_storage',
            'На судно, тн': 'coal_weight_ship',
            'ВыгрузкаНаСклад': 'unload_date',
            'ПогрузкаНаСудно': 'load_date'
        })
        
        return df[['storage_id', 'stack_id', 'cargo_code', 'coal_weight_storage', 
                   'coal_weight_ship', 'unload_date', 'load_date', 'days_in_storage']]
    
    def load_temperature(self) -> pd.DataFrame:
        """Загрузить temperature.csv."""
        path = self.data_dir / "temperature.csv"
        df = pd.read_csv(path, encoding='utf-8')
        
        # Конвертировать даты
        df['Дата акта'] = pd.to_datetime(df['Дата акта'])
        
        # Переименовать
        df = df.rename(columns={
            'Склад': 'storage_id',
            'Штабель': 'stack_id',
            'Марка': 'coal_grade',
            'Максимальная температура': 'max_temp',
            'Дата акта': 'measurement_date',
            'Смена': 'shift',
            'Пикет': 'picket'
        })
        
        return df[['storage_id', 'stack_id', 'coal_grade', 'max_temp', 'measurement_date', 'shift', 'picket']]
    
    def load_weather(self) -> pd.DataFrame:
        """Загрузить и объединить все weather_data_*.csv."""
        weather_files = sorted(self.data_dir.glob("weather_data_*.csv"))
        
        dfs = []
        for file in weather_files:
            df = pd.read_csv(file, encoding='utf-8')
            dfs.append(df)
        
        df = pd.concat(dfs, ignore_index=True)
        
        # Конвертировать даты
        df['date'] = pd.to_datetime(df['date'])
        
        # Агрегировать по дням (среднее значение за день)
        df['weather_date'] = df['date'].dt.date
        
        agg_df = df.groupby('weather_date').agg({
            't': 'mean',
            'p': 'mean',
            'humidity': 'mean',
            'precipitation': 'sum',
            'v_avg': 'mean',
            'v_max': 'max',
            'cloudcover': 'mean',
            'visibility': 'mean'
        }).reset_index()
        
        agg_df['weather_date'] = pd.to_datetime(agg_df['weather_date'])
        
        # Переименовать
        agg_df = agg_df.rename(columns={
            't': 'weather_temp',
            'p': 'weather_pressure',
            'humidity': 'weather_humidity',
            'precipitation': 'weather_precipitation',
            'v_avg': 'wind_speed_avg',
            'v_max': 'wind_speed_max',
            'cloudcover': 'weather_cloudcover',
            'visibility': 'weather_visibility'
        })
        
        return agg_df
    
    def merge_all_data(self) -> pd.DataFrame:
        """Объединить все данные в один датафрейм."""
        print("📊 Загрузка данных...")
        
        # Загрузить все файлы
        fires_df = self.load_fires()
        supplies_df = self.load_supplies()
        temperature_df = self.load_temperature()
        weather_df = self.load_weather()
        
        print(f"  ✓ fires: {len(fires_df)} записей")
        print(f"  ✓ supplies: {len(supplies_df)} записей")
        print(f"  ✓ temperature: {len(temperature_df)} записей")
        print(f"  ✓ weather: {len(weather_df)} дней")
        
        # Merge temperature с supplies
        # Сначала агрегируем supplies по складу и штабелю
        supplies_agg = supplies_df.groupby(['storage_id', 'stack_id']).agg({
            'coal_weight_storage': 'sum',
            'days_in_storage': 'max',
            'unload_date': 'min',
            'load_date': 'max',
            'cargo_code': 'first'
        }).reset_index()
        
        # Merge temperature с supplies_agg
        df = temperature_df.merge(
            supplies_agg,
            on=['storage_id', 'stack_id'],
            how='left'
        )
        
        # Merge с погодой
        df['weather_date'] = pd.to_datetime(df['measurement_date'].dt.date)
        df = df.merge(
            weather_df,
            on='weather_date',
            how='left'
        )
        
        # Merge с fires для получения целевой переменной
        df = df.merge(
            fires_df[['storage_id', 'stack_id', 'fire_date', 'stack_formation_date']],
            on=['storage_id', 'stack_id'],
            how='left'
        )
        
        # Вычислить days_until_fire (целевая переменная в днях)
        df['days_until_fire'] = (df['fire_date'] - df['measurement_date']).dt.days
        
        # Вычислить days_since_formation
        df['days_since_formation'] = (df['measurement_date'] - df['stack_formation_date']).dt.days
        
        # Удалить записи где измерение было после возгорания
        df = df[df['days_until_fire'] >= 0].copy()
        
        print(f"✓ Объединено: {len(df)} записей")
        print(f"✓ Уникальных штабелей: {df['stack_id'].nunique()}")
        print(f"✓ Штабелей с возгораниями: {df['fire_date'].notna().sum()}")
        
        return df
    
    def prepare_training_data(self) -> tuple[pd.DataFrame, pd.Series]:
        """
        Подготовить данные для обучения.
        Возвращает: (X - признаки, y - целевая переменная)
        """
        df = self.merge_all_data()
        
        # Только записи с известной датой возгорания
        df_train = df[df['fire_date'].notna()].copy()
        
        # Для каждого штабеля берем последние N дней перед возгоранием
        # чтобы обучить модель предсказывать на основе последних измерений
        df_train = df_train.sort_values(['storage_id', 'stack_id', 'measurement_date'])
        
        # Взять последние 30 дней перед возгоранием для каждого штабеля
        df_train = df_train[df_train['days_until_fire'] <= 30].copy()
        
        # ВАЖНО: Для каждого штабеля берем только одну точку на день
        # чтобы избежать дубликатов и переобучения
        df_train['measurement_day'] = pd.to_datetime(df_train['measurement_date']).dt.date
        df_train = df_train.groupby(['storage_id', 'stack_id', 'measurement_day']).agg({
            'storage_id': 'first',
            'stack_id': 'first',
            'measurement_date': 'first',
            'max_temp': 'max',
            'coal_weight_storage': 'first',
            'days_in_storage': 'first',
            'unload_date': 'first',
            'load_date': 'first',
            'cargo_code': 'first',
            'weather_date': 'first',
            'weather_temp': 'mean',
            'weather_pressure': 'mean',
            'weather_humidity': 'mean',
            'weather_precipitation': 'sum',
            'wind_speed_avg': 'mean',
            'wind_speed_max': 'max',
            'weather_cloudcover': 'mean',
            'weather_visibility': 'mean',
            'fire_date': 'first',
            'stack_formation_date': 'first',
            'days_until_fire': 'first',
            'days_since_formation': 'first',
            'coal_grade': 'first'
        }).reset_index(drop=True)
        
        print(f"\n📈 Подготовка обучающих данных:")
        print(f"  ✓ Записей для обучения: {len(df_train)}")
        print(f"  ✓ Уникальных штабелей: {df_train['stack_id'].nunique()}")
        print(f"  ✓ Средний days_until_fire: {df_train['days_until_fire'].mean():.1f}")
        print(f"  ✓ Min/Max days_until_fire: {df_train['days_until_fire'].min():.0f} / {df_train['days_until_fire'].max():.0f}")
        
        return df_train, df_train['days_until_fire']


__all__ = ["DataPreprocessor"]

