import httpx

BASE_URL = "http://localhost:8000"

# Scenarios mapping directly to location_ids (2178: LA, 1044: London, 8023: Delhi)
TEST_SUITES = {
    "Sustained Increase & Recovery": {
        "location_id": 8023,
        "points": [110.0, 120.0, 130.0, 140.0, 150.0, 110.0, 30.0]
    },
    "Sudden Spike Followed by Noise": {
        "location_id": 2178,
        "points": [20.0, 22.0, 21.0, 150.0, 145.0, 148.0]
    },
    "Gradual Cleansing (Sustained Decrease)": {
        "location_id": 1044,
        "points": [180.0, 160.0, 140.0, 110.0, 80.0, 30.0]
    }
}

def run_mock_reading_harness():
    print("=" * 80)
    print("  RUNNING LIVE MOCK-READING HARNESS")
    print("=" * 80)

    for suite_name, suite_data in TEST_SUITES.items():
        location_id = suite_data["location_id"]
        mock_points = suite_data["points"]
        
        print(f"\n[Scenario]: {suite_name} (Location ID: {location_id})")
        print("-" * 80)
        print(f"{'STEP':<6} | {'AQI':<8} | {'DETECTION TYPE':<20} | {'STATUS':<15} | {'NOTIFICATION / REASON'}")
        print("-" * 80)

        for step, aqi_val in enumerate(mock_points, 1):
            # Payload matching MockInjectRequest in main.py
            payload = {
                "location_id": location_id,
                "value": aqi_val
            }

            try:
                # Direct call to mock-reading endpoint
                response = httpx.post(f"{BASE_URL}/api/mock-reading", json=payload, timeout=10.0)
                response.raise_for_status()
                res = response.json()

                # Extract audit log fields
                detection = res.get("detection", {})
                detection_type = detection.get("type") or "NORMAL"
                status = res.get("status", "NO_ACTION")
                msg = res.get("message") or detection.get("reason", "")

                print(f"#{step:<5} | {aqi_val:<8.1f} | {detection_type:<20} | {status:<15} | {msg}")

            except Exception as e:
                print(f"#{step:<5} | {aqi_val:<8.1f} | ERROR                | FAILED          | {e}")

if __name__ == "__main__":
    run_mock_reading_harness()