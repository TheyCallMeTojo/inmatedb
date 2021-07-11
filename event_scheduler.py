import datetime
import sched
import time
from typing import Callable, NamedTuple

from logger.inmatedb_logger import InatedbLogger


class TimeSlot(NamedTuple):
    day_offset: int = 0
    hour_offset: int = 0
    minute_offset: int = 0
    second_offset: int = 0

    def __repr__(self):       
        return self.as_datetime.strftime("%m/%d/%Y %I:%M:%S %p")

    @property
    def as_datetime(self):
        date_t = datetime.datetime.now()
        date_t += datetime.timedelta(days=self.day_offset)
        date_t += datetime.timedelta(hours=self.hour_offset)
        date_t += datetime.timedelta(minutes=self.minute_offset)
        date_t += datetime.timedelta(seconds=self.second_offset)
        return date_t

    @property
    def time_until_event(self):
        date_now = datetime.datetime.now()
        timedelta = self.as_datetime - date_now
        return timedelta.seconds

class ScheduleItem(NamedTuple):
    start: TimeSlot
    callback: Callable
    callback_args: tuple = ()

    def __repr__(self):
        message = f"action `{self.callback.__qualname__}` scheduled for: {self.start}"
        return message

class EventScheduler:
    def __init__(self, silent=False):
        self.silent = silent
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.logger = InatedbLogger()

    def schedule_event(self, sched_item, scheduler=None):
        if scheduler is None:
            scheduler = self.scheduler
            self.last_schedule_item = sched_item

        if not self.silent:
            self.logger.info(sched_item)
        
        delay = sched_item.start.time_until_event
        callback = sched_item.callback
        args = sched_item.callback_args
        scheduler.enter(delay, 1, callback, argument=args)

    def clear_schedule(self):
        for event in self.scheduler.queue:
            self.scheduler.cancel(event)

    def run_schedule(self):
        self.scheduler.run()
