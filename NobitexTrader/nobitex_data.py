import os
from dotenv import load_dotenv
import time


__all__ = ["API_KEY", "CURRENT_TIME", "BASE_URL", "TESTNET"]
# __endpoints__ = [""]
# __symbols__ = [""]

# API tokens:
load_dotenv('.env')
noneTOKEN_str = "Token is not configured"
API_KEY = os.getenv('MAIN_TOKEN', noneTOKEN_str)    # DONE NO-001

# Time:
CURRENT_TIME = time.time()

# URLs:
BASE_URL = 'https://api.nobitex.ir/'
TESTNET = 'https://testnetapi.nobitex.ir/'

# ENDPOINTS:
TRADES = 'v2/trades/'
OHLC = 'market/udf/history?'

# SYMBOLs:
USDTIRT = 'USDTIRT'