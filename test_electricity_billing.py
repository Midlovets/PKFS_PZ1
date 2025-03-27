import unittest
from electricity_billing import ElectricityBillingSystem

class TestElectricityBillingSystem(unittest.TestCase):
    def setUp(self):
        self.billing_system = ElectricityBillingSystem()
        
    def tearDown(self):
        self.billing_system.meters_collection.delete_many({"meter_id": {"$in": ["METER001", "METER002", "METER003", "METER004", "METER005"]}})
        self.billing_system.billing_history_collection.delete_many({"meter_id": {"$in": ["METER001", "METER002", "METER003", "METER004", "METER005"]}})
        self.billing_system.close()

    def test_update_existing_meter(self):
        meter_id = "METER001"
        initial_day_reading = 100.0
        initial_night_reading = 50.0
        self.billing_system.add_new_meter(meter_id, initial_day_reading, initial_night_reading)
        new_day_reading = 150.0
        new_night_reading = 75.0
        result = self.billing_system.update_meter_readings(meter_id, new_day_reading, new_night_reading)
        self.assertEqual(result['meter_id'], meter_id)
        self.assertEqual(result['day_consumption'], new_day_reading - initial_day_reading)
        self.assertEqual(result['night_consumption'], new_night_reading - initial_night_reading)
        self.assertFalse(result.get('day_reset_detected', False))
        self.assertFalse(result.get('night_reset_detected', False))

    def test_add_new_meter(self):
        meter_id = "METER002"
        day_reading = 100.0
        night_reading = 50.0
        result = self.billing_system.add_new_meter(meter_id, day_reading, night_reading)
        self.assertEqual(result['meter_id'], meter_id)
        self.assertEqual(result['day_reading'], day_reading)
        self.assertEqual(result['night_reading'], night_reading)

    def test_low_night_readings(self):
        meter_id = "METER003"
        initial_day_reading = 100.0
        initial_night_reading = 50.0
        self.billing_system.add_new_meter(meter_id, initial_day_reading, initial_night_reading)
        new_day_reading = 150.0
        new_night_reading = 30.0
        result = self.billing_system.update_meter_readings(meter_id, new_day_reading, new_night_reading)
        expected_night_consumption = self.billing_system.config['reset_values']['night'] + new_night_reading - initial_night_reading
        self.assertTrue(result.get('night_reset_detected', False))
        self.assertEqual(result['night_consumption'], expected_night_consumption)

    def test_low_day_readings(self):
        meter_id = "METER004"
        initial_day_reading = 100.0
        initial_night_reading = 50.0
        self.billing_system.add_new_meter(meter_id, initial_day_reading, initial_night_reading)
        new_day_reading = 80.0
        new_night_reading = 75.0
        result = self.billing_system.update_meter_readings(meter_id, new_day_reading, new_night_reading)
        expected_day_consumption = self.billing_system.config['reset_values']['day'] + new_day_reading - initial_day_reading
        self.assertTrue(result.get('day_reset_detected', False))
        self.assertEqual(result['day_consumption'], expected_day_consumption)

    def test_low_both_readings(self):
        meter_id = "METER005"
        initial_day_reading = 100.0
        initial_night_reading = 50.0
        self.billing_system.add_new_meter(meter_id, initial_day_reading, initial_night_reading)
        new_day_reading = 80.0
        new_night_reading = 30.0
        result = self.billing_system.update_meter_readings(meter_id, new_day_reading, new_night_reading)
        expected_day_consumption = self.billing_system.config['reset_values']['day'] + new_day_reading - initial_day_reading
        expected_night_consumption = self.billing_system.config['reset_values']['night'] + new_night_reading - initial_night_reading
        self.assertTrue(result.get('day_reset_detected', False))
        self.assertTrue(result.get('night_reset_detected', False))
        self.assertEqual(result['day_consumption'], expected_day_consumption)
        self.assertEqual(result['night_consumption'], expected_night_consumption)

if __name__ == '__main__':
    unittest.main()
