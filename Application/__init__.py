import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.logs import get_logger # noqa: E402      





# Initialization of Logger Objects

bot_logs = get_logger(logger_name='bot')
# 'TPL_logs' -> 'Trading Platform Linkage Logs'
TPL_logs = get_logger(logger_name='TPL')
# 'NL_logs' -> 'Nobitex Linkage Logs'
NL_logs  = get_logger(logger_name='NL')
trade_logs = get_logger(logger_name='trade')
jarchi_logs = get_logger(logger_name='jarchi')