import os
import sys
import pytz
import json
import logging
import logging.config
from datetime import date
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import dotenv_values
from typing import Mapping, Any, Literal
from persiantools.jdatetime import JalaliDate    # type: ignore
from logging.handlers import TimedRotatingFileHandler

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.data.data_tools import extract_strategy_field_value # noqa: E402

levels_map = {'DEBUG'    : logging.DEBUG,
              'INFO'     : logging.INFO,
              'WARNING'  : logging.WARNING,
              'ERROR'    : logging.ERROR,
              'CRITICAL' : logging.CRITICAL}

LOG_LEVEL = levels_map[
    extract_strategy_field_value(field='log_level', config_path=r'Application/configs/config.json')
]

class WithTimeZone(logging.Formatter):
    def __init__(self,
                 fmt      : str | None                                 = None,
                 datefmt  : str | None                                 = None,
                 style    : Literal['{'] | Literal['%'] | Literal['$'] = '%',
                 defaults : Mapping[str, Any] | None                   = None,
                 timezone : str | None                                 = None):
        """
        Initialize the TimezoneFormatter.

        Parameters:
            fmt: Format string.
            datefmt: Datetime format string.
            style: Formatting style. ('%', '{', or '$').
            defaults: Default values to use in the format string.
            timezone: Timezone name (e.g., 'America/New_York').
        """
        super().__init__(fmt, datefmt, style)
        self.timezone = ZoneInfo(timezone) if timezone else None
        self.defaults = defaults or {}

    def formatTime(self, record, datefmt=None):
        """
        Override formatTime to use the provided timezone.
        """
        dt = datetime.fromtimestamp(record.created, self.timezone)
        if datefmt:
            return dt.strftime(datefmt)
        else:
            return dt.isoformat()

    def format(self, record):
        """
        Override format to insert default values in the format string.
        """
        # Add the defaults to the log record attributes
        record.__dict__.update(self.defaults)

        # Call the original format method to handle the rest
        return super().format(record)

formatter = WithTimeZone(
    fmt='{levelname} from "{funcName}" in "{filename}" at {asctime}:\n    {message}\n\n',
    datefmt='%Y-%m-%d %H:%M:%S GMT%z',
    style='{',
    timezone='Asia/Tehran'
)

def set_file_name():
    file_name = str(datetime.now(pytz.timezone('Asia/Tehran')).strftime("%H-00")) + '.log'

    folder_name = './Logs/'
    month_folder_name = str(date.today().strftime("%B_%Y-%m")) \
                        + str(JalaliDate.today().strftime("(%B_%Y-%m)/"))

    day_folder_name = str(date.today().strftime("%A_%B_%d")) \
                        + str(JalaliDate.today().strftime("(%A_%d_%B)/"))
    path = str(folder_name+month_folder_name+day_folder_name)
    try:
        os.makedirs(path)
    except OSError as err:
        if err.errno == 17:
            print(f'Attempt to create Logs directory {path}: It already exsist!')
        else:
            print(f'Attempt to create Logs directory {path}: error accured: {err}')

    full_name = path+file_name
    return full_name


timed_file_handler = TimedRotatingFileHandler(filename    = set_file_name(),
                                              when        = 'H',
                                              interval    = 1,
                                              backupCount = 24)

timed_file_handler.setLevel(LOG_LEVEL)
timed_file_handler.setFormatter(fmt=formatter)


def initialize_logger(logger_name: str) -> logging.Logger:
    """
    
    """
    logger = logging.getLogger(name=logger_name)
    logger.addHandler(hdlr=timed_file_handler)

    return logger



# stdout_handler = logging.handlers
# strderr_handler = logging.handlers







logging_config = {
    "version": 1,

    "disable_exicting_loggers": False,

    "formatters": {
        "detailed_with_time_zone": {
            "format": ""
        }
    },

    "handlers": {
        "stderr": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "",
            "stream": "ext://sys.stderr"
        },
        "stdout": {
            "class": "logging.StreamHandler",
            "level": "",
            "formatter": "",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": "",
            "maxBytes": 0,
            "backupCount": 0
        }
    },

    "loggers": {
        "root": {
            "level" : "",
            "handlers": [
                "stdout"
            ]
        }
    }
}
print(json.dumps(logging_config, indent=4))
