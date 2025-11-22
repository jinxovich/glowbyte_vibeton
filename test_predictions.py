#!/usr/bin/env python3
"""
Тест предсказаний для разных температур.
Проверяем, что модель ведет себя логично.
"""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from ML.predictor import CoalCombustionPredictor

def test_temperature_predictions():
    """Тестируем предсказания для разных температур."""
    
    project_root = Path(__file__).parent
    data_dir = project_root / "data"
    artifacts_dir = project_root / "ML" / "artifacts"
    
    predictor = CoalCombustionPredictor(
        data_dir=data_dir,
        artifacts_dir=artifacts_dir
    )
    
    print("\n" + "="*70)
    print("🧪 ТЕСТ ПРЕДСКАЗАНИЙ ДЛЯ РАЗНЫХ ТЕМПЕРАТУР")
    print("="*70)
    
    # Тестовые температуры
    test_temps = [1, 20, 30, 40, 45, 46, 50, 60, 70]
    
    print("\n📊 Результаты:\n")
    print(f"{'Температура':<15} {'Прогноз (дней)':<20} {'Уверенность':<15} {'Уровень риска'}")
    print("-" * 70)
    
    for temp in test_temps:
        # Создаем тестовый датафрейм
        test_df = pd.DataFrame([{
            'storage_id': '11',
            'stack_id': '11',
            'measurement_date': '2026-07-18',
            'max_temperature': temp,
            'pile_age_days': 30,
            'stack_mass_tons': 5000,
            'weather_humidity': 22,
            'weather_temp': 13
        }])
        
        # Делаем предсказание
        results = predictor.predict(test_df)
        
        if results:
            result = results[0]
            days = result['predicted_ttf_days']
            confidence = result['confidence']
            risk = result['risk_level']
            
            # Цветовое форматирование
            if days < 7:
                color = "🔴"
            elif days < 14:
                color = "🟠"
            elif days < 30:
                color = "🟡"
            else:
                color = "🟢"
            
            print(f"{temp}°C{' '*11} {color} {days:>6.1f} дней{' '*9} {confidence*100:>5.1f}%{' '*9} {risk}")
    
    print("\n" + "="*70)
    print("✅ ПРОВЕРКА ЗАВЕРШЕНА")
    print("="*70)
    
    print("\n💡 ОЖИДАЕМОЕ ПОВЕДЕНИЕ:")
    print("   • Чем выше температура → тем меньше дней до пожара")
    print("   • Чем выше температура → тем выше уверенность")
    print("   • При temp < 10°C → предупреждение + замена на 30°C")
    print("   • Больше НЕТ принудительных override для 45-60°C\n")

if __name__ == "__main__":
    test_temperature_predictions()

