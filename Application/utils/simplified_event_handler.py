import asyncio
import logging
from collections import defaultdict
from inspect import iscoroutinefunction
from typing import Callable, Coroutine, Dict, List, Any


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
            self.config: dict = {}
    # ____________________________________________________________________________ . . .


    def attach(self, listener: Listener, event: str):
        """
        Attaching a listener to an event channel.

        Parameters:
            listener (Callable | Coroutine): The listener function or coroutine.
            event (str): The event channel name.
        """
        self._listeners[event].append(listener)
        logging.debug(f'Listener \'{listener.__name__}\' attached to event \'{event}\'.')
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
    # ____________________________________________________________________________ . . .

    
    def emit(self, event: str, *args, **kwargs):
        """
        Broadcasting an event channel for all it's listeners to be executed asynchronously.

        Parameters:
            event (str): The event channel name.
            *args (any):
            **kwargs (any):
        """
        loop = asyncio.get_event_loop()
        tasks = [self.__invoke_listener(listener, *args, **kwargs) for listener in self._listeners[event]]

        loop.run_until_complete(asyncio.gather(*tasks))
    # ____________________________________________________________________________ . . .


    def __invoke_listener(self, listener: Listener, *args, **kwargs):
        if iscoroutinefunction(listener):
            return listener(*args, **kwargs)
        else:
            return asyncio.to_thread(listener, *args, **kwargs)
    # ____________________________________________________________________________ . . .

# =================================================================================================