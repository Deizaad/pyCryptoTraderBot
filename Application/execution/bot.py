import sys
import asyncio
import importlib
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.configs.profile_config import Profile    # noqa: E402
from Application.utils.botlogger import initialize_logger    # noqa: E402



initialize_logger()


# import the profile module:
prf_path: str = f'Application.execution.profiles.{Profile.MODE}'
prf_module = importlib.import_module(prf_path)

# run the profile:
asyncio.run(prf_module.run())