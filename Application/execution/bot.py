import os
import sys
import importlib
from dotenv import load_dotenv

load_dotenv('project_path.env')
path = os.getenv('PYTHONPATH')
if path:
    sys.path.append(path)

from Application.configs.profile_config import Profile    # noqa: E402
from Application.utils.botlogger import initialize_logger    # noqa: E402



initialize_logger()

# import the profile module:
prf_path: str = f'Application.execution.profiles.{Profile.MODE}'
prf_module = importlib.import_module(prf_path)

# run the profile:
prf_module.run()