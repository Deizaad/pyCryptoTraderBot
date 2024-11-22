import sys
from zoneinfo import ZoneInfo
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.load_json import load # noqa: E402





LOCAL_TIME_ZONE_NAME = load(r'Application/configs/config.json').get('local_time_zone_name')
LOCAL_TIME_ZONE      = ZoneInfo(LOCAL_TIME_ZONE_NAME)