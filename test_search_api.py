import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_search_endpoint():
    print("Testing /api/search/vendors?q=pizza...")
    try:
        response = requests.get(f"{BASE_URL}/api/search/vendors?q=pizza")
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Found {len(data)} results.")
            for v in data:
                print(f"- {v['name']} ({v['cuisine']}) matched dishes: {', '.join(v['matching_dishes'])}")
        else:
            print(f"Failed! Status code: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error connecting to server: {e}")

if __name__ == "__main__":
    test_search_endpoint()
