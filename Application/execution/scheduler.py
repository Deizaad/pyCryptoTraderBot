import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv('project_path.env')
path = os.getenv('PYTHONPATH')
if path:
    sys.path.append(path)

from Application.utils.load_json import load    # noqa: E402
from Application.utils.event_channels import Event    # noqa: E402
from Application.utils.simplified_event_handler import EventHandler    # noqa: E402



# Register events
jarchi = EventHandler()
jarchi.register_event(Event.START_ACTIVITY, [])
jarchi.register_event(Event.END_ACTIVITY, [])



def watch_transitions():
    strategy_cfg = load(r'Application/configs/strategy.json')
    activity_setup = strategy_cfg['active_times']

    if activity_setup == 247:
        logging.info(f'Broadcasting "{Event.START_ACTIVITY}" event from'\
                     ' scheduler.watch_transitions() function')

        jarchi.emit(Event.START_ACTIVITY)
    else:
        raise NotImplementedError('There is no code implementation for handling of active times'\
                                  'other than the 247')