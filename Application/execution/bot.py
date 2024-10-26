import sys
import signal
import asyncio
import logging
import importlib
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.configs.profile_config import Profile                    # noqa: E402
# from Application.utils.botlogger import initialize_logger               # noqa: E402
from Application.utils.logs import get_logger, finish_logs, get_log_level # noqa: E402



# Initializing the logger
bot_logs: logging.Logger = get_logger(logger_name='bot_logs', log_level=get_log_level('bot'))
# ________________________________________________________________________________ . . .


async def main():
    try:
        prf_path = f'Application.execution.profiles.{Profile.MODE}'
        prf_module = importlib.import_module(prf_path)

        await prf_module.run()

    except RuntimeError as err:
        bot_logs.error(f'RuntimeError occurred in "bot.main()" function: {err}')
    except Exception as err:
        bot_logs.error(f'Exception occurred in "bot.main()" function: {err}')
# ________________________________________________________________________________ . . .


def shutdown(signal_received=None, frame=None):
    """
    Gracefully shuts down the app.
    """
    bot_logs.info('Attempting to gracefully shutting down the bot!')

    finish_logs()
    sys.exit(0)
# ________________________________________________________________________________ . . .


signal.signal(signal.SIGINT, shutdown)  # Attach shutdown() to 'Interrupt Signal'
signal.signal(signal.SIGTERM, shutdown) # Attach shutdown() to 'Terminate Signal'
# =================================================================================================





# =================================================================================================
if __name__ == '__main__':
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            asyncio.ensure_future(main())
        else:
            loop.run_until_complete(main())

    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())

    finally:
        shutdown()
# =================================================================================================