'''
..  codeauthor:: Charles Blais
'''
import logging
import queue

from .worker import Worker

from pysniffwave.sql.client import Client


class SQLWorker(Worker):
    '''
    SQLite worker
    =============
    '''
    def run(self):
        '''
        SQLite thread start.  It will first initation the connection
        '''
        if self.queue is None:
            raise ValueError('queue was not set in worker')

        # initialize client connection
        client = Client()

        while not self.is_stopped:
            logging.debug('Waiting for message in queue')
            try:
                client.insert(
                    self.queue.get(timeout=self.timeout)
                )
            except queue.Empty:
                logging.error('Worker timeout (no message), stop')
                self.stop()
