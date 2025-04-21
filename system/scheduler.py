"""
Scheduler Module for AI System Automation Project.

This module implements task scheduling and execution mechanisms for the AI system,
providing facilities for scheduling tasks at specific times, with specific intervals,
or in response to specific events.

Classes:
    Scheduler: Main scheduler class for managing tasks.
    Task: Representation of a schedulable task.
    ScheduledTask: A task scheduled for execution.
    CronTask: A task scheduled using cron-like syntax.
    EventTask: A task triggered by system events.

Functions:
    schedule_task(func, **kwargs): Schedule a function for execution.
    schedule_at(func, time, **kwargs): Schedule a function at a specific time.
    schedule_interval(func, interval, **kwargs): Schedule a function at regular intervals.
    schedule_cron(func, cron_expr, **kwargs): Schedule a function using cron syntax.
    cancel_task(task_id): Cancel a scheduled task.
"""

import logging
import time
import threading
import datetime
import queue
import heapq
import uuid
import inspect
import traceback
import signal
import re
from typing import Dict, List, Optional, Any, Callable, Tuple, Set, Union
from abc import ABC, abstractmethod
import functools

# Configure logging
logger = logging.getLogger(__name__)


class Task:
    """
    Base class for all task types.

    This class represents a task that can be scheduled for execution.

    Attributes:
        id (str): Unique identifier for the task.
        name (str): Human-readable name for the task.
        function (Callable): The function to execute.
        args (tuple): Positional arguments for the function.
        kwargs (dict): Keyword arguments for the function.
        max_retries (int): Maximum number of retry attempts.
        retry_delay (float): Delay between retry attempts in seconds.
        tags (Set[str]): Tags associated with the task.
        timeout (Optional[float]): Maximum execution time in seconds.
    """

    def __init__(
        self,
        function: Callable,
        args: tuple = None,
        kwargs: dict = None,
        name: str = None,
        max_retries: int = 0,
        retry_delay: float = 1.0,
        tags: Set[str] = None,
        timeout: Optional[float] = None,
    ):
        """
        Initialize a new Task.

        Args:
            function (Callable): The function to execute.
            args (tuple, optional): Positional arguments for the function.
            kwargs (dict, optional): Keyword arguments for the function.
            name (str, optional): Human-readable name for the task.
            max_retries (int, optional): Maximum number of retry attempts.
            retry_delay (float, optional): Delay between retry attempts in seconds.
            tags (Set[str], optional): Tags associated with the task.
            timeout (Optional[float], optional): Maximum execution time in seconds.
        """
        self.id = str(uuid.uuid4())
        self.function = function
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.name = name or function.__name__
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.tags = tags or set()
        self.timeout = timeout
        self.created_at = time.time()
        self.retry_count = 0
        self.last_execution = None
        self.last_result = None
        self.last_error = None
        self.status = "pending"

    def execute(self) -> Any:
        """
        Execute the task function.

        Returns:
            Any: The result of the function execution.

        Raises:
            Exception: Any exception raised by the function.
        """
        self.status = "running"
        self.last_execution = time.time()

        try:
            if self.timeout is not None:
                # Use a separate thread with timeout
                result_queue = queue.Queue()

                def target():
                    try:
                        result = self.function(*self.args, **self.kwargs)
                        result_queue.put(("result", result))
                    except Exception as e:
                        result_queue.put(("error", e))

                thread = threading.Thread(target=target)
                thread.daemon = True
                thread.start()

                try:
                    result_type, result = result_queue.get(
                        timeout=self.timeout)
                    if result_type == "error":
                        raise result
                    return result
                except queue.Empty:
                    # Give the thread a little time to clean up
                    thread.join(0.1)
                    self.status = "timeout"
                    raise TimeoutError(
                        f"Task {self.name} timed out after {self.timeout} seconds"
                    )
            else:
                # Execute directly
                return self.function(*self.args, **self.kwargs)

        except Exception as e:
            self.status = "failed"
            self.last_error = e
            self.retry_count += 1
            if self.retry_count <= self.max_retries:
                logger.warning(
                    f"Task {self.name} failed, will retry ({self.retry_count}/{self.max_retries}): {str(e)}"
                )
                time.sleep(self.retry_delay)
                return self.execute()  # Retry
            raise
        finally:
            if self.status == "running":
                self.status = "completed"

    def to_dict(self) -> Dict:
        """
        Convert the task to a dictionary for serialization.

        Returns:
            Dict: Dictionary representation of the task.
        """
        return {
            "id": self.id,
            "name": self.name,
            "function": f"{self.function.__module__}.{self.function.__name__}",
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "tags": list(self.tags),
            "timeout": self.timeout,
            "created_at": self.created_at,
            "retry_count": self.retry_count,
            "last_execution": self.last_execution,
            "status": self.status,
        }

    def __str__(self) -> str:
        """String representation of the task."""
        return f"Task({self.id}, name={self.name}, status={self.status})"


class ScheduledTask(Task):
    """
    A task scheduled for execution at a specific time.

    Attributes:
        scheduled_time (float): When the task is scheduled to run.
        recurring (bool): Whether the task should recur.
        interval (Optional[float]): Interval between recurring executions.
        next_run (float): Time of the next scheduled execution.
    """

    def __init__(
        self,
        function: Callable,
        scheduled_time: float,
        recurring: bool = False,
        interval: Optional[float] = None,
        **kwargs,
    ):
        """
        Initialize a new ScheduledTask.

        Args:
            function (Callable): The function to execute.
            scheduled_time (float): When the task is scheduled to run.
            recurring (bool, optional): Whether the task should recur.
            interval (Optional[float], optional): Interval between recurring executions.
            **kwargs: Additional arguments for the Task class.
        """
        super().__init__(function, **kwargs)
        self.scheduled_time = scheduled_time
        self.recurring = recurring
        self.interval = interval
        self.next_run = scheduled_time

    def reschedule(self) -> None:
        """Update the next run time for a recurring task."""
        if not self.recurring:
            return

        if self.interval is not None:
            self.next_run = time.time() + self.interval

    def to_dict(self) -> Dict:
        """
        Convert the scheduled task to a dictionary.

        Returns:
            Dict: Dictionary representation of the scheduled task.
        """
        result = super().to_dict()
        result.update(
            {
                "scheduled_time": self.scheduled_time,
                "recurring": self.recurring,
                "interval": self.interval,
                "next_run": self.next_run,
            }
        )
        return result

    def __lt__(self, other):
        """Compare tasks by next run time for the priority queue."""
        if not isinstance(other, ScheduledTask):
            return NotImplemented
        return self.next_run < other.next_run


class CronTask(ScheduledTask):
    """
    A task scheduled using cron-like syntax.

    Attributes:
        cron_expr (str): Cron expression for scheduling.
        minute (Set[int]): Minutes when the task should run (0-59).
        hour (Set[int]): Hours when the task should run (0-23).
        day (Set[int]): Days of the month when the task should run (1-31).
        month (Set[int]): Months when the task should run (1-12).
        day_of_week (Set[int]): Days of the week when the task should run (0-6, where 0 is Monday).
    """

    def __init__(self, function: Callable, cron_expr: str, **kwargs):
        """
        Initialize a new CronTask.

        Args:
            function (Callable): The function to execute.
            cron_expr (str): Cron expression for scheduling in the format "minute hour day month day_of_week".
            **kwargs: Additional arguments for the Task class.
        """
        # Parse cron expression
        self.cron_expr = cron_expr
        self.minute, self.hour, self.day, self.month, self.day_of_week = (
            self._parse_cron(cron_expr)
        )

        # Calculate the next run time
        next_run = self._calculate_next_run(time.time())

        super().__init__(
            function=function,
            scheduled_time=next_run,
            recurring=True,
            interval=None,  # Not used for cron
            **kwargs,
        )

    def _parse_cron(
        self, cron_expr: str
    ) -> Tuple[Set[int], Set[int], Set[int], Set[int], Set[int]]:
        """
        Parse a cron expression.

        Args:
            cron_expr (str): Cron expression in the format "minute hour day month day_of_week".

        Returns:
            Tuple[Set[int], Set[int], Set[int], Set[int], Set[int]]: Parsed fields.

        Raises:
            ValueError: If the cron expression is invalid.
        """
        fields = cron_expr.split()
        if len(fields) != 5:
            raise ValueError(
                f"Invalid cron expression: {cron_expr}. Expected 5 fields, got {len(fields)}."
            )

        minute = self._parse_cron_field(fields[0], 0, 59)
        hour = self._parse_cron_field(fields[1], 0, 23)
        day = self._parse_cron_field(fields[2], 1, 31)
        month = self._parse_cron_field(fields[3], 1, 12)
        day_of_week = self._parse_cron_field(fields[4], 0, 6)

        return minute, hour, day, month, day_of_week

    def _parse_cron_field(self, field: str, min_val: int, max_val: int) -> Set[int]:
        """
        Parse a cron field.

        Args:
            field (str): The field to parse.
            min_val (int): Minimum valid value.
            max_val (int): Maximum valid value.

        Returns:
            Set[int]: Set of valid values for the field.

        Raises:
            ValueError: If the field is invalid.
        """
        result = set()

        # Handle wildcard
        if field == "*":
            return set(range(min_val, max_val + 1))

        # Handle lists and ranges
        for part in field.split(","):
            if "-" in part:
                # Range
                start, end = part.split("-")
                start = int(start)
                end = int(end)
                if start < min_val or end > max_val:
                    raise ValueError(
                        f"Invalid range {start}-{end} for field with range {min_val}-{max_val}"
                    )
                result.update(range(start, end + 1))
            elif "/" in part:
                # Step values
                step_range, step = part.split("/")
                step = int(step)

                if step_range == "*":
                    values = range(min_val, max_val + 1)
                elif "-" in step_range:
                    start, end = step_range.split("-")
                    start = int(start)
                    end = int(end)
                    if start < min_val or end > max_val:
                        raise ValueError(
                            f"Invalid range {start}-{end} for field with range {min_val}-{max_val}"
                        )
                    values = range(start, end + 1)
                else:
                    raise ValueError(f"Invalid step range: {step_range}")

                result.update(values[::step])
            else:
                # Single value
                value = int(part)
                if value < min_val or value > max_val:
                    raise ValueError(
                        f"Invalid value {value} for field with range {min_val}-{max_val}"
                    )
                result.add(value)

        return result

    def _calculate_next_run(self, from_time: float) -> float:
        """
        Calculate the next time this task should run.

        Args:
            from_time (float): The time to calculate from.

        Returns:
            float: The next run time as a timestamp.
        """
        # Start from the next minute
        dt = datetime.datetime.fromtimestamp(from_time)
        dt = dt.replace(second=0, microsecond=0) + \
            datetime.timedelta(minutes=1)

        # Try each minute until we find a match
        for _ in range(525600):  # Maximum number of minutes in a year
            minute = dt.minute
            hour = dt.hour
            day = dt.day
            month = dt.month
            day_of_week = dt.weekday()  # Monday is 0

            if (
                minute in self.minute
                and hour in self.hour
                and day in self.day
                and month in self.month
                and day_of_week in self.day_of_week
            ):
                return dt.timestamp()

            dt += datetime.timedelta(minutes=1)

        # If we get here, something went wrong
        raise ValueError("Could not find a valid next run time within a year.")

    def reschedule(self) -> None:
        """Update the next run time for this cron task."""
        self.next_run = self._calculate_next_run(time.time())

    def to_dict(self) -> Dict:
        """
        Convert the cron task to a dictionary.

        Returns:
            Dict: Dictionary representation of the cron task.
        """
        result = super().to_dict()
        result.update(
            {
                "cron_expr": self.cron_expr,
                "minute": list(self.minute),
                "hour": list(self.hour),
                "day": list(self.day),
                "month": list(self.month),
                "day_of_week": list(self.day_of_week),
            }
        )
        return result


class EventTask(Task):
    """
    A task triggered by system events.

    Attributes:
        event_type (str): Type of event to listen for.
        event_filter (Callable): Function to filter events.
        max_executions (Optional[int]): Maximum number of times to execute.
    """

    def __init__(
        self,
        function: Callable,
        event_type: str,
        event_filter: Callable = None,
        max_executions: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize a new EventTask.

        Args:
            function (Callable): The function to execute.
            event_type (str): Type of event to listen for.
            event_filter (Callable, optional): Function to filter events.
            max_executions (Optional[int], optional): Maximum number of times to execute.
            **kwargs: Additional arguments for the Task class.
        """
        super().__init__(function, **kwargs)
        self.event_type = event_type
        self.event_filter = event_filter
        self.max_executions = max_executions
        self.execution_count = 0

    def matches_event(self, event: Dict) -> bool:
        """
        Check if this task matches an event.

        Args:
            event (Dict): The event to check.

        Returns:
            bool: True if the task should be triggered by this event.
        """
        if event.get("type") != self.event_type:
            return False

        if self.event_filter is not None:
            return self.event_filter(event)

        return True

    def execute_for_event(self, event: Dict) -> Any:
        """
        Execute this task for a specific event.

        Args:
            event (Dict): The event that triggered the task.

        Returns:
            Any: The result of the task execution.
        """
        # Check if we've reached the maximum executions
        if (
            self.max_executions is not None
            and self.execution_count >= self.max_executions
        ):
            self.status = "max_executions_reached"
            return None

        # Add the event to the kwargs
        kwargs = self.kwargs.copy()
        kwargs["event"] = event

        # Save the original function and args
        original_function = self.function
        original_args = self.args
        original_kwargs = self.kwargs

        try:
            # Set the modified function parameters
            self.function = self.function
            self.args = self.args
            self.kwargs = kwargs

            # Execute the task
            result = self.execute()

            # Increment execution count
            self.execution_count += 1

            return result
        finally:
            # Restore the original function parameters
            self.function = original_function
            self.args = original_args
            self.kwargs = original_kwargs

    def to_dict(self) -> Dict:
        """
        Convert the event task to a dictionary.

        Returns:
            Dict: Dictionary representation of the event task.
        """
        result = super().to_dict()
        result.update(
            {
                "event_type": self.event_type,
                "has_filter": self.event_filter is not None,
                "max_executions": self.max_executions,
                "execution_count": self.execution_count,
            }
        )
        return result


class Scheduler:
    """
    Task scheduler for the AI system.

    This class manages the scheduling and execution of tasks.

    Attributes:
        task_queue (List): Priority queue of scheduled tasks.
        event_tasks (Dict[str, List[EventTask]]): Tasks triggered by events.
        running_tasks (Dict[str, threading.Thread]): Currently running tasks.
        completed_tasks (List[Dict]): History of completed tasks.
        running (bool): Whether the scheduler is running.
    """

    def __init__(self):
        """Initialize a new Scheduler."""
        self.task_queue = []  # heap queue
        self.event_tasks = {}  # event_type -> [tasks]
        self.running_tasks = {}  # task_id -> thread
        self.completed_tasks = []
        self.task_results = {}  # task_id -> result
        self.lock = threading.RLock()
        self.event_queue = queue.Queue()
        self.running = False
        self.main_thread = None
        self.initialized = False

    def start(self):
        """Start the scheduler."""
        with self.lock:
            if self.running:
                return

            self.running = True
            self.main_thread = threading.Thread(target=self._main_loop)
            self.main_thread.daemon = True
            self.main_thread.start()

            logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler."""
        with self.lock:
            if not self.running:
                return

            self.running = False
            if self.main_thread:
                self.main_thread.join(timeout=1.0)
                self.main_thread = None

            logger.info("Scheduler stopped")

    def _main_loop(self):
        """Main scheduler loop."""
        while self.running:
            try:
                self._process_due_tasks()
                self._process_events()
                self._cleanup_completed_tasks()

                # Sleep until the next task is due or a small amount of time
                next_task_time = self._get_next_task_time()
                if next_task_time is not None:
                    sleep_time = max(
                        0.1, min(1.0, next_task_time - time.time()))
                else:
                    sleep_time = 1.0

                time.sleep(sleep_time)
            except Exception as e:
                logger.error(f"Error in scheduler main loop: {str(e)}")
                time.sleep(1.0)  # Avoid tight error loops

    def _get_next_task_time(self) -> Optional[float]:
        """
        Get the time when the next task is due.

        Returns:
            Optional[float]: The time of the next task, or None if no tasks.
        """
        with self.lock:
            if not self.task_queue:
                return None
            return self.task_queue[0].next_run

    def _process_due_tasks(self):
        """Process tasks that are due for execution."""
        with self.lock:
            now = time.time()

            # Process tasks that are due
            while self.task_queue and self.task_queue[0].next_run <= now:
                task = heapq.heappop(self.task_queue)

                # Start a thread to execute the task
                thread = threading.Thread(
                    target=self._execute_task, args=(task,))
                thread.daemon = True
                thread.start()

                # Track the running task
                self.running_tasks[task.id] = thread

                # If recurring, reschedule
                if task.recurring:
                    task.reschedule()
                    heapq.heappush(self.task_queue, task)

    def _process_events(self):
        """Process events from the event queue."""
        # Process all events in the queue
        while not self.event_queue.empty():
            try:
                event = self.event_queue.get_nowait()
                self._handle_event(event)
                self.event_queue.task_done()
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"Error processing event: {str(e)}")

    def _handle_event(self, event: Dict):
        """
        Handle an event by triggering matching tasks.

        Args:
            event (Dict): The event to handle.
        """
        event_type = event.get("type")
        if not event_type:
            logger.warning(f"Event without type: {event}")
            return

        with self.lock:
            # Find matching tasks
            matching_tasks = []

            # Check specific event type tasks
            if event_type in self.event_tasks:
                for task in self.event_tasks[event_type]:
                    if task.matches_event(event):
                        matching_tasks.append(task)

            # Check wildcard tasks
            if "*" in self.event_tasks:
                for task in self.event_tasks["*"]:
                    if task.matches_event(event):
                        matching_tasks.append(task)

            # Execute matching tasks
            for task in matching_tasks:
                thread = threading.Thread(
                    target=self._execute_event_task, args=(task, event)
                )
                thread.daemon = True
                thread.start()

                # Track the running task
                self.running_tasks[task.id] = thread

    def _execute_task(self, task: Task):
        """
        Execute a task and handle the result.

        Args:
            task (Task): The task to execute.
        """
        start_time = time.time()
        logger.debug(f"Executing task {task.name} ({task.id})")

        try:
            result = task.execute()
            end_time = time.time()
            execution_time = end_time - start_time

            with self.lock:
                self.task_results[task.id] = {
                    "status": "success",
                    "result": result,
                    "execution_time": execution_time,
                }

                # Add to completed tasks history
                self.completed_tasks.append(
                    {
                        "task_id": task.id,
                        "task_name": task.name,
                        "status": "success",
                        "start_time": start_time,
                        "end_time": end_time,
                        "execution_time": execution_time,
                    }
                )

            logger.debug(
                f"Task {task.name} completed in {execution_time:.2f}s")

        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time

            with self.lock:
                self.task_results[task.id] = {
                    "status": "error",
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "execution_time": execution_time,
                }

                # Add to completed tasks history
                self.completed_tasks.append(
                    {
                        "task_id": task.id,
                        "task_name": task.name,
                        "status": "error",
                        "error": str(e),
                        "start_time": start_time,
                        "end_time": end_time,
                        "execution_time": execution_time,
                    }
                )

            logger.error(f"Task {task.name} failed: {str(e)}")

        finally:
            # Remove from running tasks
            with self.lock:
                if task.id in self.running_tasks:
                    del self.running_tasks[task.id]

    def _execute_event_task(self, task: EventTask, event: Dict):
        """
        Execute an event task.

        Args:
            task (EventTask): The task to execute.
            event (Dict): The event that triggered the task.
        """
        start_time = time.time()
        logger.debug(
            f"Executing event task {task.name} ({task.id}) for event {event.get('type')}"
        )

        try:
            result = task.execute_for_event(event)
            end_time = time.time()
            execution_time = end_time - start_time

            with self.lock:
                self.task_results[task.id] = {
                    "status": "success",
                    "result": result,
                    "execution_time": execution_time,
                    "event": event,
                }

                # Add to completed tasks history
                self.completed_tasks.append(
                    {
                        "task_id": task.id,
                        "task_name": task.name,
                        "status": "success",
                        "start_time": start_time,
                        "end_time": end_time,
                        "execution_time": execution_time,
                        "event_type": event.get("type"),
                    }
                )

            logger.debug(
                f"Event task {task.name} completed in {execution_time:.2f}s")

        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time

            with self.lock:
                self.task_results[task.id] = {
                    "status": "error",
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "execution_time": execution_time,
                    "event": event,
                }

                # Add to completed tasks history
                self.completed_tasks.append(
                    {
                        "task_id": task.id,
                        "task_name": task.name,
                        "status": "error",
                        "error": str(e),
                        "start_time": start_time,
                        "end_time": end_time,
                        "execution_time": execution_time,
                        "event_type": event.get("type"),
                    }
                )

            logger.error(f"Event task {task.name} failed: {str(e)}")

        finally:
            # Remove from running tasks
            with self.lock:
                if task.id in self.running_tasks:
                    del self.running_tasks[task.id]

    def _cleanup_completed_tasks(self):
        """Clean up the completed tasks history to prevent unbounded growth."""
        with self.lock:
            max_history = 1000  # Maximum number of completed tasks to keep
            if len(self.completed_tasks) > max_history:
                self.completed_tasks = self.completed_tasks[-max_history:]

            # Clean up old task results
            max_age = 3600  # 1 hour
            now = time.time()
            old_results = []

            for task_id, result in self.task_results.items():
                if result.get("end_time", now) < now - max_age:
                    old_results.append(task_id)

            for task_id in old_results:
                del self.task_results[task_id]

    def schedule_task(self, task: Task) -> str:
        """
        Schedule a task for execution.

        Args:
            task (Task): The task to schedule.

        Returns:
            str: The task ID.
        """
        with self.lock:
            if isinstance(task, ScheduledTask):
                heapq.heappush(self.task_queue, task)
            elif isinstance(task, EventTask):
                event_type = task.event_type
                if event_type not in self.event_tasks:
                    self.event_tasks[event_type] = []
                self.event_tasks[event_type].append(task)
            else:
                # For immediate execution, create a scheduled task
                now = time.time()
                scheduled_task = ScheduledTask(
                    task.function,
                    now,
                    args=task.args,
                    kwargs=task.kwargs,
                    name=task.name,
                )
                heapq.heappush(self.task_queue, scheduled_task)
                return scheduled_task.id

            logger.info(f"Scheduled task {task.name} ({task.id})")
            return task.id

    def schedule_at(
        self,
        function: Callable,
        scheduled_time: Union[float, datetime.datetime],
        recurring: bool = False,
        interval: Optional[float] = None,
        **kwargs,
    ) -> str:
        """
        Schedule a function at a specific time.

        Args:
            function (Callable): The function to execute.
            scheduled_time (Union[float, datetime.datetime]): When to execute the function.
            recurring (bool, optional): Whether the task should recur.
            interval (Optional[float], optional): Interval for recurring tasks.
            **kwargs: Additional arguments for the ScheduledTask.

        Returns:
            str: The task ID.
        """
        # Convert datetime to timestamp if needed
        if isinstance(scheduled_time, datetime.datetime):
            scheduled_time = scheduled_time.timestamp()

        task = ScheduledTask(
            function=function,
            scheduled_time=scheduled_time,
            recurring=recurring,
            interval=interval,
            **kwargs,
        )

        return self.schedule_task(task)

    def schedule_interval(
        self, function: Callable, interval: float, start_now: bool = False, **kwargs
    ) -> str:
        """
        Schedule a function to run at regular intervals.

        Args:
            function (Callable): The function to execute.
            interval (float): Interval in seconds.
            start_now (bool, optional): Whether to run the task immediately.
            **kwargs: Additional arguments for the ScheduledTask.

        Returns:
            str: The task ID.
        """
        now = time.time()
        scheduled_time = now if start_now else now + interval

        return self.schedule_at(
            function=function,
            scheduled_time=scheduled_time,
            recurring=True,
            interval=interval,
            **kwargs,
        )

    def schedule_cron(self, function: Callable, cron_expr: str, **kwargs) -> str:
        """
        Schedule a function using cron syntax.

        Args:
            function (Callable): The function to execute.
            cron_expr (str): Cron expression.
            **kwargs: Additional arguments for the CronTask.

        Returns:
            str: The task ID.
        """
        task = CronTask(function=function, cron_expr=cron_expr, **kwargs)

        return self.schedule_task(task)

    def schedule_event(
        self,
        function: Callable,
        event_type: str,
        event_filter: Callable = None,
        **kwargs,
    ) -> str:
        """
        Schedule a function to run in response to events.

        Args:
            function (Callable): The function to execute.
            event_type (str): Type of event to listen for.
            event_filter (Callable, optional): Function to filter events.
            **kwargs: Additional arguments for the EventTask.

        Returns:
            str: The task ID.
        """
        task = EventTask(
            function=function,
            event_type=event_type,
            event_filter=event_filter,
            **kwargs,
        )

        return self.schedule_task(task)

    def publish_event(self, event: Dict) -> None:
        """
        Publish an event to the scheduler.

        Args:
            event (Dict): The event to publish.
        """
        self.event_queue.put(event)

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a scheduled task.

        Args:
            task_id (str): ID of the task to cancel.

        Returns:
            bool: True if the task was cancelled, False otherwise.
        """
        with self.lock:
            # Check the task queue
            for i, task in enumerate(self.task_queue):
                if task.id == task_id:
                    # Remove the task from the queue
                    self.task_queue[i] = self.task_queue[-1]
                    self.task_queue.pop()
                    heapq.heapify(self.task_queue)
                    logger.info(f"Cancelled scheduled task {task_id}")
                    return True

            # Check event tasks
            for event_type, tasks in self.event_tasks.items():
                for i, task in enumerate(tasks):
                    if task.id == task_id:
                        tasks.pop(i)
                        logger.info(f"Cancelled event task {task_id}")
                        return True

            # Check running tasks
            if task_id in self.running_tasks:
                # We can't really cancel a running thread safely
                # Just log that we tried
                logger.warning(f"Attempted to cancel running task {task_id}")
                return False

            logger.warning(f"Task {task_id} not found for cancellation")
            return False

    def get_task_result(self, task_id: str) -> Optional[Dict]:
        """
        Get the result of a task.

        Args:
            task_id (str): ID of the task.

        Returns:
            Optional[Dict]: The task result, or None if not found.
        """
        with self.lock:
            return self.task_results.get(task_id)

    def get_scheduled_tasks(self) -> List[Dict]:
        """
        Get all scheduled tasks.

        Returns:
            List[Dict]: Information about scheduled tasks.
        """
        with self.lock:
            result = []

            # Add tasks from the queue
            for task in self.task_queue:
                result.append(
                    {
                        "id": task.id,
                        "name": task.name,
                        "type": "scheduled",
                        "next_run": task.next_run,
                        "recurring": task.recurring,
                        "status": task.status,
                    }
                )

            # Add event tasks
            for event_type, tasks in self.event_tasks.items():
                for task in tasks:
                    result.append(
                        {
                            "id": task.id,
                            "name": task.name,
                            "type": "event",
                            "event_type": event_type,
                            "status": task.status,
                        }
                    )

            return result

    def get_running_tasks(self) -> List[Dict]:
        """
        Get currently running tasks.

        Returns:
            List[Dict]: Information about running tasks.
        """
        with self.lock:
            result = []

            for task_id, thread in self.running_tasks.items():
                result.append(
                    {
                        "id": task_id,
                        "thread_name": thread.name,
                        "thread_alive": thread.is_alive(),
                        "thread_daemon": thread.daemon,
                    }
                )

            return result

    def get_completed_tasks(self, limit: int = 100) -> List[Dict]:
        """
        Get the history of completed tasks.

        Args:
            limit (int, optional): Maximum number of tasks to return.

        Returns:
            List[Dict]: Information about completed tasks.
        """
        with self.lock:
            return list(reversed(self.completed_tasks[-limit:]))

    def get_stats(self) -> Dict:
        """
        Get scheduler statistics.

        Returns:
            Dict: Scheduler statistics.
        """
        with self.lock:
            return {
                "scheduled_tasks": len(self.task_queue),
                "event_tasks": sum(len(tasks) for tasks in self.event_tasks.values()),
                "running_tasks": len(self.running_tasks),
                "completed_tasks": len(self.completed_tasks),
                "successful_tasks": len(
                    [t for t in self.completed_tasks if t.get(
                        "status") == "success"]
                ),
                "failed_tasks": len(
                    [t for t in self.completed_tasks if t.get(
                        "status") == "error"]
                ),
                "event_types": list(self.event_tasks.keys()),
            }


# Global scheduler instance
_scheduler = None


def get_scheduler() -> Scheduler:
    """
    Get the global scheduler instance.

    Returns:
        Scheduler: The global scheduler.
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler()
    return _scheduler


def schedule_task(function: Callable, **kwargs) -> str:
    """
    Schedule a function for immediate execution.

    Args:
        function (Callable): The function to execute.
        **kwargs: Additional arguments for the Task.

    Returns:
        str: The task ID.
    """
    scheduler = get_scheduler()
    task = Task(function, **kwargs)
    return scheduler.schedule_task(task)


def schedule_at(
    function: Callable, time_at: Union[float, datetime.datetime], **kwargs
) -> str:
    """
    Schedule a function at a specific time.

    Args:
        function (Callable): The function to execute.
        time_at (Union[float, datetime.datetime]): When to execute the function.
        **kwargs: Additional arguments for the ScheduledTask.

    Returns:
        str: The task ID.
    """
    return get_scheduler().schedule_at(function, time_at, **kwargs)


def schedule_interval(function: Callable, interval: float, **kwargs) -> str:
    """
    Schedule a function to run at regular intervals.

    Args:
        function (Callable): The function to execute.
        interval (float): Interval in seconds.
        **kwargs: Additional arguments for the ScheduledTask.

    Returns:
        str: The task ID.
    """
    return get_scheduler().schedule_interval(function, interval, **kwargs)


def schedule_cron(function: Callable, cron_expr: str, **kwargs) -> str:
    """
    Schedule a function using cron syntax.

    Args:
        function (Callable): The function to execute.
        cron_expr (str): Cron expression.
        **kwargs: Additional arguments for the CronTask.

    Returns:
        str: The task ID.
    """
    return get_scheduler().schedule_cron(function, cron_expr, **kwargs)


def schedule_event(function: Callable, event_type: str, **kwargs) -> str:
    """
    Schedule a function to run in response to events.

    Args:
        function (Callable): The function to execute.
        event_type (str): Type of event to listen for.
        **kwargs: Additional arguments for the EventTask.

    Returns:
        str: The task ID.
    """
    return get_scheduler().schedule_event(function, event_type, **kwargs)


def cancel_task(task_id: str) -> bool:
    """
    Cancel a scheduled task.

    Args:
        task_id (str): ID of the task to cancel.

    Returns:
        bool: True if the task was cancelled, False otherwise.
    """
    return get_scheduler().cancel_task(task_id)


def publish_event(event: Dict) -> None:
    """
    Publish an event to the scheduler.

    Args:
        event (Dict): The event to publish.
    """
    get_scheduler().publish_event(event)


def get_task_result(task_id: str) -> Optional[Dict]:
    """
    Get the result of a task.

    Args:
        task_id (str): ID of the task.

    Returns:
        Optional[Dict]: The task result, or None if not found.
    """
    return get_scheduler().get_task_result(task_id)


def initialize_scheduler():
    """Initialize the scheduler."""
    scheduler = get_scheduler()
    if scheduler.initialized:
        return

    # Start the scheduler
    scheduler.start()
    scheduler.initialized = True
    logger.info("Scheduler initialized")


# Decorator for creating scheduled tasks
def scheduled_task(**kwargs):
    """
    Decorator for creating scheduled tasks.

    Args:
        **kwargs: Arguments for the schedule_task function.

    Returns:
        Callable: Decorator function.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)

        # Schedule the task
        task_id = schedule_task(func, **kwargs)
        wrapper.task_id = task_id

        return wrapper

    return decorator


# Initialize the scheduler
initialize_scheduler()