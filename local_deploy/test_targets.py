import json
import urllib.request
import urllib.error

TARGETS = [
    "bc1qguj54d66l502pwvft3zjrgwtmvhhq88nsaj7t6",
    "0x2a91386cEdb02D0d1fc37a262B07d458A015F06F",
    "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "0xD6094943979AfB5d2748FBB84788Aa4D2b0bd857",
    "rJnLjofJ25FQc5wXgac4LCJFC364hptbJx",
    "rhwTCnnXrunzYGAe9GVEqcbUx7PUbTHWsm",
    "01beef7b5cb9814c9457048d3e444e629d555ef53a064dc4f69b804234eb4da4",
    "C46E163E55837748A2F623D55898B281B517654AFE06CCE6AC69BB8B0BF4553C",
    "0x353085f3c41a3c5475df2f5542dfd2d2757cd73ca2f6bf9c0b740ef0cdb07490",
    "0x33c5e72fcebed5d255eb396017982ad2cdceb2ef97275c58d04889ab2c52fac2",
    "0x69F8c4c19A3Fb24859fc9E0DacfD554c17958d75",
    "0x4Cbcff095bdb49885439c4B4F3c8dEC287F942d2",
    "0x030c0c65DBb914e423992F35b4Fe956F5E90b045",
    "0x7B9123262ad3b1F3Be48046B7D1e8f3Cd50B33D9",
    "0x97F1b05adb4FCCCA8a1a34E4801079547351419d",
    "0x36043C1860998b53dfeF070947f54a7B4567e9AC",
    "0x819c8aE7eA9FD880426fad62639D355d6aFC6921",
    "0xc28B3feFd967e573834F87400A65395e1C63BA99",
    "TJNT1H28om6hbxKwdDAcQxiGQwgrs7GDF5",
    "TSZGemBcmawToBxDvLvVzqPuav5qmqbHVK",
    "TVLAAu2vokqc9rekyUXqPyNLL5tPTBy8m5",
    "TVNcfk3b7Qq832WFg1oRpK38jnq4sMVFeX",
    "TT298Xjy7S7NuSa88diu5YY49KFEATb3N6",
    "TLrqCVpWW3g1vMNhfFKjwDa9MjAK5b12zA"
]

# We will try the live deployed Cloudflare worker first
BASE_URL = "https://nemesis-backend.legionxgaming2021.workers.dev/api"
LOCAL_URL = "http://127.0.0.1:8088/api"

def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}"}
    except Exception as e:
        return {"error": str(e)}

def test_target(target, base_url):
    print(f"\n--- Testing: {target} ---")
    
    # Nemesis ID Profile
    profile_data = fetch_json(f"{base_url}/nemesis_id/profile/{target}")
    if "error" not in profile_data:
        print(f"Profile: {profile_data.get('executive_summary', 'Success but no summary')}")
    else:
        print(f"Profile error: {profile_data['error']}")

    # Nemesis ID AML
    aml_data = fetch_json(f"{base_url}/nemesis_id/aml/{target}")
    if "error" not in aml_data:
        print(f"AML: Score {aml_data.get('score')} | Classification: {aml_data.get('classification')}")
    else:
        print(f"AML error: {aml_data['error']}")

    # Nemesis ID Intel
    intel_data = fetch_json(f"{base_url}/nemesis_id/intel/{target}")
    if "error" not in intel_data:
        print(f"Intel: Malicious? {intel_data.get('is_malicious')} | OSINT: {intel_data.get('osint_intel')}")
    else:
        print(f"Intel error: {intel_data['error']}")

def main():
    print("Starting tests...")
    
    active_url = BASE_URL
    try:
        urllib.request.urlopen(f"{BASE_URL}/start_trace", timeout=5)
        print(f"Using Cloudflare backend at {BASE_URL}")
    except urllib.error.HTTPError as e:
        if e.code in [405, 200, 404]: # Route might exist but require different method
            print(f"Using Cloudflare backend at {BASE_URL}")
        else:
            print(f"Cloudflare returned HTTP {e.code}")
    except Exception as e:
        print(f"Cloudflare backend unreachable. Trying local backend...")
        try:
            urllib.request.urlopen(f"{LOCAL_URL}/start_trace", timeout=2)
            active_url = LOCAL_URL
            print(f"Using Local backend at {LOCAL_URL}")
        except urllib.error.HTTPError as local_e:
            if local_e.code in [405, 200, 404]:
                active_url = LOCAL_URL
                print(f"Using Local backend at {LOCAL_URL}")
            else:
                print(f"Local backend returned HTTP {local_e.code}. Aborting.")
                return
        except Exception:
            print("Local backend is also NOT reachable at 127.0.0.1:8088. Please ensure app/main.py is running in another terminal.")
            return

    for target in TARGETS:
        test_target(target, active_url)

if __name__ == "__main__":
    main()
