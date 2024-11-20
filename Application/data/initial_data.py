import sys
from zoneinfo import ZoneInfo
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.data.data_tools import extract_field_value # noqa: E402



LOCAL_TIME_ZONE_NAME = extract_field_value(field       = 'local_time_zone_name',
                                           config_path = r'Application/configs/config.json')

LOCAL_TIME_ZONE = ZoneInfo(LOCAL_TIME_ZONE_NAME)