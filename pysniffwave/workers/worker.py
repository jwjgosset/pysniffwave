'''
..  codeauthor:: Charles Blais
'''

from pysniffwave.thread import StoppableThread
import queue

from typing import Optional


class Worker(StoppableThread):
    '''
    Abstract for workers
    '''
    def __init__(
        self,
        queue: Optional[queue.Queue] = None,
        timeout: float = 10,
        *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.queue = queue
        self.timeout = timeout

    def set_queue(self, value: queue.Queue):
        self.queue = value

    def set_timeout(self, value: float):
        self.timeout = value
