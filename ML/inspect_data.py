#!/usr/bin/env python3
"""
Скрипт-детектив: Куда делись мои пожары?
Анализирует потерю данных на этапах объединения.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Добавляем путь для импорта модулей
sys.path.insert(0, str(Path(__file__).parent.parent))

from ML.data_preprocessor import DataPreprocessor

def analyze_data_loss():
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    
    print("🕵️‍♂️ НАЧИНАЕМ РАССЛЕДОВАНИЕ...")
    
    # 1. Загружаем сырые данные через препроцессор (чтобы ID нормализовались)
    pp = DataPreprocessor(data_dir)
    fires = pp.load_fires()
    temps = pp.load_temperature()
    
    print(f"\n1. ИСХОДНЫЕ ДАННЫЕ:")
    print(f"   🔥 Всего записей о пожарах (fires.csv): {len(fires)}")
    print(f"   🌡️ Всего записей температур (temperature.csv): {len(temps)}")
    
    # 2. Проверка совпадения ID (Склад + Штабель)
    # Создаем уникальные ключи (склад_штабель)
    fires['key'] = fires['storage_id'] + "_" + fires['stack_id']
    temps['key'] = temps['storage_id'] + "_" + temps['stack_id']
    
    fire_keys = set(fires['key'].unique())
    temp_keys = set(temps['key'].unique())
    
    common_keys = fire_keys.intersection(temp_keys)
    missing_keys = fire_keys - temp_keys
    
    print(f"\n2. ПРОВЕРКА СТЫКОВКИ ID:")
    print(f"   Уникальных штабелей в пожарах: {len(fire_keys)}")
    print(f"   Уникальных штабелей в температурах: {len(temp_keys)}")
    print(f"   ✅ Найдено совпадений: {len(common_keys)} (столько пожаров имеют хоть какие-то данные о температуре)")
    print(f"   ❌ Потеряно (нет температурных данных): {len(missing_keys)}")
    
    if len(missing_keys) > 0:
        print(f"   Пример потерянного ID: {list(missing_keys)[0]}")

    # 3. Анализ временных рядов (Самое важное!)
    print(f"\n3. АНАЛИЗ ВРЕМЕННЫХ ИНТЕРВАЛОВ (ГЛАВНАЯ ПРИЧИНА ПОТЕРЬ):")
    print("   Проверяем, есть ли данные о температуре за 30 дней ДО пожара...")
    
    # Объединяем только те, что совпали по ключам
    merged = temps.merge(
        fires[['storage_id', 'stack_id', 'fire_date']], 
        on=['storage_id', 'stack_id'], 
        how='inner'
    )
    
    # Считаем разницу в днях
    merged['days_diff'] = (merged['fire_date'] - merged['measurement_date']).dt.days
    
    # Группируем по каждому конкретному пожару (штабелю)
    # Нас интересует: сколько измерений попало в "зону риска" (0-30 дней до пожара)
    fire_stats = merged.groupby(['storage_id', 'stack_id']).agg({
        'days_diff': [
            ('total_measurements', 'count'),
            ('in_risk_zone', lambda x: ((x >= 0) & (x <= 30)).sum()),
            ('too_early', lambda x: (x > 30).sum()),
            ('after_fire', lambda x: (x < 0).sum()),
            ('min_days', 'min'),
            ('max_days', 'max')
        ]
    })
    fire_stats.columns = fire_stats.columns.droplevel(0)
    
    valid_fires = fire_stats[fire_stats['in_risk_zone'] > 0]
    empty_fires = fire_stats[fire_stats['in_risk_zone'] == 0]
    
    print(f"   📊 Из {len(common_keys)} штабелей с данными:")
    print(f"     ✅ Пригодны для обучения (есть замеры за 0-30 дней до пожара): {len(valid_fires)}")
    print(f"     ❌ Непригодны (нет замеров перед пожаром): {len(empty_fires)}")
    
    print(f"\n   🧐 ПОЧЕМУ ОНИ НЕПРИГОДНЫ (Анализ {len(empty_fires)} потерянных):")
    if len(empty_fires) > 0:
        early_only = empty_fires[empty_fires['too_early'] > 0]
        late_only = empty_fires[empty_fires['after_fire'] > 0]
        print(f"     • Замеры прекратились более чем за 30 дней до пожара: {len(early_only)}")
        print(f"     • Замеры начались только ПОСЛЕ пожара (ошибка дат?): {len(late_only)}")
        print(f"     • Пример 'упущенного' пожара:")
        print(empty_fires.head(1)[['min_days', 'max_days']])
    
    print(f"\n4. ПЛОТНОСТЬ ДАННЫХ:")
    avg_measurements = valid_fires['in_risk_zone'].mean()
    print(f"   В среднем у нас всего {avg_measurements:.1f} строк замеров на один пожар в зоне риска.")
    print("   (Это очень мало! XGBoost сложно учить динамику на 2 точках)")

if __name__ == "__main__":
    analyze_data_loss()