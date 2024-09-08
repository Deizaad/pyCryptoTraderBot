import os
import sys
import pytz
import json
import logging
import traceback
import logging.config
from zoneinfo import ZoneInfo
from dotenv import dotenv_values
from datetime import date, datetime
from persiantools.jdatetime import JalaliDate                        # type: ignore
from typing import Mapping, Any, Literal, override
from logging.handlers import TimedRotatingFileHandler

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.load_json import load                         # noqa: E402
from Application.data.data_tools import extract_strategy_field_value # noqa: E402




# Extract log level from config file
# =================================================================================================
levels_map = {'DEBUG'    : logging.DEBUG,
              'INFO'     : logging.INFO,
              'WARNING'  : logging.WARNING,
              'ERROR'    : logging.ERROR,
              'CRITICAL' : logging.CRITICAL}

LOG_LEVEL = levels_map[
    extract_strategy_field_value(field='log_level', config_path=r'Application/configs/config.json')
]
# =================================================================================================




# Formatters
# =================================================================================================
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

texted_with_time_zone = WithTimeZone(
    fmt='{levelname} from "{funcName}" in "{filename}" at {asctime}:\n    {message}\n\n',
    datefmt='%Y-%m-%d %H:%M:%S GMT%z',
    style='{',
    timezone='Asia/Tehran'
)
# ________________________________________________________________________________ . . .


class JSONFormatter(logging.Formatter):
    def format(self, record):
        # Create a dictionary from the log record's attributes
        log_record = {
            'level': record.levelname,
            'message': record.getMessage(),
            'time': self.formatTime(record),
            'logger_name': record.name,
            'filename': record.pathname,
            'line': record.lineno,
            'function': record.funcName,
            'process': record.process,
            'thread': record.threadName,
        }

        # Handle any extra fields passed to the logger
        log_record.update(self._get_extra_fields(record))

        # Add exception info if it exists
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_record)
    # ____________________________________________________________________________ . . .
    

    def _get_extra_fields(self, record):
        """
        Capture any extra fields provided in the `extra` argument and ensure they are JSON serializable.
        """
        extra_fields = {}
        # Ignore fields that are part of the standard LogRecord attributes
        standard_fields = set([
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
            'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
            'created', 'msecs', 'relativeCreated', 'thread', 'threadName', 'process',
            'processName', 'message', 'asctime'
        ])

        for key, value in record.__dict__.items():
            if key not in standard_fields and self._is_json_serializable(value):
                extra_fields[key] = value
            else:
                extra_fields[key] = str(value)  # Serialize non-serializable fields as string

        return extra_fields
    # ____________________________________________________________________________ . . .
    

    def _is_json_serializable(self, value):
        """
        Checks if a value can be serialized into JSON.
        """
        try:
            json.dumps(value)
            return True
        except (TypeError, OverflowError):
            return False
    # ____________________________________________________________________________ . . .
        
    
    def formatTime(self, record, datefmt=None):
        """
        Customizes the time format to ISO 8601.
        """
        return datetime.utcfromtimestamp(record.created).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    # ____________________________________________________________________________ . . .


    def formatException(self, exc_info):
        """
        Formats exception info as a string for JSON serialization.
        """
        return ''.join(traceback.format_exception(*exc_info))
# ________________________________________________________________________________ . . .


class JSONWithTimezoneFormatter(logging.Formatter):
    def __init__(self,
                 fmt: str | None = None,
                 datefmt: str | None = None,
                 style: Literal['{', '%', '$'] = '%',
                 defaults: Mapping[str, Any] | None = None,
                 timezone: str | None = None,
                 output_json: bool = False,
                 json_fields: Mapping[str, str] | None = None):
        """
        Initialize the JSONWithTimezoneFormatter.

        Parameters:
            fmt: Format string (used if output_json is False).
            datefmt: Datetime format string.
            style: Formatting style. ('%', '{', or '$').
            defaults: Default values to use in the format string.
            timezone: Timezone name (e.g., 'America/New_York').
            output_json: Whether to format the log record as JSON.
            json_fields: Custom key-value pairs for JSON log record.
        """
        super().__init__(fmt, datefmt, style)
        self.timezone = ZoneInfo(timezone) if timezone else None
        self.defaults = defaults or {}
        self.output_json = output_json
        self.json_fields = json_fields or {
            'level': 'levelname',
            'message': 'getMessage',
            'time': 'asctime',
            'logger_name': 'name',
            'filename': 'pathname',
            'line': 'lineno',
            'function': 'funcName',
            'process': 'process',
            'thread': 'threadName'
        }
    # ____________________________________________________________________________ . . .

    @override
    def format(self, record):
        """
        Formats the log record. Outputs as JSON if output_json is True, otherwise follows standard 
        formatting.
        """
        # Add default values to the log record attributes
        record.__dict__.update(self.defaults)

        if self.output_json:
            return self._format_as_json(record)
        else:
            # Standard format
            return super().format(record)
    # ____________________________________________________________________________ . . .


    def _format_as_json(self, record):
        """
        Formats the log record as a JSON string with customizable key-value pairs.
        """
        log_record = {}

        for key, attr in self.json_fields.items():
            log_record[key] = getattr(record, attr)() if callable(getattr(record, attr, None)) else getattr(record, attr, None)

        # Handle any extra fields passed to the logger
        log_record.update(self._get_extra_fields(record))

        # Add exception info if it exists
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_record)
    # ____________________________________________________________________________ . . .


    def formatTime(self, record, datefmt=None):
        """
        Customizes the time format to ISO 8601 in JSON mode and uses timezones when available.
        """
        # Use timezone if specified
        if self.timezone:
            dt = datetime.fromtimestamp(record.created, self.timezone)
        else:
            dt = datetime.utcfromtimestamp(record.created)

        if datefmt:
            return dt.strftime(datefmt)
        else:
            # ISO 8601 format for JSON
            return dt.isoformat() if self.output_json else dt.strftime('%Y-%m-%d %H:%M:%S GMT%z')
    # ____________________________________________________________________________ . . .


    def formatException(self, exc_info):
        """
        Formats exception info as a string for JSON serialization.
        """
        return ''.join(traceback.format_exception(*exc_info))
    # ____________________________________________________________________________ . . .


    def _get_extra_fields(self, record):
        """
        Capture any extra fields provided in the `extra` argument and ensure they are JSON serializable.
        """
        extra_fields = {}
        # Standard fields to ignore for extra attributes
        standard_fields = set([
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
            'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
            'created', 'msecs', 'relativeCreated', 'thread', 'threadName', 'process',
            'processName', 'message', 'asctime'
        ])

        for key, value in record.__dict__.items():
            if key not in standard_fields and self._is_json_serializable(value):
                extra_fields[key] = value
            else:
                extra_fields[key] = str(value)  # Serialize non-serializable fields as string

        return extra_fields
    # ____________________________________________________________________________ . . .


    def _is_json_serializable(self, value):
        """
        Checks if a value can be serialized into JSON.
        """
        try:
            json.dumps(value)
            return True
        except (TypeError, OverflowError):
            return False
# ________________________________________________________________________________ . . .
        

# =================================================================================================




# Handlers
# =================================================================================================
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
# ________________________________________________________________________________ . . .


# TIMED FILE (.log) HANDLER
timed_file_handler = TimedRotatingFileHandler(filename    = set_file_name(),
                                              when        = 'H',
                                              interval    = 1,
                                              backupCount = 24)

timed_file_handler.setLevel(LOG_LEVEL)
timed_file_handler.setFormatter(fmt=texted_with_time_zone)
# ________________________________________________________________________________ . . .


# TIMED .json HANDLER
# timed_json_handler = logging.handlers.QueueHandler()
# ________________________________________________________________________________ . . .


# THREADED HANDLER
# threaded_handler = logging.handlers.QueueHandler()
# ________________________________________________________________________________ . . .


# STDOUT HANDLER
# stdout = logging.StreamHandler()
# ________________________________________________________________________________ . . .


# STDERR HANDLER
# ________________________________________________________________________________ . . .


# =================================================================================================



# Initializers
# =================================================================================================
def initialize_logger(logger_name: str) -> logging.Logger:
    """
    Initializes the logger.
    """
    logger = logging.getLogger(name=logger_name)
    logger.addHandler(hdlr=timed_file_handler)

    return logger
# ________________________________________________________________________________ . . .


def initialize_logger_from_config(logger_name: str) -> logging.Logger:
    """
    Initializes the logger from logging_config.json file.
    """
    logging.config.dictConfig(load(r'Application/configs/logging_config.json'))
    logger = logging.getLogger(name=logger_name)
    logger.addHandler(hdlr=timed_file_handler)

    return logger
# ________________________________________________________________________________ . . .


# =================================================================================================








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
print(json.dumps(load(r'Application/configs/logging_config.json'), indent=4))