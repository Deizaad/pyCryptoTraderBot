import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.execution.scheduler import watch_transitions    # noqa: E402
from Application.trading.trade_engine import start_trade_engine    # noqa: E402



async def run():
    watch_transitions()
    await start_trade_engine()