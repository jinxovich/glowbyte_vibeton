import sys
from pathlib import Path

# Добавляем путь к корню проекта, чтобы питон видел папку ML
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from ML.predictor import CoalCombustionPredictor
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедись, что ты запускаешь скрипт из корневой папки или из папки ML.")
    sys.exit(1)

def main():
    # Определяем пути
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    artifacts_dir = project_root / "ML" / "artifacts"
    
    print(f"📂 Данные: {data_dir}")
    print(f"💾 Артефакты: {artifacts_dir}")
    
    if not data_dir.exists():
        print(f"❌ Папка с данными не найдена: {data_dir}")
        return

    try:
        # 1. Инициализация
        predictor = CoalCombustionPredictor(
            data_dir=data_dir,
            artifacts_dir=artifacts_dir
        )
        
        # 2. Запуск обучения
        metrics = predictor.train()
        
        print("\n" + "="*60)
        print("✅ ОБУЧЕНИЕ УСПЕШНО ЗАВЕРШЕНО")
        print(f"🎯 Точность (±2 дня): {metrics.get('accuracy_2days', 0):.2%}")
        print("="*60)

    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()