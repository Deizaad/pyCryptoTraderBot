import os
import sys
import pytz
import json
import queue
import logging
import traceback
import logging.config
import logging.handlers
from zoneinfo import ZoneInfo
from datetime import date, datetime
from typing import Mapping, Any, Literal, override
from logging.handlers import TimedRotatingFileHandler
from persiantools.jdatetime import JalaliDate, JalaliDateTime  # type: ignore


with open(r'Application/configs/config.json', 'r') as config_file:
    config = json.load(config_file)
LOCAL_TIME_ZONE_NAME = config.get('local_time_zone_name', None)


def extract_log_configs(field : str) -> Any:
    path = r'Application/configs/logs_config.json'

    with open(path, 'r') as file:
                json_dict = json.load(file)

    value = json_dict.get(field, None)

    if not value:
        raise ValueError(f"Can not find value of '{field}' field 'strategy.json' config file, "\
                         "it has not been quantified with a value, or perhaps you misspelled it.")
    
    return value


# Extract log levels dynamically
def get_log_level(
    logger_or_handler: Literal["stdout", "file", "jarchi", "trader", "bot", "TPL", 'NL'],
) -> int:
    """
    _summary_

    Parameters:
        logger_or_handler (Literal['stdout', 'file', 'jarchi', 'trader', 'bot', 'TPL', 'NL']): _description_.

    Returns:
        log_level (int): _description_.
    """
    levels_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    log_level = levels_map.get(
        extract_log_configs(f"{logger_or_handler}_log_level"),
        logging.INFO,
    )

    return log_level
# =================================================================================================





# Formatters
class FormatterWithTimeZone(logging.Formatter):
    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: Literal["{", "%", "$"] = "{",
        defaults: Mapping[str, Any] | None = None,
        timezone: str | None = None,
        calendar_type: Literal["Gregorian", "Jalali"] = "Gregorian",
    ):
        """
        Inherited class from logging.Formatter class and Included time zone in it.

        Parameters:
            fmt (str): Format string.
            datefmt (str): Datetime format string.
            style (Literal['{', '%', '$']): Formatting style.
            defaults Mapping[str, Any]: Default values to include to formatted string.
            timezone (str): Timezone name (e.g., 'America/New_York').
            calendar_type (Literal['Gregorian', 'Jalali']): __description__. Defaults to 'Gregorian'.
        """
        super().__init__(fmt, datefmt, style)
        self.timezone = ZoneInfo(timezone) if timezone else ZoneInfo("UTC")
        self.defaults = defaults or {}
        self.calendar_type = calendar_type

    # ____________________________________________________________________________ . . .

    @override
    def format(self, record: logging.LogRecord):
        """
        Override of the 'format' method to insert default values in the format string.
        """
        # Add the defaults to the log record attributes
        record.__dict__.update(self.defaults)

        # Call the original format method to handle the rest
        return super().format(record)

    # ____________________________________________________________________________ . . .

    @override
    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None):
        """
        Override of the 'formatTime' method to use the provided timezone.
        """
        dt = (
            JalaliDateTime.fromtimestamp(record.created, self.timezone)
            if self.calendar_type == "Jalali"
            else datetime.fromtimestamp(record.created, self.timezone)
        )

        return dt.strftime(datefmt) if datefmt else dt.isoformat()
# =================================================================================================


class JSONFormatter(logging.Formatter):
    @override
    def format(self, record: logging.LogRecord):
        """
        Override of the 'format' mathod.
        """
        # Create a dictionary from the log record's attributes
        log_record = {
            "level": record.levelname,
            "time": self.formatTime(record),
            "time-stamp": record.created,
            "logger_name": record.name,
            "message": record.getMessage(),
            "path": record.pathname,
            "filename": record.filename,
            "module": record.module,
            "line": record.lineno,
            "function": record.funcName,
            "async_task": record.taskName,
            "thread": {"name": record.threadName, "id": record.thread},
            "process": {"name": record.processName, "id": record.process},
        }

        # Handle any extra fields passed to the logger
        log_record.update(self._get_extra_fields(record))

        # Add exception info if it exists
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)

    # ____________________________________________________________________________ . . .

    def _get_extra_fields(self, record):
        """
        Capture any extra fields provided in the `extra` argument and ensure they are JSON serializable.
        """
        extra_fields = {}
        # Ignore fields that are part of the standard LogRecord attributes
        standard_fields = set(
            [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "process",
                "processName",
                "message",
                "asctime",
                "taskName",
            ]
        )

        for key, value in record.__dict__.items():
            if key not in standard_fields and self._is_json_serializable(value):
                extra_fields[key] = value
            else:
                extra_fields[key] = str(
                    value
                )  # Serialize non-serializable fields as string

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

    @override
    def formatTime(self, record, datefmt=None):
        """
        Customizes the time format to ISO 8601.
        """
        return datetime.fromtimestamp(record.created, ZoneInfo("UTC")).strftime(
            extract_log_configs(field="date_fmt")
        )

    # ____________________________________________________________________________ . . .

    def formatException(self, exc_info):
        """
        Formats exception info as a string for JSON serialization.
        """
        return "".join(traceback.format_exception(*exc_info))
# =================================================================================================


class JSONWithTimezoneFormatter(logging.Formatter):
    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: Literal["{", "%", "$"] = "%",
        defaults: Mapping[str, Any] | None = None,
        timezone: str | None = None,
        output_json: bool = False,
        json_fields: Mapping[str, str] | None = None,
        calendar_type: Literal["Gregorian", "Jalali"] = "Gregorian",
    ):
        """
        Inherited from logging.Formatter class to format logs as json and included time zone handling.

        Parameters:
            fmt (str): Format string (used if output_json is False).
            datefmt (str): Datetime format string.
            style (Literal['%', '{', or '$']): Formatting style.
            defaults (Mapping[str, Any]): Default values to use in the format string.
            timezone (str): Timezone name (e.g., 'America/New_York').
            output_json (bool): Whether to format the log record as JSON.
            json_fields (Mapping[str, Any]): Custom key-value pairs for JSON log record.
            calendar_type (Literal['Gregorian', 'Jalali']): Weather to use Jalali DateTime or not.
        """
        super().__init__(fmt, datefmt, style)
        self.timezone = ZoneInfo(timezone) if timezone else ZoneInfo("UTC")
        self.defaults = defaults or {}
        self.output_json = output_json
        self.calendar_type = calendar_type
        self.json_fields = json_fields or {
            "level": "levelname",
            "time": "asctime",
            "time_stamp": "created",
            "logger": "name",
            "message": "message",
            "path": "pathname",
            "file": "filename",
            "module": "module",
            "line": "lineno",
            "function": "funcName",
            "async_task": "taskName",
            "thread_name": "threadName",
            "thread_id": "thread",
            "process_name": "processName",
            "process_id": "process"
        }

    # ____________________________________________________________________________ . . .

    @override
    def format(self, record: logging.LogRecord) -> str:
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

    def _format_as_json(self, record: logging.LogRecord):
        """
        Formats the log record as a JSON string with customizable key-value pairs.
        """
        log_record = {}

        for key, attr in self.json_fields.items():
            log_record[key] = (
                getattr(record, attr)() \
                if callable(getattr(record, attr, None)) \
                else getattr(record, attr, None)
            )

        # Handle any extra fields passed to the logger
        log_record.update(self._get_extra_fields(record))

        # Add exception info if it exists
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        if record.stack_info:
            log_record["stack_info"] = self.formatException(record.stack_info)

        return json.dumps(log_record)

    # ____________________________________________________________________________ . . .

    @override
    def formatTime(self, record, datefmt=None):
        """
        Customizes the time format to ISO 8601 in JSON mode and uses timezones when available.
        """
        # Use timezone if specified
        if self.calendar_type == "Jalali":
            dt = JalaliDateTime.fromtimestamp(record.created, self.timezone)
        else:
            dt = datetime.fromtimestamp(record.created, self.timezone)

        if datefmt:
            return dt.strftime(datefmt)
        else:
            # ISO 8601 format for JSON
            return (
                dt.isoformat() \
                if self.output_json \
                else dt.strftime(extract_log_configs(field="date_fmt"))
            )

    # ____________________________________________________________________________ . . .

    def formatException(self, exc_info):
        """
        Formats exception info as a string for JSON serialization.
        """
        return "".join(traceback.format_exception(*exc_info))

    # ____________________________________________________________________________ . . .

    def _get_extra_fields(self, record: logging.LogRecord):
        """
        Capture any extra fields provided in the `extra` argument and ensure they are JSON
        serializable.
        """
        extra_fields = {}
        # Standard fields to ignore for extra attributes
        standard_fields = set(
            [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "process",
                "processName",
                "message",
                "asctime",
                "taskName",
            ]
        )

        for key, value in record.__dict__.items():
            if key not in standard_fields and self._is_json_serializable(value):
                extra_fields[key] = value
            else:
                extra_fields[key] = str(
                    value
                )  # Serialize non-serializable fields as string

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
# =================================================================================================





# Filters
class FilterErrors(logging.Filter):
    @override
    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        return record.levelno <= logging.INFO
# ________________________________________________________________________________ . . .

# Other Filters ...
# =================================================================================================





# File Name Generators
def month_day_hour_file_name_generator(
    parent_logs_path: str,
    time_zone_name: str = "UTC",
    file_suffix: str = "log",
    folder_naming_approach: Literal[
        "Gregorian_Dated",
        "Jalali_Dated",
        "Double_Dated"] = "Gregorian_Dated"
    ) -> str:
    """
    Generates the full name of log file (including path). Creates a folder with month name,
    inside it a folder with day name, and inside it names the log files with the current hour.

    Parameters:
        parent_logs_path (str): Full path of parent folder to store log files.
        time_zone_name (str, optional): Time Zone name.
        file_suffix (str, optional): Suffix of log file. Defaults to 'log'.
        folder_naming_approach (Literal['Gregorian_Dated', 'Jalali_Dated', 'Double_Dated'], optional): Which approach to use to name 'month' and 'day' folders. Defaults to 'Gregorian_Dated'.

    Returns:
        full_log_file_name (str): A string with full name of log file including it's path.
    """
    current_time_hour = datetime.now(pytz.timezone(time_zone_name)).strftime("%H-00")
    file_name = f"{current_time_hour}.{file_suffix}"

    Gregorian_month_name = date.today().strftime("%B_%Y-%m")
    Gregorian_day_name = date.today().strftime("%A_%B_%d")
    Jalali_month_name = JalaliDate.today().strftime("%B_%Y-%m")
    Jalali_day_name = JalaliDate.today().strftime("%A_%d_%B")

    sub_folders_name_map = {
        "Gregorian_Dated": f"{Gregorian_month_name}/{Gregorian_day_name}/",
        "Jalali_Dated": f"{Jalali_month_name}/{Jalali_day_name}/",
        "Double_Dated": f"{Gregorian_month_name}({Jalali_month_name})/" \
                        f"{Gregorian_day_name}({Jalali_day_name})/",
    }

    path = f"{parent_logs_path}{sub_folders_name_map[folder_naming_approach]}"
    os.makedirs(path, exist_ok=True)

    return path + file_name
# ________________________________________________________________________________ . . .

# Other Generators ...
# =================================================================================================





# Handlers
def timed_file_handler(
    logs_path: str,
    file_suffix: Literal["log", "jsonl"],
    when: str,
    rotating_interval: int,
    backup_count: int,
    date_fmt: str,
    time_zone: str,
    logs_date_type: Literal["Gregorian", "Jalali"],
    json_fields: Mapping[str, str] | None = None,
    log_level: int = get_log_level("file"),
    naming_approach: Literal[
        "Gregorian_Dated",
        "Jalali_Dated",
        "Double_Dated"] = "Gregorian_Dated"
    ) -> logging.Handler:
    """
    _summary_

    Args:
        logs_path (str): _description_.
        file_suffix (Literal['log', 'jsonl']): _description_.
        when (str): Rotating time to create next file.
        rotating_interval (int): Rotating time interval to create next file.
        backup_count (int): Number of files to keep before overwriting the first file.
        date_fmt (str): _description_.
        time_zone (str): _description_.
        logs_date_type (Literal["Gregorian", "Jalali"]): _description_.
        json_fields (Mapping[str, str], optional): _description_.
        log_level (int, optional): _description_. Defaults to get_log_level('file').
        naming_approach (Literal['Gregorian_Dated', 'Jalali_Dated', 'Double_Dated'], optional): Defaults to 'Gregorian_Dated'.

    Returns:
        file_handler (logging.TimedRotatingFileHandler): _description_.
    """
    file_handler = TimedRotatingFileHandler(
        filename    = month_day_hour_file_name_generator(
            parent_logs_path       = logs_path,
            time_zone_name         = LOCAL_TIME_ZONE_NAME,
            file_suffix            = file_suffix,
            folder_naming_approach = naming_approach),
        when        = when,
        interval    = rotating_interval,
        backupCount = backup_count)

    file_handler.setLevel(log_level)

    if file_suffix == "jsonl":
        file_handler.setFormatter(
            fmt=JSONWithTimezoneFormatter(
                datefmt       = date_fmt,
                timezone      = time_zone,
                output_json   = True,
                json_fields   = json_fields,
                calendar_type = logs_date_type)
        )
    else:
        file_handler.setFormatter(
            fmt = FormatterWithTimeZone(
                fmt           = extract_log_configs(field='stderr_fmt'),
                datefmt       = date_fmt,
                style         = "{",
                timezone      = time_zone,
                calendar_type = logs_date_type,
            )
        )

    return file_handler
# ________________________________________________________________________________ . . .


def stdout_handler(log_level: int,
                   calendar_type: Literal["Jalali", "Gregorian"],
                   filter_errors: bool = True) -> logging.Handler:
    """
    _summary_.

    Parameters:
        log_level (int): _description_.
        calendar_type (Literal['Jalali', 'Gregorian']): _description_.
        filter_errors (bool, optional): _description_.

    Returns:
        handler (logging.Handler): _description_.
    """
    stdout_handler = logging.StreamHandler(stream=sys.stdout)

    stdout_handler.setLevel(log_level)
    stdout_handler.setFormatter(
        fmt=FormatterWithTimeZone(
            fmt           = extract_log_configs(field="stdout_fmt"),
            datefmt       = extract_log_configs(field="date_fmt"),
            style         = "{",
            timezone      = LOCAL_TIME_ZONE_NAME,
            calendar_type = calendar_type,
        )
    )

    if filter_errors:
        stdout_handler.addFilter(filter=FilterErrors())

    return stdout_handler
# ________________________________________________________________________________ . . .


def stderr_handler(calendar_type: Literal["Jalali", "Gregorian"]) -> logging.Handler:
    """_summary_

    Args:
        calendar_type (Literal['Jalali', 'Gregorian']): _description_.

    Returns:
        handler (logging.Handler): _description_.
    """
    stderr_handler = logging.StreamHandler(stream=sys.stderr)

    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(
        fmt=FormatterWithTimeZone(
            fmt           = extract_log_configs(field="stderr_fmt"),
            datefmt       = extract_log_configs(field="date_fmt"),
            style         = "{",
            timezone      = LOCAL_TIME_ZONE_NAME,
            calendar_type = calendar_type,
        )
    )

    return stderr_handler
# ________________________________________________________________________________ . . .


def queue_workers() -> (tuple[logging.handlers.QueueHandler, logging.handlers.QueueListener]):
    """
    _summary_

    Returns:
        _type_: _description_
    """
    logs_queue: queue.Queue = queue.Queue()
    queue_handler = logging.handlers.QueueHandler(logs_queue)
    queue_listener = logging.handlers.QueueListener(
        logs_queue,

        stderr_handler(calendar_type=extract_log_configs(field='stream_handlers_calendar_type')),

        stdout_handler(
            log_level     = get_log_level("stdout"),
            filter_errors = True,
            calendar_type = extract_log_configs(field='stream_handlers_calendar_type')),

        timed_file_handler(
            logs_path         = extract_log_configs(field="logs_root_path"),
            file_suffix       = extract_log_configs(field="log_suffix"),
            when              = extract_log_configs(field="rotating_file_handler_unit"),
            rotating_interval = extract_log_configs(field="rotating_file_handler_interval"),
            backup_count      = extract_log_configs(field="files_backup_count",),
            date_fmt          = extract_log_configs(field="date_fmt"),
            time_zone         = LOCAL_TIME_ZONE_NAME,
            logs_date_type    = extract_log_configs(field="file_handlers_calendar_type"),
            json_fields       =extract_log_configs(field="json_fields"),
            log_level         = get_log_level("file"),
            naming_approach   = extract_log_configs(field="file_naming_approach")),

        respect_handler_level=True,
    )

    return queue_handler, queue_listener


queue_listener: logging.handlers.QueueListener | None = None
# ________________________________________________________________________________ . . .

# Other Handlers ...
# =================================================================================================





# =================================================================================================
def initialize_logger(logger_name: str, log_level: int) -> logging.Logger:
    """
    Initializes the logger.
    """
    logger = logging.getLogger(name=logger_name)
    logger.setLevel(log_level)
    global queue_listener
    queue_handler, queue_listener = queue_workers()
    logger.addHandler(hdlr=queue_handler)

    queue_listener.start()

    logger.info(f'Initialized the "{logger.name}" logger.')
    return logger
# ________________________________________________________________________________ . . .


def finish_logs():
    """Finishes handling queued logs by stopping the QueueListener."""
    global queue_listener
    if queue_listener:
        queue_listener.stop()
    else:
        raise
# ________________________________________________________________________________ . . .


def get_logger(logger_name: str, log_level: int | None = None):
    logger = logging.getLogger(logger_name)
    if not logger.handlers:
        if log_level:
            logger = initialize_logger(logger_name=logger_name, log_level=log_level)
        else:
            raise Exception
    return logger
# =================================================================================================





if __name__ == "__main__":
    try:
        logger = get_logger(logger_name="TEST_LOGGER", log_level=logging.INFO)

        logger.debug(msg="This is a test debug log message")
        logger.info(msg="This is a test info log message")
        logger.warning(msg="This is a test warning log message")
        logger.error(
            msg="This is a test error log message", exc_info=True, stack_info=True
        )

    except Exception as err:
        logger.error("Error In main process: ", str(err))
    finally:
        finish_logs()