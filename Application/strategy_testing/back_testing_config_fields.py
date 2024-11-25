import sys
from dotenv import dotenv_values
from persiantools.jdatetime import JalaliDateTime # type: ignore

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

# from Application.utils.load_json import load                # noqa: E402
from Application.data.data_tools import extract_field_value # noqa: E402


back_testing_config_path = r'Application/configs/back_testing_config.json'


SYMBOL = (
    extract_field_value(field="historical_sample", config_path=back_testing_config_path)
    .get("trading_pair")
    .get("symbol")
)

TIMEFRAME = extract_field_value(
    field="historical_sample", config_path=back_testing_config_path
).get("timeframe")

HISTORY_START: int = int(JalaliDateTime.strptime(
    data_string = extract_field_value(
        field="historical_sample", config_path=back_testing_config_path).get("start"),
    fmt="%Y-%m-%d %H:%M:%S").timestamp())

HISTORY_END: int = int(JalaliDateTime.strptime(
    data_string = extract_field_value(
        field="historical_sample", config_path=back_testing_config_path).get("end"),
    fmt="%Y-%m-%d %H:%M:%S").timestamp())

UNSEEN_START: int = int(JalaliDateTime.strptime(
    data_string = extract_field_value(
        field="unseen_sample", config_path=back_testing_config_path).get("start"),
    fmt="%Y-%m-%d %H:%M:%S").timestamp())

UNSEEN_END: int = int(JalaliDateTime.strptime(
    data_string = extract_field_value(
        field="unseen_sample", config_path=back_testing_config_path).get("end"),
    fmt="%Y-%m-%d %H:%M:%S").timestamp())

FETCH_CHUNCK_SIZE: int = extract_field_value(
    field="historical_sample", config_path=back_testing_config_path
).get("fetch_chunck_size")