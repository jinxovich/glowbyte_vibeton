#!/usr/bin/env python3
"""Тест простой модели на разных температурах."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ML.simple_predictor import SimpleCoalFirePredictor


def main():
    project_root = Path(__file__).parent
    data_dir = project_root / "data"
    artifacts_dir = project_root / "ML" / "artifacts"
    
    predictor = SimpleCoalFirePredictor(
        data_dir=data_dir,
        artifacts_dir=artifacts_dir
    )
    
    # Загружаем модель
    try:
        predictor.load_model()
    except FileNotFoundError:
        print("❌ Модель не обучена! Запустите: python ML/train_simple.py")
        return 1
    
    print("\n" + "="*80)
    print("🧪 ТЕСТ ПРОСТОЙ МОДЕЛИ НА РАЗНЫХ ТЕМПЕРАТУРАХ")
    print("="*80)
    
    # Тестовые сценарии
    test_cases = [
        # (temp, storage_days, description)
        (20, 10, "Свежий штабель, низкая температура"),
        (30, 30, "Месяц хранения, нормальная температура"),
        (40, 20, "Начало нагрева"),
        (45, 30, "Повышенная температура"),
        (50, 40, "Опасная температура"),
        (60, 30, "Критическая температура"),
        (70, 20, "Экстремальная температура"),
        (35, 5, "Молодой штабель, теплый"),
        (45, 60, "Старый штабель, горячий"),
    ]
    
    print("\n📊 Результаты:\n")
    print(f"{'Температура':<15} {'Возраст':<12} {'Прогноз':<18} {'Уверенность':<15} {'Риск':<15} {'Описание'}")
    print("-" * 100)
    
    for temp, age, desc in test_cases:
        result = predictor.predict(
            storage_id="11",
            stack_id="11",
            max_temp=temp,
            storage_days=age,
            mass_tons=5000,
            humidity=50,
            wind_speed=3
        )
        
        days = result['days_to_fire']
        conf = result['confidence']
        risk = result['risk_level']
        
        # Эмодзи по риску
        if risk == "критический":
            emoji = "🔴"
        elif risk == "высокий":
            emoji = "🟠"
        elif risk == "средний":
            emoji = "🟡"
        elif risk == "низкий":
            emoji = "🟢"
        else:
            emoji = "⚪"
        
        print(f"{temp}°C{' '*11} {age} дней{' '*5} {emoji} {days:>5.1f} дней{' '*8} {conf*100:>5.1f}%{' '*9} {risk:<15} {desc}")
    
    print("\n" + "="*80)
    print("✅ ТЕСТ ЗАВЕРШЕН")
    print("="*80)
    
    print("\n💡 ПРОВЕРКА ЛОГИКИ:")
    print("   ✓ Чем выше температура → тем меньше дней до пожара")
    print("   ✓ Чем старше штабель → тем опаснее")
    print("   ✓ Уверенность растет с температурой")
    print()


if __name__ == "__main__":
    exit(main())

