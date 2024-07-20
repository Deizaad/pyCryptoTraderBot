import asyncio
import inspect
import logging
from collections import defaultdict
from typing import Callable, Coroutine, Dict, List, Any

# Introducing Listeners type
Listener = Callable[..., Coroutine[Any, Any, Any]] | Callable[..., Any]



# =================================================================================================
class EventHandler:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(EventHandler, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    # ____________________________________________________________________________ . . .


    def __init__(self) -> None:
        if not hasattr(self, '_initialized'):
            self._initialized = True

            self._listeners: Dict[str, List[Listener]] = defaultdict(list)
            self._event_supplies: Dict[str, List[str]] = {}
    # ____________________________________________________________________________ . . .


    def attach(self, listener: Listener, event: str):
        """
        Attaching a listener to an event channel.

        Parameters:
            listener (Callable | Coroutine): The listener function or coroutine.
            event (str): The event channel name.
        """
        if event not in self._event_supplies:
            raise ValueError(f"""Event "{event}" is not registered. Register the event before 
                             attaching listeners""")
        
        self._listeners[event].append(listener)
        logging.info(f'Listener \'{listener.__name__}\' attached to event chanel \'{event}\'.')
    # ____________________________________________________________________________ . . .
    
    
    def detach(self, listener: Listener, event: str):
        """
        Detaching a listener from an event Channel.

        Parameters:
            listener (Callable | Coroutine): The listener function or coroutine.
            event (str): The event channel name.
        """
        if event in self._listeners:
            self._listeners[event].remove(listener)
            
            if not self._listeners[event]:
                del self._listeners[event]

        logging.info(f'Listener \'{listener.__name__}\' detached from event chanel \'{event}\'.')
    # ____________________________________________________________________________ . . .


    def register_event(self, event: str, event_supplies: List[str]):
        """
        Register an event along with it's required parameters.

        parameters:
            event (str): The event channel name.
            event_supplies (List[str]): The list of supply parameters for event channel.
        """
        self._event_supplies[event] = event_supplies
    # ____________________________________________________________________________ . . .

    
    def emit(self, event: str, **kwargs):
        """
        Broadcasting an event channel for all it's listeners to be executed asynchronously.

        Parameters:
            event (str): The event channel name.
            **kwargs (any): Keyword arguments to pass to listeners.
        """
        if event not in self._event_supplies:
            raise ValueError(f'Event {event} is not registered.')
        
        event_supplies = self._event_supplies[event]
        for supply in event_supplies:
            if supply not in kwargs:
                raise ValueError(f'Missing supply parameter "{supply}" for event "{event}".')

        loop = asyncio.get_event_loop()
        tasks = [self.__invoke_listener(listener, **kwargs) for listener in self._listeners[event]]

        # Check if the event loop is already running
        if loop.is_running():
            # Use asyncio.gather to run tasks if the loop is already running
            asyncio.ensure_future(asyncio.gather(*tasks))
        else:
            loop.run_until_complete(asyncio.gather(*tasks))
    # ____________________________________________________________________________ . . .


    def __invoke_listener(self, listener: Listener, **kwargs):
        # Get the signature of listener
        signature = inspect.signature(listener)
        
        # Extract the parameters that match the listener's signature
        listener_kwargs = {k: v for k, v in kwargs.items() if k in signature.parameters}

        if inspect.iscoroutinefunction(listener):
            return listener(**listener_kwargs)
        else:
            return asyncio.to_thread(listener, **listener_kwargs)
    # ____________________________________________________________________________ . . .

# =================================================================================================