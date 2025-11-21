"""Аналитика и дополнительные endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from ..ml import get_predictor, read_prediction_history
from ..config import get_config

router = APIRouter(tags=["analytics"])


class CalendarItem(BaseModel):
    """Элемент календаря с прогнозами."""
    date: str
    count: int
    risk_level: str
    stockpiles: List[Dict[str, Any]]


class MetricsSummary(BaseModel):
    """Сводка по метрикам."""
    accuracy_2days: float
    mae: float
    rmse: float
    kpi_achieved: bool
    total_predictions: int
    trained_at: str | None


@router.get("/api/calendar", response_model=List[CalendarItem])
def get_calendar_data(predictor=Depends(get_predictor)) -> List[CalendarItem]:
    """
    Получить данные для календаря прогнозов.
    
    Returns:
        Список дат с количеством прогнозируемых возгораний
    """
    history = read_prediction_history(limit=1000)
    
    # Группировать по датам
    calendar_data = defaultdict(lambda: {
        'count': 0,
        'stockpiles': [],
        'max_risk': 0
    })
    
    risk_levels = {
        'критический': 5,
        'высокий': 4,
        'средний': 3,
        'низкий': 2,
        'минимальный': 1
    }
    
    for pred in history:
        date = pred['predicted_combustion_date']
        risk_level = pred.get('risk_level', 'минимальный')
        
        calendar_data[date]['count'] += 1
        calendar_data[date]['stockpiles'].append({
            'storage_id': pred['storage_id'],
            'stack_id': pred['stack_id'],
            'confidence': pred.get('confidence', 0)
        })
        
        # Обновить максимальный уровень риска для дня
        current_risk = risk_levels.get(risk_level, 1)
        if current_risk > calendar_data[date]['max_risk']:
            calendar_data[date]['max_risk'] = current_risk
    
    # Сформировать результат
    result = []
    for date, data in sorted(calendar_data.items()):
        # Определить уровень риска для дня
        max_risk_num = data['max_risk']
        risk_level = next(
            (level for level, num in risk_levels.items() if num == max_risk_num),
            'минимальный'
        )
        
        result.append(CalendarItem(
            date=date,
            count=data['count'],
            risk_level=risk_level,
            stockpiles=data['stockpiles']
        ))
    
    return result


@router.get("/api/metrics", response_model=MetricsSummary)
def get_metrics_summary(predictor=Depends(get_predictor)) -> MetricsSummary:
    """
    Получить сводку по метрикам модели.
    
    Returns:
        Основные метрики качества модели
    """
    metrics = predictor.load_metrics()
    history = read_prediction_history()
    
    if not metrics:
        return MetricsSummary(
            accuracy_2days=0.0,
            mae=0.0,
            rmse=0.0,
            kpi_achieved=False,
            total_predictions=len(history),
            trained_at=None
        )
    
    return MetricsSummary(
        accuracy_2days=metrics.get('accuracy_2days', 0.0),
        mae=metrics.get('mae', 0.0),
        rmse=metrics.get('rmse', 0.0),
        kpi_achieved=metrics.get('kpi_achieved', False),
        total_predictions=len(history),
        trained_at=metrics.get('trained_at')
    )


@router.get("/api/stockpile/{storage_id}/{stack_id}")
def get_stockpile_details(
    storage_id: str,
    stack_id: str,
    predictor=Depends(get_predictor)
) -> Dict[str, Any]:
    """
    Получить детальную информацию по конкретному штабелю.
    
    Args:
        storage_id: ID склада
        stack_id: ID штабеля
        
    Returns:
        История измерений и прогнозов для штабеля
    """
    history = read_prediction_history(limit=1000)
    
    # Фильтровать по штабелю
    stockpile_history = [
        pred for pred in history
        if pred['storage_id'] == storage_id and pred['stack_id'] == stack_id
    ]
    
    if not stockpile_history:
        return {
            'storage_id': storage_id,
            'stack_id': stack_id,
            'found': False,
            'message': 'Штабель не найден в истории'
        }
    
    # Получить последний прогноз
    latest = stockpile_history[-1]
    
    # Подготовить временной ряд
    timeseries = [
        {
            'date': pred['measurement_date'],
            'predicted_days': pred['predicted_ttf_days'],
            'confidence': pred.get('confidence', 0),
            'max_temperature': pred.get('max_temperature', 0)
        }
        for pred in stockpile_history
    ]
    
    return {
        'storage_id': storage_id,
        'stack_id': stack_id,
        'found': True,
        'latest_prediction': latest,
        'total_measurements': len(stockpile_history),
        'timeseries': timeseries,
        'risk_trend': 'increasing' if len(timeseries) > 1 and 
                      timeseries[-1]['predicted_days'] < timeseries[0]['predicted_days']
                      else 'stable'
    }


@router.get("/api/dashboard")
def get_dashboard_data(predictor=Depends(get_predictor)) -> Dict[str, Any]:
    """
    Получить данные для главного dashboard.
    
    Returns:
        Агрегированные данные для отображения на главной странице
    """
    metrics = predictor.load_metrics()
    history = read_prediction_history(limit=1000)
    
    # Статистика по уровням риска
    risk_counts = {
        'критический': 0,
        'высокий': 0,
        'средний': 0,
        'низкий': 0,
        'минимальный': 0
    }
    
    for pred in history:
        risk_level = pred.get('risk_level', 'минимальный')
        if risk_level in risk_counts:
            risk_counts[risk_level] += 1
    
    # Статистика по складам
    storages = defaultdict(int)
    for pred in history:
        storages[pred['storage_id']] += 1
    
    # Ближайшие возгорания (следующие 7 дней)
    today = datetime.now().date()
    upcoming_fires = []
    
    for pred in history:
        fire_date = datetime.strptime(pred['predicted_combustion_date'], '%Y-%m-%d').date()
        days_until = (fire_date - today).days
        
        if 0 <= days_until <= 7:
            upcoming_fires.append({
                'storage_id': pred['storage_id'],
                'stack_id': pred['stack_id'],
                'date': pred['predicted_combustion_date'],
                'days_until': days_until,
                'risk_level': pred.get('risk_level', 'минимальный'),
                'confidence': pred.get('confidence', 0)
            })
    
    # Сортировать по близости
    upcoming_fires.sort(key=lambda x: x['days_until'])
    
    return {
        'metrics': {
            'accuracy_2days': metrics.get('accuracy_2days', 0.0),
            'mae': metrics.get('mae', 0.0),
            'rmse': metrics.get('rmse', 0.0),
            'kpi_achieved': metrics.get('kpi_achieved', False)
        },
        'statistics': {
            'total_predictions': len(history),
            'risk_distribution': risk_counts,
            'storages': dict(storages),
            'at_risk_count': risk_counts['критический'] + risk_counts['высокий']
        },
        'upcoming_fires': upcoming_fires[:10],  # Топ-10
        'trained_at': metrics.get('trained_at')
    }


__all__ = ["router"]

