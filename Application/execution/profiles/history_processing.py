import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.unified_linkage import fetch_historical_kline


def run():
    _attach_to_events()
    pass


def _attach_to_events():
    pass