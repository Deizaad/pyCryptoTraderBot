import sys
import asyncio
import logging
import importlib
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.configs.profile_config import Profile    # noqa: E402
from Application.utils.botlogger import initialize_logger    # noqa: E402



async def main():
    try:
        initialize_logger()

        # import the profile module:
        prf_path = f'Application.execution.profiles.{Profile.MODE}'
        prf_module = importlib.import_module(prf_path)

        # run the profile:
        await prf_module.run()

    except RuntimeError as err:
        logging.error(f'RuntimeError occurred in "bot.py" module: {err}')
    except Exception as err:
        logging.error(f'Exception occurred in "bot.py" module: {err}')
# ________________________________________________________________________________ . . .


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.ensure_future(main())
    else:
        loop.run_until_complete(main())