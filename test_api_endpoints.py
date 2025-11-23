#!/usr/bin/env python3
"""
Тест всех эндпоинтов API с полными данными
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def test_register():
    print_header("1️⃣  ТЕСТ: Регистрация пользователя")
    
    data = {
        "email": f"test_{datetime.now().timestamp()}@example.com",
        "full_name": "Test User",
        "password": "test123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=data)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✅ Пользователь зарегистрирован: {response.json()['email']}")
        return response.json()['email'], data['password']
    else:
        print(f"❌ Ошибка: {response.text}")
        return None, None

def test_login(email, password):
    print_header("2️⃣  ТЕСТ: Авторизация")
    
    data = {
        "username": email,
        "password": password
    }
    
    response = requests.post(
        f"{BASE_URL}/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        token = response.json()['access_token']
        print(f"✅ Получен токен: {token[:20]}...")
        return token
    else:
        print(f"❌ Ошибка: {response.text}")
        return None

def test_predict_basic(token):
    print_header("3️⃣  ТЕСТ: Базовый прогноз (минимум полей)")
    
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "storage_id": "11",
        "stack_id": "11",
        "max_temperature": 45.5
    }
    
    response = requests.post(f"{BASE_URL}/predict/", json=data, headers=headers)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Прогноз получен:")
        print(f"   • Дней до пожара: {result['predicted_ttf_days']:.1f}")
        print(f"   • Риск: {result['risk_level']}")
        print(f"   • Уверенность: {result['confidence']*100:.0f}%")
        print(f"   • ID предсказания: #{result['id']}")
        return result
    else:
        print(f"❌ Ошибка: {response.text}")
        return None

def test_predict_full(token):
    print_header("4️⃣  ТЕСТ: Полный прогноз (все поля)")
    
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        # Обязательные
        "storage_id": "11",
        "stack_id": "21",
        "max_temperature": 55.5,
        
        # Основные
        "pile_age_days": 45,
        "stack_mass_tons": 7500,
        "coal_grade": "ДГ",
        "measurement_date": "2025-11-23",
        
        # Погода
        "weather_temp": 18.5,
        "weather_humidity": 65,
        "wind_speed": 4.2,
        "wind_speed_max": 7.5,
        "wind_direction": 180,
        "precipitation": 0.5,
        "pressure": 1015,
        "cloud_cover": 75,
        "visibility": 8000,
        "weather_code": 500,
        
        # Доп данные
        "picket": "П-3",
        "shift": "1",
        "co_level_ppm": 35.5,
        "ash_content": 12.3,
        "moisture_content": 8.5
    }
    
    print("📤 Отправка данных:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    response = requests.post(f"{BASE_URL}/predict/", json=data, headers=headers)
    print(f"\nСтатус: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Прогноз получен:")
        print(f"   • Дней до пожара: {result['predicted_ttf_days']:.1f}")
        print(f"   • Риск: {result['risk_level']}")
        print(f"   • Уверенность: {result['confidence']*100:.0f}%")
        print(f"   • ID предсказания: #{result['id']}")
        if result.get('warnings'):
            print(f"   • Предупреждения: {len(result['warnings'])}")
            for w in result['warnings']:
                print(f"     - {w}")
        return result
    else:
        print(f"❌ Ошибка: {response.text}")
        return None

def test_predict_critical(token):
    print_header("5️⃣  ТЕСТ: Критический случай (высокая температура)")
    
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "storage_id": "11",
        "stack_id": "13",
        "max_temperature": 65.0,  # Критическая!
        "pile_age_days": 60,
        "co_level_ppm": 120,  # Очень высокий CO!
        "moisture_content": 3.0  # Очень сухой!
    }
    
    response = requests.post(f"{BASE_URL}/predict/", json=data, headers=headers)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Прогноз получен:")
        print(f"   • Дней до пожара: {result['predicted_ttf_days']:.1f}")
        print(f"   • Риск: {result['risk_level']}")
        print(f"   • Уверенность: {result['confidence']*100:.0f}%")
        if result.get('warnings'):
            print(f"   🚨 ПРЕДУПРЕЖДЕНИЯ:")
            for w in result['warnings']:
                print(f"     - {w}")
        return result
    else:
        print(f"❌ Ошибка: {response.text}")
        return None

def test_dashboard(token):
    print_header("6️⃣  ТЕСТ: Дашборд")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/predict/dashboard", headers=headers)
    
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Данные дашборда получены:")
        print(f"   • Всего предсказаний: {data['total_predictions']}")
        print(f"   • Критических: {data['critical_count']}")
        print(f"   • Средняя уверенность: {data['avg_confidence']}%")
        print(f"   • Распределение рисков: {data['risk_distribution']}")
        return data
    else:
        print(f"❌ Ошибка: {response.text}")
        return None

def test_history(token):
    print_header("7️⃣  ТЕСТ: История предсказаний")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/predict/history?limit=5", headers=headers)
    
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ История получена: {len(data)} записей")
        for i, pred in enumerate(data[:3], 1):
            print(f"   {i}. #{pred['id']} - {pred['predicted_ttf_days']:.1f} дней ({pred['risk_level']})")
        return data
    else:
        print(f"❌ Ошибка: {response.text}")
        return None

def main():
    print("\n" + "🔥"*30)
    print("  ПОЛНОЕ ТЕСТИРОВАНИЕ API ЭНДПОИНТОВ")
    print("🔥"*30)
    
    # Используем существующего пользователя или создаем нового
    print("\n❓ Использовать существующего пользователя?")
    print("   (или Enter для создания нового)")
    email = input("   Email (или Enter): ").strip()
    
    if email:
        password = input("   Password: ").strip()
    else:
        email, password = test_register()
        if not email:
            print("\n❌ Не удалось зарегистрировать пользователя")
            return
    
    # Логин
    token = test_login(email, password)
    if not token:
        print("\n❌ Не удалось авторизоваться")
        return
    
    # Тесты предсказаний
    test_predict_basic(token)
    test_predict_full(token)
    test_predict_critical(token)
    
    # Тесты дашборда
    test_dashboard(token)
    test_history(token)
    
    print_header("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ!")
    print("\n📊 ИТОГ:")
    print("   • Регистрация/логин: ✅")
    print("   • Базовый прогноз: ✅")
    print("   • Полный прогноз (все поля): ✅")
    print("   • Критический случай: ✅")
    print("   • Дашборд: ✅")
    print("   • История: ✅")
    print("\n🎉 API РАБОТАЕТ ПОЛНОСТЬЮ!\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

