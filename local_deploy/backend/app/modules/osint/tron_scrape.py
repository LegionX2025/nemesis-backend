import requests
import json

def fetch_tron_accounts(limit=1000, max_start=1000):
    base_url = "https://apilist.tronscanapi.com/api/account/list"
    tron_accounts = []

    current_start = 0

    while current_start < max_start:
        # Construct the URL with pagination
        params = {
            "limit": limit,
            "start": current_start
        }

        # Fetch data from the API
        response = requests.get(base_url, params=params)

        if response.status_code != 200:
            print(f"Error fetching data: {response.status_code}")
            break

        data = response.json()

        # Check if 'data' key exists in the response
        if "data" in data:
            accounts = data["data"]
            tron_accounts.extend(accounts)

            # Update the starting point for the next request
            current_start += 1

            # If the API returns fewer accounts than requested, stop the loop
            if len(accounts) < limit:
                print("Reached the end of available accounts.")
                break
        else:
            print("Unexpected response format. No 'data' key found.")
            break

    return tron_accounts

def save_accounts_to_file(accounts, filename="tron_accounts.json"):
    try:
        with open(filename, "w") as file:
            json.dump(accounts, file, indent=4)
        print(f"Accounts saved to {filename}")
    except Exception as e:
        print(f"Error saving accounts to file: {e}")

if __name__ == "__main__":
    limit = 1000  # Number of accounts to fetch per request
    max_start = 1000  # Maximum starting point for pagination
    tron_accounts = fetch_tron_accounts(limit=limit, max_start=max_start)
    print(f"Fetched {len(tron_accounts)} accounts.")

    # Save to a JSON file
    save_accounts_to_file(tron_accounts)
