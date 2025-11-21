import { useState, useEffect } from 'react';
import { Calendar as CalendarIcon } from 'lucide-react';
import { getCalendar } from '../lib/api';
import type { CalendarItem } from '../types';
import { getRiskColor } from '../lib/utils';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, getDay, addMonths, subMonths } from 'date-fns';
import { ru } from 'date-fns/locale';

export default function Calendar() {
  const [data, setData] = useState<CalendarItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentMonth, setCurrentMonth] = useState(new Date());

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const calendarData = await getCalendar();
      setData(calendarData);
    } catch (error) {
      console.error('Failed to load calendar:', error);
    } finally {
      setLoading(false);
    }
  };

  const monthStart = startOfMonth(currentMonth);
  const monthEnd = endOfMonth(currentMonth);
  const monthDays = eachDayOfInterval({ start: monthStart, end: monthEnd });

  // Get first day of month (0 = Sunday, 1 = Monday, etc.)
  const startDay = (getDay(monthStart) + 6) % 7; // Convert to Monday = 0

  // Create calendar grid with empty cells for previous month days
  const calendarGrid = [
    ...Array(startDay).fill(null),
    ...monthDays,
  ];

  const getDayData = (date: Date): CalendarItem | undefined => {
    const dateStr = format(date, 'yyyy-MM-dd');
    return data.find(item => item.date === dateStr);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <CalendarIcon className="h-6 w-6 text-red-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900">
              Календарь прогнозируемых возгораний
            </h2>
          </div>

          <div className="flex items-center space-x-4">
            <button
              onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
              className="px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              ←
            </button>
            <span className="font-semibold text-lg">
              {format(currentMonth, 'LLLL yyyy', { locale: ru })}
            </span>
            <button
              onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
              className="px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              →
            </button>
          </div>
        </div>

        {/* Weekday headers */}
        <div className="grid grid-cols-7 gap-2 mb-2">
          {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].map((day) => (
            <div key={day} className="text-center font-semibold text-gray-600 py-2">
              {day}
            </div>
          ))}
        </div>

        {/* Calendar grid */}
        <div className="grid grid-cols-7 gap-2">
          {calendarGrid.map((day, index) => {
            if (!day) {
              return <div key={`empty-${index}`} className="aspect-square" />;
            }

            const dayData = getDayData(day);
            const isToday = format(day, 'yyyy-MM-dd') === format(new Date(), 'yyyy-MM-dd');

            return (
              <div
                key={index}
                className={`
                  aspect-square p-2 rounded-lg border-2 transition-all cursor-pointer
                  ${dayData
                    ? `${getRiskColor(dayData.risk_level)} border-transparent hover:scale-105`
                    : 'bg-white border-gray-200 hover:border-gray-300'
                  }
                  ${isToday ? 'ring-2 ring-blue-500' : ''}
                `}
                title={dayData ? `${dayData.count} прогноз(ов) - ${dayData.risk_level}` : ''}
              >
                <div className="h-full flex flex-col">
                  <span className={`text-sm font-semibold ${dayData ? '' : 'text-gray-900'}`}>
                    {format(day, 'd')}
                  </span>
                  {dayData && (
                    <div className="flex-1 flex items-center justify-center">
                      <span className="text-xs font-bold">
                        🔥 {dayData.count}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Legend */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <p className="text-sm font-semibold text-gray-700 mb-3">Уровни риска:</p>
          <div className="flex flex-wrap gap-4">
            {[
              { level: 'критический', label: 'Критический (< 3 дн.)' },
              { level: 'высокий', label: 'Высокий (3-7 дн.)' },
              { level: 'средний', label: 'Средний (7-14 дн.)' },
              { level: 'низкий', label: 'Низкий (14-30 дн.)' },
              { level: 'минимальный', label: 'Минимальный (> 30 дн.)' },
            ].map((item) => (
              <div key={item.level} className="flex items-center space-x-2">
                <div className={`w-4 h-4 rounded ${getRiskColor(item.level as any)}`} />
                <span className="text-sm text-gray-600">{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

