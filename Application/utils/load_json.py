import sys
import json
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.logs import get_logger # noqa: E402

bot_logs = get_logger(logger_name='bot_logs')



# =================================================================================================
def load(file_path: str) -> dict:
    try:
        with open(file_path, 'r') as file:
            json_dict = json.load(file)
            return json_dict
    except FileNotFoundError:
        bot_logs.error(f"json File not found at {file_path}")
        raise
    except json.JSONDecodeError:
        bot_logs.error(f"Error decoding JSON from the .json file at {file_path}")
        raise
    except Exception as err:
        bot_logs.error(f"Unexpected error loading .json file: {err}")
        raise
# =================================================================================================



if __name__ == '__main__':
    config = load(r'Application/configs/signal_config.json')

    print(config, type(config))