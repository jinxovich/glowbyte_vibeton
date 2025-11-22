#!/usr/bin/env python3
"""Обучение простой модели."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ML.simple_predictor import SimpleCoalFirePredictor


def main():
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    artifacts_dir = project_root / "ML" / "artifacts"
    
    predictor = SimpleCoalFirePredictor(
        data_dir=data_dir,
        artifacts_dir=artifacts_dir
    )
    
    try:
        metrics = predictor.train()
        print("\n✅ Готово!")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

