"""Оценка качества модели."""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, Any


def evaluate_model(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
    """
    Вычислить все метрики качества модели.
    
    Args:
        y_true: Реальные значения (дни до возгорания)
        y_pred: Предсказанные значения
        
    Returns:
        Словарь с метриками
    """
    # Основные метрики
    errors = y_pred - y_true
    abs_errors = np.abs(errors)
    
    # Accuracy ±2 дня (KPI)
    accuracy_2days = np.mean(abs_errors <= 2)
    
    # MAE и RMSE
    mae = np.mean(abs_errors)
    rmse = np.sqrt(np.mean(errors ** 2))
    
    # MAPE (Mean Absolute Percentage Error) - только для значений > 5 дней
    # Избегаем деления на ноль и взрыва MAPE для малых значений
    mape_mask = y_true > 5
    if np.sum(mape_mask) > 0:
        mape = np.mean(np.abs(errors[mape_mask] / y_true[mape_mask])) * 100
    else:
        mape = 0.0
    
    # Медианная абсолютная ошибка
    median_ae = np.median(abs_errors)
    
    # Процентили ошибок
    percentile_50 = np.percentile(abs_errors, 50)
    percentile_90 = np.percentile(abs_errors, 90)
    percentile_95 = np.percentile(abs_errors, 95)
    
    # Confusion matrix для ±2 дней
    within_2days = abs_errors <= 2
    beyond_2days = abs_errors > 2
    
    # True Positive: предсказано правильно (в пределах ±2 дней)
    tp = np.sum(within_2days)
    
    # False Positive: предсказано неправильно (больше ±2 дней)
    fp = np.sum(beyond_2days)
    
    # Precision и Recall (для бинарной классификации "правильно/неправильно")
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    
    # Для регрессии recall = accuracy
    recall = accuracy_2days
    
    # F1-score
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    # R² (коэффициент детерминации)
    ss_res = np.sum(errors ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    # Процент предсказаний в разных диапазонах
    within_1day = np.mean(abs_errors <= 1)
    within_3days = np.mean(abs_errors <= 3)
    within_5days = np.mean(abs_errors <= 5)
    within_7days = np.mean(abs_errors <= 7)
    
    return {
        # Главный KPI
        'accuracy_2days': float(accuracy_2days),
        'kpi_achieved': accuracy_2days >= 0.70,
        
        # Основные метрики
        'mae': float(mae),
        'rmse': float(rmse),
        'mape': float(mape),
        'median_ae': float(median_ae),
        'r2_score': float(r2),
        
        # Процентили
        'p50_error': float(percentile_50),
        'p90_error': float(percentile_90),
        'p95_error': float(percentile_95),
        
        # Классификационные метрики
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        
        # Confusion matrix
        'confusion_matrix': {
            'correct_predictions': int(tp),
            'incorrect_predictions': int(fp),
            'total': int(len(y_true))
        },
        
        # Точность в разных диапазонах
        'accuracy_breakdown': {
            '±1_day': float(within_1day),
            '±2_days': float(accuracy_2days),
            '±3_days': float(within_3days),
            '±5_days': float(within_5days),
            '±7_days': float(within_7days)
        },
        
        # Статистика ошибок
        'error_statistics': {
            'mean_error': float(np.mean(errors)),
            'std_error': float(np.std(errors)),
            'min_error': float(np.min(errors)),
            'max_error': float(np.max(errors)),
            'mean_abs_error': float(mae)
        }
    }


def print_metrics_report(metrics: Dict[str, Any]) -> None:
    """Красиво вывести отчет по метрикам."""
    print("\n" + "="*60)
    print("📊 ОТЧЕТ ПО МЕТРИКАМ МОДЕЛИ")
    print("="*60)
    
    # KPI
    print(f"\n🎯 ГЛАВНЫЙ KPI:")
    print(f"  Accuracy (±2 дня): {metrics['accuracy_2days']:.2%}")
    if metrics['kpi_achieved']:
        print(f"  ✅ KPI достигнут! (требуется >= 70%)")
    else:
        print(f"  ❌ KPI не достигнут (требуется >= 70%)")
    
    # Основные метрики
    print(f"\n📈 ОСНОВНЫЕ МЕТРИКИ:")
    print(f"  MAE (средняя абс. ошибка): {metrics['mae']:.2f} дней")
    print(f"  RMSE: {metrics['rmse']:.2f} дней")
    print(f"  Медианная ошибка: {metrics['median_ae']:.2f} дней")
    print(f"  R² score: {metrics['r2_score']:.4f}")
    
    # Точность в диапазонах
    print(f"\n🎯 ТОЧНОСТЬ В РАЗНЫХ ДИАПАЗОНАХ:")
    for key, value in metrics['accuracy_breakdown'].items():
        print(f"  {key}: {value:.2%}")
    
    # Процентили
    print(f"\n📊 ПРОЦЕНТИЛИ ОШИБОК:")
    print(f"  50% ошибок меньше: {metrics['p50_error']:.2f} дней")
    print(f"  90% ошибок меньше: {metrics['p90_error']:.2f} дней")
    print(f"  95% ошибок меньше: {metrics['p95_error']:.2f} дней")
    
    # Confusion matrix
    print(f"\n✅ CONFUSION MATRIX:")
    cm = metrics['confusion_matrix']
    print(f"  Правильных предсказаний: {cm['correct_predictions']}")
    print(f"  Неправильных предсказаний: {cm['incorrect_predictions']}")
    print(f"  Всего: {cm['total']}")
    
    print("\n" + "="*60)


__all__ = ["evaluate_model", "print_metrics_report"]

