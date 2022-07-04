'''
..  codeauthor:: Charles Blais
'''
import logging
from typing import Optional, List
import time
import datetime

import pandas as pd

from .worker import Worker

from pysniffwave.hdf5.client import Client

from pysniffwave.sniffwave.parser import Channel, ChannelError

# from pysniffwave.nagios.store import get_arrival_file, store_latest_timestamp


class HDF5Worker(Worker):
    '''
    HDF5 worker
    ===========
    '''
    def __init__(
        self,
        *args,
        directory: Optional[str] = None,
        **kwargs,
    ):
        '''
        :param str directory: location where to store files
        '''
        super().__init__(*args, **kwargs)
        self.directory = directory

    def run(self):
        '''
        SQLite thread start.  It will first initation the connection
        '''
        if self.queue is None:
            raise ValueError('queue was not set in worker')

        # initialize client for HDF5 storage
        client = Client(directory=self.directory)

        # Ensure the latest_timestamp file exists
        # if self.directory is not None:
        #     arrival_file = get_arrival_file(directory=self.directory)

        while not self.is_stopped:
            logging.debug(f'Sleeping for {self.timeout}s')
            time.sleep(self.timeout)
            qsize = self.queue.qsize()

            if(qsize == 0):
                logging.error('No message in queue for worker, stop')
                break

            channel: List[Channel] = []
            channel_errors: List[ChannelError] = []
            logging.info(f'Processing {qsize} in queue')
            for _ in range(qsize - 1):
                item = self.queue.get()
                if isinstance(item, ChannelError):
                    channel_errors.append(item)
                else:
                    channel.append(item)
                    # Store latency and timestamp for nagios check
                    # # They end up like 8 minutes behind (and counting)
                    # if self.directory is not None:
                    #     store_latest_timestamp(
                    #         file_path=arrival_file,
                    #         channel_stats=item
                    #     )

            if len(channel):
                client.write(
                    pd.DataFrame(channel),
                    at=datetime.datetime.now())
            if len(channel_errors):
                client.write_error(
                    pd.DataFrame(channel_errors),
                    at=datetime.datetime.now())

        # Ensure any open HDF5 files are closed before stopping
        client.close()
