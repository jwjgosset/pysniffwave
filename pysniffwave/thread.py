'''
Thread library
==============

Stoppable thread library for infinite running threads.

..  codeauthor:: Charles Blais
'''
import logging
import threading
import signal


class StoppableThread(threading.Thread):
    '''
    Abstract for workers
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stop_event = threading.Event()
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def stop(self, *args):
        '''
        Stop the thread by setting the thread event
        '''
        logging.info('Request received to stop thread')
        self._stop_event.set()

    @property
    def is_stopped(self) -> bool:
        '''
        Check if we identified the thread to stop

        :rtype: bool
        '''
        return self._stop_event.is_set()
