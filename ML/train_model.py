print("🔵 [1] ЗАПУСК СКРИПТА... (Если ты это видишь, Python работает)")

import sys
import os
print(f"🔵 [2] Библиотеки sys/os загружены. Python: {sys.version}")

from pathlib import Path
print("🔵 [3] Pathlib загружен")

# Add parent directory to path
current_path = Path(__file__).parent.parent
sys.path.insert(0, str(current_path))
print(f"🔵 [4] Путь добавлен в sys.path: {current_path}")

try:
    print("🔵 [5] Попытка импорта CoalCombustionPredictor...")
    from ML.predictor import CoalCombustionPredictor
    print("✅ [6] УСПЕШНО импортирован CoalCombustionPredictor")
except ImportError as e:
    print(f"❌ [CRITICAL] Ошибка импорта: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ [CRITICAL] Лютая ошибка при импорте: {e}")
    sys.exit(1)

def main():
    print("🔵 [7] Вход в функцию main()")
    
    # Пути
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    artifacts_dir = project_root / "ML" / "artifacts"
    
    print(f"   Data dir: {data_dir}")
    print(f"   Artifacts dir: {artifacts_dir}")
    
    if not data_dir.exists():
        print("❌ [ERROR] Папка data не найдена!")
        return

    print("🔵 [8] Инициализация предиктора...")
    try:
        predictor = CoalCombustionPredictor(
            data_dir=data_dir,
            artifacts_dir=artifacts_dir
        )
        print("✅ [9] Предиктор создан")
    except Exception as e:
        print(f"❌ [ERROR] Ошибка при создании предиктора: {e}")
        return
    
    print("🔵 [10] Запуск обучения...")
    try:
        metrics = predictor.train()
        print("✅ [11] Обучение завершено!")
    except Exception as e:
        print(f"❌ [ERROR] Ошибка во время обучения: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "="*60)
    print("✅ ВСЕ ОТРАБОТАЛО")
    print("="*60)

if __name__ == "__main__":
    print("🔵 [0] Проверка __name__ == __main__ пройдена")
    main()