'''
..  codeauthor:: Charles Blais
'''
import logging
import queue

from .worker import Worker


class PrintWorker(Worker):
    '''
    Standard print worker
    '''
    def run(self):
        '''
        Print information to stdout
        '''
        if self.queue is None:
            raise ValueError('queue was not set in worker')

        while not self.is_stopped:
            logging.debug('Waiting for message in queue')
            try:
                data = self.queue.get(timeout=self.timeout)
                print(data)
            except queue.Empty:
                logging.error('Worker timeout (no message), stop')
                self.stop()
