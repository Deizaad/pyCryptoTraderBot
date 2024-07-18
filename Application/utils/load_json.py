import json
import logging



# =================================================================================================
def load(file_path: str) -> dict:
    try:
        with open(file_path, 'r') as file:
            json_dict = json.load(file)
            return json_dict
    except FileNotFoundError:
        logging.error(f"json File not found at {file_path}")
        raise
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from the .json file at {file_path}")
        raise
    except Exception as err:
        logging.error(f"Unexpected error loading .json file: {err}")
        raise
# =================================================================================================



if __name__ == '__main__':
    config = load(r'Application/configs/signal_config.json')

    print(config, type(config))