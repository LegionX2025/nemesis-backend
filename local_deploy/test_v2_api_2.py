import requests
import json

url = "https://api.etherscan.io/v2/api?chainid=56&module=account&action=txlist&address=0x030c0c65DBb914e423992F35b4Fe956F5E90b045&startblock=0&endblock=99999999&sort=desc&apikey=AYQRQWFDJRK8WAX2ICJ8U4JUSYXZT5J7II"

try:
    response = requests.get(url)
    with open("v2_test_output.json", "w") as f:
        f.write(json.dumps({
            "status_code": response.status_code,
            "text": response.text
        }))
except Exception as e:
    with open("v2_test_output.json", "w") as f:
        f.write(str(e))
