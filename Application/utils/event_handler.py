import asyncio
import logging
from collections import defaultdict, deque
from contextvars import ContextVar
from typing import Callable, Coroutine, Dict, List, Union, Any, Tuple
from functools import wraps
import time


# Setup logging
logger = logging.getLogger(__name__)


Listener = Union[Callable[..., Coroutine[Any, Any, Any]], Callable[..., Any]]



# =================================================================================================
class AsyncEventHandler:
    """
    Asynchronous event handler that supports event dispatching, listener management, 
    rate limiting, circuit breaking, scheduling, middleware, and more.

    Attributes:
        _listeners (Dict[str, List[Listener]]): A dictionary mapping event names to lists of listener functions or coroutines.
        _context (ContextVar): A context variable for managing context.
        _rate_limits (Dict[str, float]): A dictionary mapping event names to their rate limit intervals in seconds.
        _last_called (Dict[str, float]): A dictionary tracking the last call time of each event.
        _event_queue (asyncio.PriorityQueue): A priority queue for managing event dispatch order.
        _middleware (List[Callable]): A list of middleware functions or coroutines to be executed for every event dispatch.
        _filters (List[Callable]): A list of filter functions to filter events before dispatching.
        _before_dispatch_hooks (List[Callable]): A list of hooks to be executed before every event dispatch.
        _after_dispatch_hooks (List[Callable]): A list of hooks to be executed after every event dispatch.
        _event_dependencies (Dict[str, List[str]]): A dictionary mapping events to their dependencies.
        _event_tags (Dict[str, set]): A dictionary mapping events to their tags.
        _event_ttl (Dict[str, float]): A dictionary mapping events to their time-to-live (TTL) in seconds.
        _schedulers (List[Callable]): A list of scheduler coroutines for periodic events.
        _event_priorities (Dict[str, int]): A dictionary mapping events to their priority levels.
        _custom_loggers (Dict[str, Callable]): A dictionary mapping events to custom logger functions or coroutines.
        _event_categories (Dict[str, List[str]]): A dictionary mapping categories to lists of events.
        _listener_health (Dict[Listener, Dict[str, int]]): A dictionary tracking the success and failure counts of each listener.
        _dynamic_config (Dict[str, Any]): A dictionary for storing dynamic configuration values.
        _event_correlation (Dict[str, List[str]]): A dictionary mapping events to their correlated events.
        _event_broadcast_targets (Dict[str, List[str]]): A dictionary mapping events to their broadcast targets.
        _rate_limits_per_listener (Dict[Listener, float]): A dictionary mapping listeners to their rate limit intervals in seconds.
        _circuit_breakers (Dict[str, Dict[str, Union[int, float]]]): A dictionary mapping events to their circuit breaker settings.
        _load_balancers (Dict[str, List[Callable]]): A dictionary mapping events to their load balancer functions.
        _dead_letter_queue (deque): A deque for managing events that could not be processed.
        _global_throttling (Dict[str, Union[int, float]]): A dictionary for managing global throttling settings.
        _tenant_events (Dict[str, List[str]]): A dictionary mapping tenants to their events.
        _tenant_listeners (Dict[str, List[Listener]]): A dictionary mapping tenants to their listeners.
        _audit_log (List[Tuple]): A list for storing audit logs of event dispatches.
        _tracing_enabled (bool): A flag indicating whether event tracing is enabled.
        _task_queue (set): A set for managing running asyncio tasks.
        _running (bool): A flag indicating whether the event handler is running.
    """
    def __init__(self):
        self._listeners: Dict[str, List[Listener]] = defaultdict(list)
        self._context = ContextVar("context")
        self._rate_limits: Dict[str, float] = {}
        self._last_called: Dict[str, float] = defaultdict(float)
        self._event_queue = asyncio.PriorityQueue()
        self._middleware = []
        self._filters = []
        self._before_dispatch_hooks = []
        self._after_dispatch_hooks = []
        self._event_dependencies: Dict[str, List[str]] = defaultdict(list)
        self._event_tags: Dict[str, set] = defaultdict(set)
        self._event_ttl: Dict[str, float] = {}
        self._schedulers = []
        self._event_priorities: Dict[str, int] = defaultdict(int)
        self._custom_loggers: Dict[str, Callable] = {}
        self._event_categories: Dict[str, List[str]] = defaultdict(list)
        self._listener_health: Dict[Listener, Dict[str, int]] = defaultdict(lambda: {"success": 0, "failure": 0})
        self._dynamic_config: Dict[str, Any] = {}
        self._event_correlation: Dict[str, List[str]] = defaultdict(list)
        self._event_broadcast_targets: Dict[str, List[str]] = defaultdict(list)
        self._rate_limits_per_listener: Dict[Listener, float] = {}
        self._circuit_breakers: Dict[str, Dict[str, Union[int, float]]] = defaultdict(lambda: {"max_failures": 0, "reset_time": 0, "failures": 0, "last_failure_time": 0})
        self._load_balancers: Dict[str, List[Callable]] = defaultdict(list)
        self._dead_letter_queue = deque()
        self._global_throttling = {"interval": 0, "last_called": 0}
        self._tenant_events: Dict[str, List[str]] = defaultdict(list)
        self._tenant_listeners: Dict[str, List[Listener]] = defaultdict(list)
        self._audit_log = []
        self._tracing_enabled = False
        self._task_queue = set()
        self._running = False
    # ____________________________________________________________________________ . . .


    async def dispatch(self, event: str, *args, **kwargs):
        """
        Dispatches an event along with provided args/kwargs to its registered listeners.

        :param event: The name of the event to dispatch.
        :param args: Positional arguments to pass to the listeners.
        :param kwargs: Keyword arguments to pass to the listeners.
        """
        if event in self._filters:
            for filter_func in self._filters:
                if not filter_func(event, *args, **kwargs):
                    return

        for hook in self._before_dispatch_hooks:
            await hook(event, *args, **kwargs)

        priority = self._event_priorities[event]
        await self._event_queue.put((priority, event, args, kwargs))

        for hook in self._after_dispatch_hooks:
            await hook(event, *args, **kwargs)
    # ____________________________________________________________________________ . . .


    async def _dispatch(self, event: str, *args, **kwargs):
        if event in self._event_dependencies:
            for dependency in self._event_dependencies[event]:
                if dependency not in self._listeners:
                    logger.error(f'Dependency "{dependency}" not yet processed for event "{event}".')
                    return

        if self._tracing_enabled:
            self._audit_log.append((event, args, kwargs, time.time()))

        for listener in self._listeners[event]:
            if event in self._circuit_breakers:
                breaker = self._circuit_breakers[event]
                if breaker['failures'] >= breaker['max_failures']:
                    if time.time() - breaker['last_failure_time'] > breaker['reset_time']:
                        breaker['failures'] = 0
                    else:
                        continue

            if event in self._rate_limits:
                current_time = time.time()
                if current_time - self._last_called[event] < self._rate_limits[event]:
                    continue
                self._last_called[event] = current_time

            if listener in self._rate_limits_per_listener:
                current_time = time.time()
                if current_time - self._last_called[str(listener)] < self._rate_limits_per_listener[listener]:
                    continue
                self._last_called[str(listener)] = current_time

            if self._global_throttling['interval'] > 0:
                current_time = time.time()
                if current_time - self._global_throttling['last_called'] < self._global_throttling['interval']:
                    continue
                self._global_throttling['last_called'] = current_time

            await self._create_task(event, listener, *args, **kwargs)
    # ____________________________________________________________________________ . . .


    async def _create_task(self, event, listener, *args, **kwargs):
        """
        Create an asyncio task for a listener.

        :param event: The name of the event.
        :param listener: The listener to create a task for.
        :param args: Positional arguments to pass to the listener.
        :param kwargs: Keyword arguments to pass to the listener.
        """
        if asyncio.iscoroutinefunction(listener):
            task = asyncio.create_task(listener(*args, **kwargs))
        else:
            task = asyncio.create_task(asyncio.to_thread(listener, *args, **kwargs))

        self._task_queue.add(task)
        task.add_done_callback(self._task_queue.discard)

        try:
            await task
            self._listener_health[listener]["success"] += 1
        except Exception as e:
            self._listener_health[listener]["failure"] += 1
            logger.error(f'Error in listener {listener.__name__} for event "{event}": {e}')
    # ____________________________________________________________________________ . . .


    async def _process_event(self):
        while self._running:
            priority, event, args, kwargs = await self._event_queue.get()
            await self._dispatch(event, *args, **kwargs)
            self._event_queue.task_done()
    # ____________________________________________________________________________ . . .


    # async def _execute_with_retries(self, event, listener, *args, **kwargs):
    #     """
    #     Execute a listener with retries in case of failure.

    #     :param event: The name of the event.
    #     :param listener: The listener to execute.
    #     :param args: Positional arguments to pass to the listener.
    #     :param kwargs: Keyword arguments to pass to the listener.
    #     """
    #     attempt = 0
    #     while attempt < self._retry_attempts:
    #         try:
    #             start_time = time.time()
    #             if asyncio.iscoroutinefunction(listener.callback):
    #                 await asyncio.wait_for(listener.callback(*args, **kwargs), listener.timeout)
    #             else:
    #                 await self._execute_sync_with_timeout(listener.callback, listener.timeout, *args, **kwargs)
    #             self._log_execution_time(listener.callback, start_time)
    #             self._listener_health[listener.callback]['success'] += 1
    #             break
    #         except (asyncio.TimeoutError, Exception) as e:
    #             attempt += 1
    #             self._listener_health[listener.callback]['failure'] += 1
    #             self._handle_error(listener.callback, e, attempt)
    # ____________________________________________________________________________ . . .


    # async def _execute_sync_with_timeout(self, callback, timeout, *args, **kwargs):
    #     """
    #     Execute a synchronous callback with a timeout.

    #     :param callback: The callback to execute.
    #     :param timeout: The timeout for the execution.
    #     :param args: Positional arguments to pass to the callback.
    #     :param kwargs: Keyword arguments to pass to the callback.
    #     """
    #     start_time = time.time()
    #     try:
    #         loop = asyncio.get_running_loop()
    #         with ThreadPoolExecutor() as pool:
    #             await loop.run_in_executor(pool, callback, *args, **kwargs)
    #         self._log_execution_time(callback, start_time)
    #     except TimeoutError:
    #         self._handle_error(callback, "Timeout occurred")
    #     except Exception as e:
    #         self._handle_error(callback, e)
    # ____________________________________________________________________________ . . .


    def _log_execution_time(self, callback, start_time):
        """
        Log the execution time of a callback.

        :param callback: The callback function.
        :param start_time: The start time of the execution.
        """
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f'Listener {callback} executed in {execution_time:.4f} seconds.')
    # ____________________________________________________________________________ . . .


    # def _handle_error(self, callback, error, attempt=None):
    #     """
    #     Handle errors during event listener execution.

    #     :param callback: The callback function that failed.
    #     :param error: The error that occurred.
    #     :param attempt: The attempt number (for retries).
    #     """
    #     if attempt:
    #         logger.error(f'Listener {callback} failed on attempt {attempt} with error: {error}')
    #     else:
    #         logger.error(f'Listener {callback} failed with error: {error}')

    #     if callback in self._error_handlers:
    #         handler = self._error_handlers[callback]
    #         if asyncio.iscoroutinefunction(handler):
    #             asyncio.create_task(handler(error))
    #         else:
    #             handler(error)
    # ____________________________________________________________________________ . . .


    async def connect(self, event: str, listener: Listener):
        """
        Connect a listener to an event channel.

        :param listener: The listener function or coroutine.
        :param event: The event name.
        """
        self._listeners[event].append(listener)
        logger.info(f'Listener {listener.__name__} connected to event "{event}".')
    # ____________________________________________________________________________ . . .


    async def disconnect(self, event: str, listener: Listener):
        """
        Disconnect a listener from an event.

        :param listener: The listener function or coroutine.
        :param event: The event name.
        """
        self._listeners[event].remove(listener)
        logger.info(f'Listener {listener.__name__} disconnected from event "{event}".')
    # ____________________________________________________________________________ . . .


    async def bulk_connect(self, event_listeners: Dict[str, List[Listener]]):
        """
        Connect multiple listeners in bulk.

        :param listeners: A list of tuples containing listener, event, and optional parameters.
        """
        for event, listeners in event_listeners.items():
            for listener in listeners:
                await self.connect(event, listener)
        logger.info('Bulk connect operation completed.')
    # ____________________________________________________________________________ . . .


    async def bulk_disconnect(self, event_listeners: Dict[str, List[Listener]]):
        """
        Disconnect multiple listeners in bulk.

        :param listeners: A list of tuples containing listener and event.
        """
        for event, listeners in event_listeners.items():
            for listener in listeners:
                await self.disconnect(event, listener)
        logger.info('Bulk disconnect operation completed.')
    # ____________________________________________________________________________ . . .


    async def once(self, event: str, listener: Listener):
        """
        Connect a listener to an event to be executed only once.

        :param listener: The listener function or coroutine.
        :param event: The event name.
        """
        @wraps(listener)
        async def wrapper(*args, **kwargs):
            await listener(*args, **kwargs)
            await self.disconnect(event, wrapper)
        await self.connect(event, wrapper)
        logger.info(f'Listener {listener.__name__} connected to event "{event}" for a single use.')
    # ____________________________________________________________________________ . . .


    def set_error_handler(self, event: str, handler: Listener):
        """
        Set an error handler for a specific listener.

        :param handler: The error handler function or coroutine.
        """
        self._listeners[event].append(handler)
        logger.info(f'Error handler {handler.__name__} set for event "{event}".')
    # ____________________________________________________________________________ . . .


    def list_subscribers(self, event: str):
        """
        List all subscribers for a given event.

        :param event: The event name.
        :return: A list of listener functions or coroutines.
        """
        return self._listeners[event]
    # ____________________________________________________________________________ . . .


    async def dispatch_to_group(self, group: str, event: str, *args, **kwargs):
        """
        Dispatch an event to all listeners in a specific group.

        :param group: The group name.
        :param args: Positional arguments to pass to the listeners.
        :param kwargs: Keyword arguments to pass to the listeners.
        """
        if group in self._event_categories:
            for grouped_event in self._event_categories[group]:
                await self.dispatch(grouped_event, *args, **kwargs)
        logger.info(f'Event "{event}" dispatched to group "{group}".')
    # ____________________________________________________________________________ . . .


    async def dispatch_with_timeout(self, event: str, timeout: float, *args, **kwargs):
        """
        Dispatch an event with a timeout for the listeners.

        :param event: The event name.
        :param timeout: The timeout for the event dispatch.
        :param args: Positional arguments to pass to the listeners.
        :param kwargs: Keyword arguments to pass to the listeners.
        """
        try:
            await asyncio.wait_for(self.dispatch(event, *args, **kwargs), timeout)
            logger.info(f'Event "{event}" dispatched with timeout of {timeout} seconds.')
        except asyncio.TimeoutError:
            logger.warning(f'Dispatch of event "{event}" timed out after {timeout} seconds.')
    # ____________________________________________________________________________ . . .


    def add_filter(self, filter_func: Callable[[str, Tuple, Dict], bool]):
        """
        Add a filter function to preprocess events.

        :param filter_func: The filter function.
        """
        self._filters.append(filter_func)
        logger.info('Filter function added.')
    # ____________________________________________________________________________ . . .


    def add_middleware(self, middleware_func: Callable[[str, Tuple, Dict], Coroutine[Any, Any, None]]):
        """
        Add a middleware function to preprocess events.

        :param middleware_func: The middleware function.
        """
        self._middleware.append(middleware_func)
        logger.info('Middleware function added.')
    # ____________________________________________________________________________ . . .


    async def cancel_event(self, event: str):
        """
        Cancel an event, preventing its listeners from being executed.

        :param event: The event name.
        """
        if event in self._listeners:
            del self._listeners[event]
            logger.info(f'Event "{event}" cancelled.')
    # ____________________________________________________________________________ . . .


    async def clear_cancelled_event(self, event: str):
        """
        Clear a cancelled event, allowing its listeners to be executed again.

        :param event: The event name.
        """
        if event in self._listeners:
            self._listeners[event].clear()
            logger.info(f'Cancelled event "{event}" cleared.')
    # ____________________________________________________________________________ . . .


    # def set_max_concurrent_tasks(self, max_tasks):
    #     self._max_concurrent_tasks = max_tasks
    #     self._semaphore = asyncio.Semaphore(self._max_concurrent_tasks)
    #     logger.info(f'Max concurrent tasks set to {max_tasks}.')
    # ____________________________________________________________________________ . . .


    # def set_retry_attempts(self, attempts):
    #     self._retry_attempts = attempts
    #     logger.info(f'Retry attempts set to {attempts}.')
    # ____________________________________________________________________________ . . .


    def set_rate_limit(self, event: str, limit: float):
        """
        Set rate limit for an event.

        :param event: The event name.
        :param limit: The rate limit in seconds.
        """
        self._rate_limits[event] = limit
        logger.info(f'Rate limit set for event "{event}" to {limit} seconds.')
    # ____________________________________________________________________________ . . .


    def remove_rate_limit(self, event: str):
        """
        Remove the rate limit for an event.

        :param event: The event name.
        """
        if event in self._rate_limits:
            del self._rate_limits[event]
            logger.info(f'Rate limit removed for event "{event}".')
    # ____________________________________________________________________________ . . .


    def remove_filter(self, filter_func: Callable):
        """
        Remove a filter function.

        :param filter_func: The filter function to remove.
        """
        if filter_func in self._filters:
            self._filters.remove(filter_func)
            logger.info('Filter function removed.')
    # ____________________________________________________________________________ . . .


    # def save_state(self, filepath):
    #     with self._lock:
    #         with open(filepath, 'w') as f:
    #             f.write(str({
    #                 'listeners': self._listeners,
    #                 'cancelled_events': self._cancelled_events,
    #                 'audit_log': self._audit_log
    #             }))
    #         logger.info(f'State saved to {filepath}.')
    # ____________________________________________________________________________ . . .


    # def load_state(self, filepath):
    #     with self._lock:
    #         with open(filepath, 'r') as f:
    #             self._persistent_storage = eval(f.read())

    #         self._listeners = self._persistent_storage.get('listeners', defaultdict(list))
    #         self._cancelled_events = self._persistent_storage.get('cancelled_events', set())
    #         self._audit_log = self._persistent_storage.get('audit_log', [])
    #         logger.info(f'State loaded from {filepath}.')
    # ____________________________________________________________________________ . . .


    # def set_listener_state(self, listener, state):
    #     with self._lock:
    #         self._listener_states[listener] = state
    #         logger.info(f'State set for listener {listener}.')
    # ____________________________________________________________________________ . . .


    def get_listener_state(self, listener: Listener):
        """
        Get the state of a listener.

        :param listener: The listener function or coroutine.
        :return: The state of the listener.
        """
        return self._listener_health.get(listener, {"success": 0, "failure": 0})
    # ____________________________________________________________________________ . . .


    def add_before_dispatch_hook(self, hook_func: Callable[[str, Tuple, Dict], Coroutine[Any, Any, None]]):
        """
        Add a before dispatch hook.

        :param hook_func: The hook function.
        """
        self._before_dispatch_hooks.append(hook_func)
        logger.info('Before dispatch hook added.')
    # ____________________________________________________________________________ . . .


    def add_after_dispatch_hook(self, hook_func: Callable[[str, Tuple, Dict], Coroutine[Any, Any, None]]):
        """
        Add an after dispatch hook.

        :param hook_func: The hook function.
        """
        self._after_dispatch_hooks.append(hook_func)
        logger.info('After dispatch hook added.')
    # ____________________________________________________________________________ . . .


    def manage_context(self, context):
        """
        Context manager to manage context variables.

        :param key: The context variable key.
        :param value: The context variable value.
        """
        self._context.set(context)
        logger.info('Context managed.')
    # ____________________________________________________________________________ . . .



    # def set_context(self, key, value):
    #     context = self._context.get()
    #     context[key] = value
    #     self._context.set(context)
    # ____________________________________________________________________________ . . .


    # def get_context(self, key):
    #     context = self._context.get()
    #     return context.get(key)
    # ____________________________________________________________________________ . . .


    def add_event_dependency(self, event: str, dependency: str):
        """
        Add a dependency for an event.

        :param event: The event name.
        :param dependency: The dependency event name.
        """
        self._event_dependencies[event].append(dependency)
        logger.info(f'Dependency "{dependency}" added to event "{event}".')
    # ____________________________________________________________________________ . . .


    def remove_event_dependency(self, event: str, dependency: str):
        """
        Remove a dependency for an event.

        :param event: The event name.
        :param dependency: The dependency to remove.
        """
        if dependency in self._event_dependencies[event]:
            self._event_dependencies[event].remove(dependency)
            logger.info(f'Dependency "{dependency}" removed from event "{event}".')
    # ____________________________________________________________________________ . . .


    def add_event_tag(self, event: str, tag: str):
        """
        Add a tag to an event.

        :param event: The event name.
        :param tag: The tag to add.
        """
        self._event_tags[event].add(tag)
        logger.info(f'Tag "{tag}" added to event "{event}".')
    # ____________________________________________________________________________ . . .


    def remove_event_tag(self, event: str, tag: str):
        """
        Remove a tag from an event.

        :param event: The event name.
        :param tag: The tag to remove.
        """
        if tag in self._event_tags[event]:
            self._event_tags[event].remove(tag)
            logger.info(f'Tag "{tag}" removed from event "{event}".')
    # ____________________________________________________________________________ . . .


    def set_event_ttl(self, event: str, ttl: float):
        """
        Set a time-to-live (TTL) for an event.

        :param event: The event name.
        :param ttl: The TTL in seconds.
        """
        self._event_ttl[event] = ttl
        logger.info(f'TTL set to {ttl} seconds for event "{event}".')
    # ____________________________________________________________________________ . . .


    def add_scheduler(self, scheduler):
        """
        Add a scheduler for periodic events.

        :param scheduler: The scheduler coroutine.
        """
        self._schedulers.append(scheduler)
        logger.info('Scheduler added.')
    # ____________________________________________________________________________ . . .


    def remove_scheduler(self, scheduler):
        """
        Remove a scheduler.

        :param scheduler: The scheduler to remove.
        """
        if scheduler in self._schedulers:
            self._schedulers.remove(scheduler)
            logger.info('Scheduler removed.')
    # ____________________________________________________________________________ . . .


    def set_event_priority(self, event: str, priority: int):
        """
        Set priority for an event.

        :param event: The event name.
        :param priority: The priority value.
        """
        self._event_priorities[event] = priority
        logger.info(f'Priority for event "{event}" set to {priority}.')
    # ____________________________________________________________________________ . . .


    def add_custom_logger(self, event: str, logger_func: Callable):
        """
        Add a custom logger for an event.

        :param event: The event name.
        :param logger_func: The logger function or coroutine.
        """
        self._custom_loggers[event] = logger_func
        logger.info(f'Custom logger added for event "{event}".')
    # ____________________________________________________________________________ . . .


    def categorize_event(self, event: str, category: str):
        """
        Categorize an event.

        :param event: The event name.
        :param category: The category name.
        """
        self._event_categories[category].append(event)
        logger.info(f'Event "{event}" categorized under "{category}".')
    # ____________________________________________________________________________ . . .


    def set_listener_health(self, listener: Listener, health: Dict[str, int]):
        """
        Set the health status of a listener.

        :param listener: The listener function or coroutine.
        :param success: The success count.
        :param failure: The failure count.
        """
        self._listener_health[listener] = health
        logger.info(f'Health set for listener "{listener.__name__}".')
    # ____________________________________________________________________________ . . .


    # def set_event_listener_timeout(self, listener, timeout):
    #     for event, listeners in self._listeners.items():
    #         for l in listeners:
    #             if l.callback == listener:
    #                 l.timeout = timeout
    #                 logger.info(f'Timeout {timeout} set for listener "{listener}".')
    # ____________________________________________________________________________ . . .


    # def set_event_listener_condition(self, listener, condition):
    #     for event, listeners in self._listeners.items():
    #         for l in listeners:
    #             if l.callback == listener:
    #                 l.condition = condition
    #                 logger.info(f'Condition set for listener "{listener}".')
    # ____________________________________________________________________________ . . .


    async def add_dynamic_config(self, config_name: str, config_value: Any):
        """
        Add a dynamic configuration value.

        :param config_name: The name of the configuration.
        :param config_value: The value of the configuration.
        """
        self._dynamic_config[config_name] = config_value
        logger.info(f'Dynamic config "{config_name}" added with value "{config_value}".')
    # ____________________________________________________________________________ . . .


    async def get_dynamic_config(self, config_name: str):
        """
        Get a dynamic configuration value.

        :param config_name: The name of the configuration.
        :return: The value of the configuration.
        """
        return self._dynamic_config.get(config_name, None)
    # ____________________________________________________________________________ . . .


    def correlate_events(self, event: str, related_event: str):
        """
        Correlate two events.

        :param event1: The first event name.
        :param event2: The second event name.
        """
        self._event_correlation[event].append(related_event)
        logger.info(f'Event "{event}" correlated with "{related_event}".')
    # ____________________________________________________________________________ . . .


    async def broadcast_event(self, event: str, targets: List[str], *args, **kwargs):
        """
        Broadcast an event to multiple targets.

        :param event: The event name.
        :param targets: The target list.
        """
        for target in targets:
            await self.dispatch(target, *args, **kwargs)
        logger.info(f'Event "{event}" broadcasted to targets: {targets}.')
    # ____________________________________________________________________________ . . .


    def set_rate_limit_per_listener(self, listener: Listener, interval: float):
        """
        Set a rate limit for a specific listener.

        :param listener: The listener function or coroutine.
        :param interval: The rate limit interval in seconds.
        """
        self._rate_limits_per_listener[listener] = interval
        logger.info(f'Rate limit of {interval} seconds set for listener "{listener.__name__}".')
    # ____________________________________________________________________________ . . .


    def set_circuit_breaker(self, event: str, max_failures: int, reset_time: float):
        """
        Set a circuit breaker for an event.

        :param event: The event name.
        :param max_failures: The maximum number of failures before opening the circuit.
        :param reset_time: The time in seconds to wait before closing the circuit again.
        """
        self._circuit_breakers[event] = {
            'max_failures': max_failures,
            'reset_time': reset_time,
            'failures': 0,
            'last_failure_time': 0
        }
        logger.info(f'Circuit breaker set for event "{event}" with max failures {max_failures} and reset time {reset_time} seconds.')
    # ____________________________________________________________________________ . . .


    def add_load_balancer(self, event: str, balancer: Callable):
        """
        Add a load balancer for an event.

        :param event: The event name.
        :param load_balancer_func: The load balancer function.
        """
        self._load_balancers[event].append(balancer)
        logger.info('Load balancer added.')
    # ____________________________________________________________________________ . . .


    def add_to_dead_letter_queue(self, event: str, args, kwargs):
        """
        Add an event to the dead letter queue.

        :param event: The event name.
        :param reason: The reason for adding to the dead letter queue.
        """
        self._dead_letter_queue.append((event, args, kwargs))
        logger.info(f'Event "{event}" added to dead letter queue.')
    # ____________________________________________________________________________ . . .


    def set_global_throttling(self, interval: float):
        """
        Set global throttling interval for event dispatching.

        :param interval: Throttling interval in seconds.
        """
        self._global_throttling['interval'] = interval
        logger.info(f'Global throttling interval set to {interval} seconds.')
    # ____________________________________________________________________________ . . .


    def add_tenant_event(self, tenant: str, event: str):
        """
        Add an event to a tenant.

        :param tenant: The tenant name.
        :param event: The event name.
        """
        self._tenant_events[tenant].append(event)
        logger.info(f'Event "{event}" added to tenant "{tenant}".')
    # ____________________________________________________________________________ . . .


    def add_tenant_listener(self, tenant: str, listener: Listener):
        """
        Add a listener to a tenant.

        :param tenant: The tenant name.
        :param listener: The listener function or coroutine.
        """
        self._tenant_listeners[tenant].append(listener)
        logger.info(f'Listener "{listener.__name__}" added to tenant "{tenant}".')
    # ____________________________________________________________________________ . . .


    async def emit_to_tenant(self, tenant_id: str, event: str, *args, **kwargs):
        """
        Emit an event to a specific tenant.

        :param tenant_id: The tenant ID.
        :param event: The event name.
        :param args: Positional arguments to pass to the listeners.
        :param kwargs: Keyword arguments to pass to the listeners.
        """
        if tenant_id in self._tenant_events:
            for tenant_event in self._tenant_events[tenant_id]:
                await self.dispatch(tenant_event, *args, **kwargs)
        logger.info(f'Event "{event}" emitted to tenant "{tenant_id}".')
    # ____________________________________________________________________________ . . .


    async def dispatch_to_tenant(self, tenant: str, event: str, *args, **kwargs):
        """
        Dispatch an event to a tenant's listeners.

        :param tenant: The tenant name.
        :param event: The event name.
        :param args: Positional arguments to pass to the listeners.
        :param kwargs: Keyword arguments to pass to the listeners.
        """
        if tenant in self._tenant_events:
            for tenant_event in self._tenant_events[tenant]:
                await self.dispatch(tenant_event, *args, **kwargs)
        logger.info(f'Event "{event}" dispatched to tenant "{tenant}".')
    # ____________________________________________________________________________ . . .


    async def emit_to_all_tenants(self, event: str, *args, **kwargs):
        """
        Emit an event to all tenants.

        :param event: The event name.
        :param args: Positional arguments to pass to the listeners.
        :param kwargs: Keyword arguments to pass to the listeners.
        """
        for tenant_id in self._tenant_events:
            await self.emit_to_tenant(tenant_id, event, *args, **kwargs)
        logger.info(f'Event "{event}" emitted to all tenants.')
    # ____________________________________________________________________________ . . .


    async def schedule_event(self, event: str, delay: float, *args, **kwargs):
        """
        Schedule an event to be dispatched after a delay.

        :param event: The event name.
        :param delay: The delay in seconds.
        :param args: Positional arguments to pass to the listeners.
        :param kwargs: Keyword arguments to pass to the listeners.
        """
        await asyncio.sleep(delay)
        await self.dispatch(event, *args, **kwargs)
        logger.info(f'Event "{event}" scheduled to dispatch after {delay} seconds.')
    # ____________________________________________________________________________ . . .


    async def throttle_event(self, event: str, interval: float):
        """
        Throttle an event, allowing it to be dispatched at most once per interval.

        :param event: The event name.
        :param interval: The interval in seconds.
        """
        self._rate_limits[event] = interval
        logger.info(f'Event "{event}" throttled to {interval} seconds interval.')
    # ____________________________________________________________________________ . . .


    async def debounce_event(self, event: str, delay: float):
        """
        Debounce an event, delaying its dispatch until no new events occur within the interval.

        :param event: The event name.
        :param interval: The debounce interval in seconds.
        """
        self._rate_limits[event] = delay
        logger.info(f'Event "{event}" debounced with delay of {delay} seconds.')
    # ____________________________________________________________________________ . . .


    async def _delayed_dispatch(self, event: str, delay: float, *args, **kwargs):
        """
        Dispatch an event after a delay.

        :param event: The event name.
        :param delay: The delay in seconds.
        :param args: Positional arguments to pass to the listeners.
        :param kwargs: Keyword arguments to pass to the listeners.
        """
        await asyncio.sleep(delay)
        await self.dispatch(event, *args, **kwargs)
        logger.info(f'Event "{event}" delayed dispatch after {delay} seconds.')
    # ____________________________________________________________________________ . . .


    def enable_tracing(self):
        """
        Enable tracing of events.
        """
        self._tracing_enabled = True
        logger.info('Tracing enabled.')
    # ____________________________________________________________________________ . . .


    def disable_tracing(self):
        """
        Disable tracing of events.
        """
        self._tracing_enabled = False
        logger.info('Tracing disabled.')
    # ____________________________________________________________________________ . . .


    def get_audit_log(self):
        """
        Get the audit log of traced events.

        :return: The audit log.
        """
        return self._audit_log
    # ____________________________________________________________________________ . . .


    async def start(self):
        """
        Start processing events.
        """
        self._running = True
        asyncio.create_task(self._process_event())
        logger.info('Event handler started.')
    # ____________________________________________________________________________ . . .


    async def stop(self):
        """
        Stop processing events.
        """
        self._running = False
        await self._event_queue.join()
        logger.info('Event handler stopped.')
    # ____________________________________________________________________________ . . .


    async def shutdown(self):
        self._running = False
        await self._event_queue.join()
        for task in self._task_queue:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f'Task {task} cancelled.')
        logger.info('AsyncEventHandler shutdown complete.')
# =================================================================================================



event_handler = AsyncEventHandler()