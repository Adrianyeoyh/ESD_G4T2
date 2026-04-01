import requests
from requests.exceptions import ConnectionError, RequestException, Timeout

TIMEOUT_SECONDS = 8

# UPDATED: Common paths based on typical project structures
DRUGS_URLS = ["http://localhost:5081/drugs", "http://localhost:5081/drug", "http://localhost:5081/"]
# UPDATED: Most orchestrators use /health or just / for status
PAYMENT_URLS = ["http://localhost:5004/health", "http://localhost:5004/"]

OUTSYSTEMS_GET_URL = "https://personal-iipxahjd.outsystemscloud.com/ClinicalRecordServices/rest/RecordsAPI/"

# UPDATED: Using the exact lowercase path from your Swagger screenshot
OUTSYSTEMS_PATIENT_URL = "https://personal-wv4mxqur.outsystemscloud.com/PatientService/rest/PatientAPI/patient"

# UPDATED: Exact keys required by your Swagger Example Value
DUMMY_PATIENT = {
    "nric": "S8881234B",        # Change this to something unique!
    "name": "Bernice Test",
    "phoneNo": 91234567,        # Pure integer
    "email": "test@gmail.com"
}

def check_service(name, urls, method="GET", json_data=None):
    print(f"\n--- Checking {name} ---")
    headers = {"Content-Type": "application/json"}
    
    for url in urls:
        try:
            if method == "GET":
                response = requests.get(url, timeout=TIMEOUT_SECONDS)
            else:
                response = requests.post(url, json=json_data, headers=headers, timeout=TIMEOUT_SECONDS)
            
            if response.status_code in [200, 201]:
                print(f"✅ PASS: {url} returned {response.status_code}")
                return True
            else:
                print(f"❌ FAIL: {url} returned {response.status_code}")
        except Exception as e:
            print(f"⚠️ ERROR: Could not connect to {url}")
    return False

def main():
    print("=== FINAL SYSTEM INTEGRATION CHECK ===")
    
    results = {
        "Local Drug Service": check_service("Drug Service", DRUGS_URLS),
        "Local Payment Service": check_service("Payment Service", PAYMENT_URLS),
        "OutSystems Clinical Records": check_service("OutSystems GET", [OUTSYSTEMS_GET_URL]),
        "OutSystems Patient Add": check_service("OutSystems POST", [OUTSYSTEMS_PATIENT_URL], "POST", DUMMY_PATIENT)
    }

    print("\n" + "="*30)
    print("       FINAL SUMMARY")
    print("="*30)
    for name, ok in results.items():
        print(f"{name.ljust(25)}: {'🟢 PASS' if ok else '🔴 FAIL'}")

    if all(results.values()):
        print("\n🚀 ALL SYSTEMS GO! You are ready for Frontend development.")
    else:
        print("\n🚧 HOLD UP: Some services are still failing. Check the logs above.")

if __name__ == "__main__":
    main()
