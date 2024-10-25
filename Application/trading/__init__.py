import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.logs import get_logger, get_log_level # noqa: E402

trade_logs = get_logger(logger_name='trade_logs', log_level=get_log_level('trader'))