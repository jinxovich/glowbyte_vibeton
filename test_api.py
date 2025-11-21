#!/usr/bin/env python3
"""Quick API test script."""

import requests
import json
from datetime import datetime

API_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    print("Testing /health...")
    response = requests.get(f"{API_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_prediction():
    """Test prediction endpoint."""
    print("\nTesting /predict...")
    
    data = {
        "records": [
            {
                "storage_id": "3",
                "stack_id": "21",
                "measurement_date": datetime.now().isoformat(),
                "max_temperature": 45.5,
                "pile_age_days": 30,
                "stack_mass_tons": 5000,
                "weather_humidity": 60,
                "weather_temp": 20
            }
        ]
    }
    
    response = requests.post(f"{API_URL}/predict", json=data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()[0]
        print(f"✅ Prediction successful!")
        print(f"  Storage/Stack: {result['storage_id']}/{result['stack_id']}")
        print(f"  Predicted days until fire: {result['predicted_ttf_days']:.1f}")
        print(f"  Predicted date: {result['predicted_combustion_date']}")
        print(f"  Risk level: {result['risk_level']}")
        print(f"  Confidence: {result['confidence']:.2%}")
        return True
    else:
        print(f"❌ Prediction failed: {response.text}")
        return False

def test_metrics():
    """Test metrics endpoint."""
    print("\nTesting /api/metrics...")
    response = requests.get(f"{API_URL}/api/metrics")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        metrics = response.json()
        print(f"  Accuracy (±2 days): {metrics['accuracy_2days']:.2%}")
        print(f"  MAE: {metrics['mae']:.2f} days")
        print(f"  KPI Achieved: {'✅' if metrics['kpi_achieved'] else '❌'}")
        return True
    return False

if __name__ == "__main__":
    print("🔥 Testing Coal Fire Prediction API\n")
    print("="*50)
    
    success = True
    success = test_health() and success
    success = test_prediction() and success
    success = test_metrics() and success
    
    print("\n" + "="*50)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")

