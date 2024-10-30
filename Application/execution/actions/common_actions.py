"""
functionalities:
    * extract the current state of connected accounts from exchange at startup.
"""
import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.data.user import User                              # noqa: E402
from Application.api.nobitex_api import Account                     # noqa: E402
from Application.utils.event_channels import Event                  # noqa: E402
from Application.api.api_service import APIService                  # noqa: E402
from Application.utils.simplified_event_handler import EventHandler # noqa: E402

jarchi = EventHandler()
account = Account(APIService())




def _register_internal_events():
    jarchi.register_event(event=Event.SUCCESS_AUTHORIZATION, event_supplies=[])
# ____________________________________________________________________________ . . .


def heart_beat():
    """
    Constantly performs a connection pulse to check with trading platform.
    """
    async for new_response in account.live_fetch_user_profile(token=User.TOKEN): # type: ignore
        
# ____________________________________________________________________________ . . .


async def authorize_connection():
    """
    _summary_

    Raises:
        ValueError: In case of wrong invalid user API token.
        ValueError: In case of Mismatched userAPI token with user ID.
    """
    _register_internal_events()

    response = await anext(account.live_fetch_user_profile(token=User.TOKEN)) # type: ignore

    if response.status_code == 200:
        if response.json()['profile']['id'] == User.ID:
            await jarchi.emit(event=Event.SUCCESS_AUTHORIZATION)

        else:
            raise ValueError("Provided User API token doesn't match the User_ID!")
        
    elif response.status_code == 401:
        raise ValueError('User API Token is wrong!')
# ____________________________________________________________________________ . . .

# =================================================================================================


