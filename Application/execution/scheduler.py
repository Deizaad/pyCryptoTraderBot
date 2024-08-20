import sys
import logging
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.load_json import load                           # noqa: E402
from Application.utils.event_channels import Event                     # noqa: E402
from Application.utils.simplified_event_handler import EventHandler    # noqa: E402

jarchi = EventHandler()

jarchi.register_event(Event.END_ACTIVITY, [])
jarchi.register_event(Event.START_ACTIVITY, [])



async def watch_transitions():
    """
    Watches for active time transitions and emits on corresponding event channel.
    """
    strategy_cfg = load(r'Application/configs/strategy.json')
    activity_setup = strategy_cfg['active_times']

    if activity_setup == 247:
        logging.info(f'Broadcasting "{Event.START_ACTIVITY}" event from'\
                     ' scheduler.watch_transitions() function')

        await jarchi.emit(Event.START_ACTIVITY)
    else:
        raise NotImplementedError('There is no code implementation for handling of active times'\
                                  'other than the 247')
# ________________________________________________________________________________ . . .