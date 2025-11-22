"""
Простой и эффективный предсказатель самовозгорания угля.
Основан на физических принципах, без лишних костылей.
"""

from __future__ import annotations

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List
import joblib
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler


class SimpleCoalFirePredictor:
    """
    Простой предсказатель пожаров.
    Фокус на главном: температура, время хранения, влажность.
    """
    
    def __init__(self, data_dir: Path, artifacts_dir: Path):
        self.data_dir = Path(data_dir)
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = self.artifacts_dir / "models" / "simple_model.pkl"
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        
    def load_data(self) -> pd.DataFrame:
        """Загрузка и объединение всех данных."""
        print("\n📊 Загрузка данных...")
        
        # 1. Fires - целевая переменная
        fires = pd.read_csv(self.data_dir / "fires.csv", encoding='utf-8')
        fires['Дата начала'] = pd.to_datetime(fires['Дата начала'])
        fires['Нач.форм.штабеля'] = pd.to_datetime(fires['Нач.форм.штабеля'])
        fires = fires.rename(columns={
            'Склад': 'storage_id',
            'Штабель': 'stack_id',
            'Дата начала': 'fire_date',
            'Нач.форм.штабеля': 'formation_date'
        })
        print(f"  ✓ Пожары: {len(fires)} событий")
        
        # 2. Temperature - главный предиктор
        temp = pd.read_csv(self.data_dir / "temperature.csv", encoding='utf-8')
        temp['Дата акта'] = pd.to_datetime(temp['Дата акта'])
        temp = temp.rename(columns={
            'Склад': 'storage_id',
            'Штабель': 'stack_id',
            'Максимальная температура': 'max_temp',
            'Дата акта': 'measurement_date'
        })
        print(f"  ✓ Температурные замеры: {len(temp)} записей")
        
        # 3. Supplies - масса и время хранения
        supplies = pd.read_csv(self.data_dir / "supplies.csv", encoding='utf-8')
        supplies['ВыгрузкаНаСклад'] = pd.to_datetime(supplies['ВыгрузкаНаСклад'])
        supplies = supplies.rename(columns={
            'Склад': 'storage_id',
            'Штабель': 'stack_id',
            'На склад, тн': 'mass_tons'
        })
        # Агрегируем по штабелю
        supplies_agg = supplies.groupby(['storage_id', 'stack_id']).agg({
            'mass_tons': 'sum',
            'ВыгрузкаНаСклад': 'min'
        }).reset_index()
        supplies_agg = supplies_agg.rename(columns={'ВыгрузкаНаСклад': 'first_unload_date'})
        print(f"  ✓ Поставки: {len(supplies_agg)} штабелей")
        
        # 4. Weather - влажность и ветер
        weather_files = list(self.data_dir.glob("weather_data_*.csv"))
        if weather_files:
            weather_dfs = []
            for f in weather_files:
                df = pd.read_csv(f, encoding='utf-8')
                weather_dfs.append(df)
            weather = pd.concat(weather_dfs, ignore_index=True)
            weather['date'] = pd.to_datetime(weather['date'])
            # Агрегируем по дню
            weather_daily = weather.groupby(weather['date'].dt.date).agg({
                't': 'mean',
                'humidity': 'mean',
                'v_avg': 'mean',
                'precipitation': 'sum'
            }).reset_index()
            weather_daily['date'] = pd.to_datetime(weather_daily['date'])
            weather_daily = weather_daily.rename(columns={
                't': 'air_temp',
                'v_avg': 'wind_speed'
            })
            print(f"  ✓ Погода: {len(weather_daily)} дней")
        else:
            weather_daily = pd.DataFrame()
        
        # ОБЪЕДИНЕНИЕ
        print("\n🔗 Объединение данных...")
        
        # Normalize IDs
        for df in [fires, temp, supplies_agg]:
            df['storage_id'] = df['storage_id'].astype(str).str.strip()
            df['stack_id'] = df['stack_id'].astype(str).str.strip()
        
        # Температуры + поставки
        data = temp.merge(supplies_agg, on=['storage_id', 'stack_id'], how='left')
        
        # + Погода (по дате замера)
        if not weather_daily.empty:
            data['weather_date'] = data['measurement_date'].dt.date
            data['weather_date'] = pd.to_datetime(data['weather_date'])
            data = data.merge(weather_daily, left_on='weather_date', right_on='date', how='left')
            data = data.drop(columns=['date', 'weather_date'])
        
        # + Пожары (привязка к БЛИЖАЙШЕМУ будущему пожару)
        print("  🔗 Привязываем измерения к ближайшим пожарам...")
        
        # Каждое измерение должно привязываться к ближайшему БУДУЩЕМУ пожару
        data_with_fires = []
        
        for (storage, stack), temp_group in data.groupby(['storage_id', 'stack_id']):
            # Пожары этого штабеля
            stack_fires = fires[
                (fires['storage_id'] == storage) & 
                (fires['stack_id'] == stack)
            ].sort_values('fire_date')
            
            if len(stack_fires) == 0:
                continue
            
            # Для каждого измерения находим ближайший будущий пожар
            for _, measurement in temp_group.iterrows():
                meas_date = measurement['measurement_date']
                
                # Пожары после этого измерения
                future_fires = stack_fires[stack_fires['fire_date'] > meas_date]
                
                if len(future_fires) > 0:
                    # Берем БЛИЖАЙШИЙ пожар
                    nearest_fire = future_fires.iloc[0]
                    
                    measurement['fire_date'] = nearest_fire['fire_date']
                    measurement['formation_date'] = nearest_fire['formation_date']
                    
                    data_with_fires.append(measurement)
        
        if not data_with_fires:
            raise ValueError("Нет данных после привязки к пожарам!")
        
        data = pd.DataFrame(data_with_fires)
        
        # Целевая переменная: дни до пожара
        data['days_to_fire'] = (data['fire_date'] - data['measurement_date']).dt.days
        
        # Дни хранения
        data['storage_days'] = (data['measurement_date'] - data['formation_date']).dt.days
        
        # Фильтруем: только измерения перед пожаром (0-60 дней)
        data = data[
            (data['days_to_fire'] >= 0) & 
            (data['days_to_fire'] <= 60)
        ].copy()
        
        print(f"  ✓ Итого обучающих примеров: {len(data)}")
        
        return data
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Создание ПРОСТЫХ и ПОНЯТНЫХ признаков.
        Только то, что реально влияет на самовозгорание.
        """
        df = df.copy()
        
        # Заполнение пропусков
        df['max_temp'] = df['max_temp'].fillna(df['max_temp'].median())
        df['mass_tons'] = df['mass_tons'].fillna(5000)
        df['storage_days'] = df['storage_days'].fillna(0)
        df['humidity'] = df['humidity'].fillna(50)
        df['air_temp'] = df['air_temp'].fillna(15)
        df['wind_speed'] = df['wind_speed'].fillna(3)
        df['precipitation'] = df['precipitation'].fillna(0)
        
        # ===== КЛЮЧЕВЫЕ ПРИЗНАКИ =====
        
        # 1. Температура (ГЛАВНЫЙ фактор)
        df['temp'] = df['max_temp']
        df['temp_squared'] = df['max_temp'] ** 2
        df['temp_cubed'] = df['max_temp'] ** 3
        
        # 2. Возраст штабеля
        df['age_days'] = df['storage_days']
        df['age_weeks'] = df['storage_days'] / 7
        df['age_squared'] = df['storage_days'] ** 2
        
        # 3. Масса (больше масса = медленнее остывает)
        df['mass'] = df['mass_tons']
        df['log_mass'] = np.log1p(df['mass_tons'])
        
        # 4. Влажность (сухой уголь = опаснее)
        df['humidity_pct'] = df['humidity']
        df['dryness'] = 100 - df['humidity']
        
        # 5. Ветер (усиливает окисление)
        df['wind'] = df['wind_speed']
        
        # 6. Осадки (мокрый уголь = безопаснее)
        df['rain'] = df['precipitation']
        
        # ===== ВЗАИМОДЕЙСТВИЯ =====
        
        # Термическая опасность
        df['thermal_risk'] = df['max_temp'] * df['storage_days']
        
        # Эффект сухости
        df['dry_heat'] = df['max_temp'] * df['dryness']
        
        # Окисление
        df['oxidation'] = df['max_temp'] * df['wind_speed'] * (100 - df['humidity']) / 100
        
        # Тепловая инерция (большая масса дольше держит тепло)
        df['thermal_mass'] = df['max_temp'] * np.log1p(df['mass_tons'])
        
        # Время × масса
        df['age_mass'] = df['storage_days'] * np.log1p(df['mass_tons'])
        
        # Порог критической температуры
        df['critical_temp'] = (df['max_temp'] > 60).astype(int)
        df['high_temp'] = (df['max_temp'] > 45).astype(int)
        df['warm_temp'] = (df['max_temp'] > 35).astype(int)
        
        # Время хранения (опасные пороги)
        df['old_pile'] = (df['storage_days'] > 30).astype(int)
        df['very_old_pile'] = (df['storage_days'] > 60).astype(int)
        
        return df
    
    def get_feature_names(self) -> List[str]:
        """Список признаков для модели."""
        return [
            # Базовые
            'temp', 'temp_squared', 'temp_cubed',
            'age_days', 'age_weeks', 'age_squared',
            'mass', 'log_mass',
            'humidity_pct', 'dryness',
            'wind', 'rain',
            # Взаимодействия
            'thermal_risk', 'dry_heat', 'oxidation',
            'thermal_mass', 'age_mass',
            # Пороги
            'critical_temp', 'high_temp', 'warm_temp',
            'old_pile', 'very_old_pile'
        ]
    
    def train(self) -> Dict[str, Any]:
        """Обучение модели."""
        print("\n" + "="*70)
        print("🔥 ОБУЧЕНИЕ ПРОСТОЙ МОДЕЛИ")
        print("="*70)
        
        # Загрузка
        data = self.load_data()
        
        if len(data) < 50:
            raise ValueError(f"Слишком мало данных: {len(data)}")
        
        # Признаки
        print("\n🔧 Создание признаков...")
        data = self.create_features(data)
        
        feature_names = self.get_feature_names()
        X = data[feature_names].fillna(0)
        y = data['days_to_fire']
        
        print(f"  ✓ Признаков: {len(feature_names)}")
        print(f"  ✓ Примеров: {len(X)}")
        
        # Масштабирование
        X_scaled = self.scaler.fit_transform(X)
        
        # Модель - Random Forest с оптимальной регуляризацией
        print("\n🤖 Обучение Random Forest (оптимизированная)...")
        self.model = RandomForestRegressor(
            n_estimators=200,          # Больше деревьев
            max_depth=6,               # Немного глубже (было 3)
            min_samples_split=10,      # Меньше ограничений (было 20)
            min_samples_leaf=5,        # Меньше ограничений (было 10)
            max_features='sqrt',       # Корень из числа признаков
            random_state=42,
            n_jobs=-1
        )
        
        # Cross-validation
        tscv = TimeSeriesSplit(n_splits=5)
        cv_scores = []
        
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X_scaled), 1):
            X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            self.model.fit(X_train, y_train)
            y_pred = self.model.predict(X_val)
            
            # Метрики
            mae = np.mean(np.abs(y_pred - y_val))
            accuracy_2d = np.mean(np.abs(y_pred - y_val) <= 2) * 100
            
            cv_scores.append(accuracy_2d)
            print(f"  Fold {fold}: Accuracy ±2d = {accuracy_2d:.1f}%, MAE = {mae:.2f}")
        
        print(f"\n  ✓ Средняя CV Accuracy: {np.mean(cv_scores):.1f}%")
        
        # Финальное обучение
        print("\n💾 Финальное обучение...")
        self.model.fit(X_scaled, y)
        
        # Feature importance
        if hasattr(self.model, 'feature_importances_'):
            importance = pd.DataFrame({
                'feature': feature_names,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            print("\n🔍 ТОП-10 признаков:")
            print(importance.head(10).to_string(index=False))
        elif hasattr(self.model, 'coef_'):
            importance = pd.DataFrame({
                'feature': feature_names,
                'coefficient': np.abs(self.model.coef_)
            }).sort_values('coefficient', ascending=False)
            
            print("\n🔍 ТОП-10 признаков (по модулю коэффициента):")
            print(importance.head(10).to_string(index=False))
        
        # Сохранение
        print("\n💾 Сохранение модели...")
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': feature_names
        }, self.model_path)
        print(f"  ✓ Сохранено: {self.model_path}")
        
        # Метрики
        y_pred_train = self.model.predict(X_scaled)
        train_mae = np.mean(np.abs(y_pred_train - y))
        train_acc = np.mean(np.abs(y_pred_train - y) <= 2) * 100
        
        metrics = {
            'cv_accuracy': np.mean(cv_scores),
            'train_accuracy': train_acc,
            'train_mae': train_mae,
            'n_features': len(feature_names),
            'n_samples': len(X)
        }
        
        # Сохранение метрик
        with open(self.artifacts_dir / "simple_metrics.json", 'w') as f:
            json.dump(metrics, f, indent=2)
        
        print("\n" + "="*70)
        print(f"✅ ОБУЧЕНИЕ ЗАВЕРШЕНО!")
        print(f"  CV Accuracy ±2d: {metrics['cv_accuracy']:.1f}%")
        print(f"  Train Accuracy ±2d: {metrics['train_accuracy']:.1f}%")
        print(f"  Train MAE: {metrics['train_mae']:.2f} дней")
        print("="*70)
        
        return metrics
    
    def load_model(self):
        """Загрузка модели."""
        if not self.model_path.exists():
            raise FileNotFoundError("Модель не обучена! Запустите train()")
        
        data = joblib.load(self.model_path)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
    
    def predict(self, 
                storage_id: str,
                stack_id: str,
                max_temp: float,
                storage_days: int = 30,
                mass_tons: float = 5000,
                humidity: float = 50,
                air_temp: float = 15,
                wind_speed: float = 3,
                precipitation: float = 0) -> Dict[str, Any]:
        """
        Простое предсказание.
        
        Args:
            storage_id: ID склада
            stack_id: ID штабеля
            max_temp: Температура штабеля (°C)
            storage_days: Дней хранения
            mass_tons: Масса (тонн)
            humidity: Влажность (%)
            air_temp: Температура воздуха (°C)
            wind_speed: Скорость ветра (м/с)
            precipitation: Осадки (мм)
        """
        if self.model is None:
            self.load_model()
        
        # Валидация
        if max_temp < 0 or max_temp > 200:
            raise ValueError(f"Некорректная температура: {max_temp}°C")
        
        # Создание датафрейма
        df = pd.DataFrame([{
            'max_temp': max_temp,
            'storage_days': storage_days,
            'mass_tons': mass_tons,
            'humidity': humidity,
            'air_temp': air_temp,
            'wind_speed': wind_speed,
            'precipitation': precipitation
        }])
        
        # Признаки
        df = self.create_features(df)
        X = df[self.feature_names].fillna(0)
        X_scaled = self.scaler.transform(X)
        
        # Предсказание
        days_pred = self.model.predict(X_scaled)[0]
        days_pred = max(0, days_pred)  # Не может быть отрицательным
        
        # Уверенность (на основе температуры)
        if max_temp > 60:
            confidence = 0.9
        elif max_temp > 45:
            confidence = 0.75
        elif max_temp > 35:
            confidence = 0.6
        else:
            confidence = 0.4
        
        # Уровень риска
        if days_pred < 3:
            risk = "критический"
            risk_color = "red"
        elif days_pred < 7:
            risk = "высокий"
            risk_color = "orange"
        elif days_pred < 14:
            risk = "средний"
            risk_color = "yellow"
        elif days_pred < 30:
            risk = "низкий"
            risk_color = "green"
        else:
            risk = "минимальный"
            risk_color = "gray"
        
        # Дата возгорания
        fire_date = datetime.now() + timedelta(days=int(days_pred))
        
        return {
            'storage_id': storage_id,
            'stack_id': stack_id,
            'days_to_fire': round(days_pred, 1),
            'fire_date': fire_date.strftime('%Y-%m-%d'),
            'confidence': round(confidence, 2),
            'risk_level': risk,
            'risk_color': risk_color,
            'max_temp': max_temp,
            'storage_days': storage_days
        }

