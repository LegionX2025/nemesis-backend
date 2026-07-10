import requests
import json

tatum_key = "t-689cf2666ee03b5b553977b2-ffee8013de0747bda4e360b7"
url = "https://api.tatum.io/v3/bsc/account/transaction/0x3b5D17e2236f4D773DA87EE10B71D80C5e5b5772"

headers = {
    "x-api-key": tatum_key
}

response = requests.get(url, headers=headers)
print(response.json())
