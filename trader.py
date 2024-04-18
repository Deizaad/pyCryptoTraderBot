import os
from dotenv import load_dotenv
import requests

# Load api token
load_dotenv('.env')
API_KEY: str | None = os.getenv('MAIN_TOKEN', default=None)  # TODO #NO-001 configure 'os.getenv' to return "Token is not configured"
                                                             # in case of None.
print(API_KEY)

# Get connection to exchange
base_url = 'https://api.nobitex.ir/'
testnet = 'https://testnetapi.nobitex.ir/'

response = requests.get(base_url + '/v2/depth/USDTIRT')
print(response)
print(response.text)

payload = {}

headers = {
  'Authorization': 'Token ' + API_KEY
}

response2 = requests.get(base_url + '/users/profile', headers=headers, data=payload)
# response = requests.request("GET", url, headers=headers, data=payload)

print(response2)
print(response2.json())
