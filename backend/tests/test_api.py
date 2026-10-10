import unittest

from fastapi.testclient import TestClient

import main
from foodkeeper import PRODUCTS
from safety_rules import assess_food


class SafetyRuleTests(unittest.TestCase):
    def test_danger_zone_exposure_over_limit_is_critical(self):
        result = assess_food(PRODUCTS[113], 20, 1)
        self.assertEqual(result["risk"], "Critical")

    def test_short_danger_zone_exposure_is_not_critical(self):
        result = assess_food(PRODUCTS[113], 20, 1 / 24)
        self.assertEqual(result["risk"], "High")

    def test_hot_day_uses_one_hour_limit(self):
        result = assess_food(PRODUCTS[113], 33, 1 / 24)
        self.assertEqual(result["risk"], "High")
        self.assertIn("1 hour", result["basis"])

    def test_canned_tuna_at_room_temperature_uses_pantry_guidance(self):
        result = assess_food(PRODUCTS[618], 20, 1)
        self.assertEqual(result["risk"], "Low")
        self.assertIn("3 Years", result["storage_guidance"])

    def test_frozen_food_is_low_risk_at_freezer_temperature(self):
        result = assess_food(PRODUCTS[113], -18, 90)
        self.assertEqual(result["risk"], "Low")
        self.assertIn("12 Months", result["storage_guidance"])

    def test_refrigerated_storage_duration_uses_selected_item(self):
        within_guide = assess_food(PRODUCTS[113], 4, 1)
        beyond_guide = assess_food(PRODUCTS[113], 4, 3)
        self.assertEqual(within_guide["risk"], "Low")
        self.assertEqual(beyond_guide["risk"], "High")

    def test_conditions_beyond_assessment_range_are_flagged(self):
        result = assess_food(PRODUCTS[113], 25, 400)
        self.assertTrue(result["out_of_range"])
        self.assertIsNotNone(result["range_warning"])


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.original_rate_limit = main.rate_limit
        self.original_client = main.client
        main.rate_limit = 30
        main.rate_windows.clear()
        self.client = TestClient(main.app)

    def tearDown(self):
        main.rate_limit = self.original_rate_limit
        main.client = self.original_client
        main.rate_windows.clear()

    def test_options_endpoint_serves_foodkeeper_entries(self):
        response = self.client.get("/options")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Dairy Products & Eggs", response.json()["food_categories"])
        self.assertIn("Glass Container", response.json()["packaging_types"])
        self.assertIn("Chicken — whole", [
            item["display_name"] for item in response.json()["food_items"]
        ])

    def test_invalid_values_return_validation_error_with_cors(self):
        response = self.client.post(
            "/predict",
            headers={"Origin": "http://localhost:5173"},
            json={"food_id": 113, "temperature": -1000, "days_stored": -5},
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.headers["access-control-allow-origin"], "http://localhost:5173"
        )

    def test_prediction_works_without_groq(self):
        main.client = None
        response = self.client.post(
            "/predict",
            json={"food_id": 618, "temperature": 20, "days_stored": 1},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["risk"], "Low")
        self.assertEqual(response.json()["explanation_status"], "disabled")

    def test_prediction_rejects_unknown_food_item(self):
        response = self.client.post(
            "/predict",
            json={"food_id": 999999, "temperature": 4, "days_stored": 1},
        )
        self.assertEqual(response.status_code, 422)

    def test_rate_limit_returns_retry_after(self):
        main.rate_limit = 1
        payload = {"food_id": 618, "temperature": 20, "days_stored": 1}
        self.assertEqual(self.client.post("/predict", json=payload).status_code, 200)
        response = self.client.post("/predict", json=payload)
        self.assertEqual(response.status_code, 429)
        self.assertIn("retry-after", response.headers)


if __name__ == "__main__":
    unittest.main()
