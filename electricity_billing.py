import datetime
from pymongo import MongoClient
from typing import Dict, List
from config import DEFAULT_CONFIG 

class ElectricityBillingSystem:
    def __init__(self, config: Dict = None):
        try:
            self.client = MongoClient('mongodb://localhost:27017/')
            self.db = self.client['electricity_billing']
        except Exception as e:
            print(f"Помилка підключення до бази даних: {e}")
            raise

        self.config = config or DEFAULT_CONFIG
        self.meters_collection = self.db['meters']
        self.billing_history_collection = self.db['billing_history']

        self._create_indexes()

    def _create_indexes(self):
        self.meters_collection.create_index("meter_id", unique=True)
        self.billing_history_collection.create_index([("meter_id", 1), ("date", 1)])

    def add_new_meter(self, meter_id: str, day_reading: float, night_reading: float) -> Dict:
        if self.meters_collection.find_one({"meter_id": meter_id}):
            raise ValueError(f"Лічильник з ID {meter_id} вже існує. Неможливо додати повторно.")
        
        current_time = datetime.datetime.now()
        meter_data = {
            "meter_id": meter_id,
            "day_reading": day_reading,
            "night_reading": night_reading,
            "date": current_time,
            "created_at": current_time
        }
        self.meters_collection.insert_one(meter_data)

        billing_record = {
            "meter_id": meter_id,
            "date": current_time,
            "current_day_reading": day_reading,
            "current_night_reading": night_reading,
            "day_consumption": 0,
            "night_consumption": 0,
            "day_tariff": self.config['tariffs']['day'],
            "night_tariff": self.config['tariffs']['night'],
            "total_amount": 0.0,
            "notes": "Первинний запис при реєстрації лічильника"
        }
        self.billing_history_collection.insert_one(billing_record)

        return meter_data

    def update_meter_readings(self, meter_id: str, day_reading: float, night_reading: float) -> Dict:
        current_meter = self.meters_collection.find_one({"meter_id": meter_id})
        if not current_meter:
            raise ValueError(f"Лічильник з ID {meter_id} не знайдено")

        day_reset = day_reading < current_meter['day_reading']
        night_reset = night_reading < current_meter['night_reading']

        day_consumption = self._calculate_consumption(
            current_meter['day_reading'], day_reading, day_reset, self.config['reset_values']['day']
        )
        night_consumption = self._calculate_consumption(
            current_meter['night_reading'], night_reading, night_reset, self.config['reset_values']['night']
        )

        day_cost = day_consumption * self.config['tariffs']['day']
        night_cost = night_consumption * self.config['tariffs']['night']
        total_amount = round(day_cost + night_cost, 2)

        current_time = datetime.datetime.now()

        billing_record = {
            "meter_id": meter_id,
            "date": current_time,
            "previous_day_reading": current_meter['day_reading'],
            "previous_night_reading": current_meter['night_reading'],
            "current_day_reading": day_reading,
            "current_night_reading": night_reading,
            "day_consumption": day_consumption,
            "night_consumption": night_consumption,
            "day_tariff": self.config['tariffs']['day'],
            "night_tariff": self.config['tariffs']['night'],
            "total_amount": total_amount,
            "day_reset_detected": day_reset,
            "night_reset_detected": night_reset
        }
        self.billing_history_collection.insert_one(billing_record)

        self.meters_collection.update_one(
            {"meter_id": meter_id},
            {"$set": {
                "day_reading": day_reading,
                "night_reading": night_reading,
                "date": current_time
            }}
        )

        return billing_record

    def get_meter_history(self, meter_id: str) -> List[Dict]:
        return list(
            self.billing_history_collection
            .find({"meter_id": meter_id}, {"_id": 0})
            .sort("date", 1)
        )

    def get_all_meters(self) -> List[Dict]:
        return list(self.meters_collection.find({}, {"_id": 0}))

    def _calculate_consumption(self, previous_reading: float, current_reading: float, 
                                is_reset: bool, reset_value: float) -> float:
        return (reset_value + current_reading - previous_reading) if is_reset else (current_reading - previous_reading)

    def close(self):
        if hasattr(self, 'client'):
            self.client.close()

    def __del__(self):
        self.close()
