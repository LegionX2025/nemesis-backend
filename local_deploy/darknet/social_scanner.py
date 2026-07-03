import json
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

# Load the platform dictionary
PLATFORMS_FILE = os.path.join(os.path.dirname(__file__), "social_platforms.json")

def load_platforms():
    try:
        with open(PLATFORMS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading social platforms: {e}")
        return {}

PLATFORMS = load_platforms()

# Headers to bypass basic bot-blocking
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

def check_url(platform_name, url_template, username):
    """
    Synchronously check a single URL.
    Returns (platform_name, url) if successful, otherwise None.
    """
    try:
        url = url_template.format(quote(username))
        
        # We use a timeout of 5 seconds.
        # Allow redirects, but check final status code.
        res = requests.get(url, headers=HEADERS, timeout=5, allow_redirects=True)
        
        if res.status_code == 200:
            # Basic false-positive detection: if the page contains phrases indicating not found.
            text = res.text.lower()
            false_positive_phrases = [
                "page not found",
                "couldn't find",
                "doesn't exist",
                "user not found",
                "profile not found",
                "error 404"
            ]
            for phrase in false_positive_phrases:
                if phrase in text:
                    return None
            return (platform_name, url)
        
    except requests.RequestException:
        # Ignore timeouts, connection errors, etc.
        pass
    
    return None

def verify_username(username, max_workers=20):
    """
    Concurrently scan the username across all defined platforms.
    Returns a list of dictionaries with platform names and discovered URLs.
    """
    if not username or not PLATFORMS:
        return []

    verified_accounts = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_platform = {
            executor.submit(check_url, platform_name, url_template, username): platform_name
            for platform_name, url_template in PLATFORMS.items()
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_platform):
            result = future.result()
            if result:
                platform_name, url = result
                verified_accounts.append({
                    "platform": platform_name,
                    "url": url
                })
                
    return verified_accounts

if __name__ == "__main__":
    # Test execution
    test_user = "admin"
    print(f"Scanning for user: {test_user} across {len(PLATFORMS)} platforms...")
    results = verify_username(test_user, max_workers=50)
    print(f"Found {len(results)} accounts:")
    for res in results:
        print(f" - {res['platform']}: {res['url']}")
