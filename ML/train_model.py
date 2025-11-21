#!/usr/bin/env python3
"""Скрипт для обучения модели."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ML.predictor import CoalCombustionPredictor


def main():
    """Главная функция."""
    # Пути
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    artifacts_dir = project_root / "ML" / "artifacts"
    
    print("🔥 Инициализация Coal Fire Prediction System...")
    print(f"  Data dir: {data_dir}")
    print(f"  Artifacts dir: {artifacts_dir}")
    
    # Создать предиктор
    predictor = CoalCombustionPredictor(
        data_dir=data_dir,
        artifacts_dir=artifacts_dir
    )
    
    # Обучить модель
    metrics = predictor.train()
    
    print("\n" + "="*60)
    print("✅ ОБУЧЕНИЕ ЗАВЕРШЕНО УСПЕШНО!")
    print("="*60)
    print(f"\n📊 Главные метрики:")
    print(f"  • Accuracy (±2 дня): {metrics['accuracy_2days']:.2%}")
    print(f"  • MAE: {metrics['mae']:.2f} дней")
    print(f"  • RMSE: {metrics['rmse']:.2f} дней")
    print(f"\n💾 Модель сохранена в: {artifacts_dir / 'models' / 'coal_fire_model.pkl'}")
    print(f"📈 Метрики сохранены в: {artifacts_dir / 'training_metrics.json'}")
    
    if metrics['kpi_achieved']:
        print(f"\n🎉 KPI достигнут! Точность >= 70%")
    else:
        print(f"\n⚠️  KPI не достигнут. Попробуйте:")
        print(f"  • Добавить больше данных")
        print(f"  • Настроить гиперпараметры")
        print(f"  • Добавить новые признаки")


if __name__ == "__main__":
    main()

