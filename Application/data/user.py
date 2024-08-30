import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.load_json import load    # noqa: E402

config = load(r'Application/configs/config.json')
setting_token = 'TEST_TOKEN' if config['setting'] == "TEST" else 'MAIN_TOKEN'



# =================================================================================================
class User:
    TOKEN = dotenv_values('secrets.env').get(setting_token, '')

    class Fee:
        MAKER: float = 0.1
        TAKER: float = 0.2
# =================================================================================================



# =================================================================================================
if __name__ == '__main__':
    print(User.TOKEN)
# =================================================================================================