'''
HDF5 Client
===========

Library for simplify reading/writing HDF5 files for the purpose
of sniffwave.

Writting content to files is based on the current time.  Entries are
added based on now.  The structure of the HDF5 file archive is as:

    YYYY/mm/dd/sniffwave_YYYYmmdd_HH.h5

where:

    YYYY = year
    mm = month
    dd = day
    HH = hour

The content of the HDF5 is just two tables based on the two types of response
returned by the sniffwave utility.

1. stats = general status
2. errors = special conditions (out-of-order, gap, overlap)

Their table structure matches the same as the sql database example.

.. see:: pysniffwave.sql.models or pysniffwave.sniffwave.parser

The reader will return a pd.Dataframe based on the conditions sent.

..  codeauthor:: Charles Blais
'''
import logging
from typing import Optional, Union
import datetime
from pathlib import Path

import pandas as pd
pd.set_option('display.max_rows', None)

MIN_ITEMSIZE_CHANNELS = {
    'network': 2,
    'station': 5,
    'location': 2,
    'channel': 3,
}
MIN_ITEMSIZE_ERRORS = {
    **MIN_ITEMSIZE_CHANNELS,
    'error': 20,
}
DTYPES = {
    'n_samples': 'uint16',
    'n_bytes': 'uint16',
    'sample_rate': 'float32',
    'data_latency': 'float32',
    'feeding_latency': 'float32',
}


class Client(object):
    '''
    See module description.  NOTE: client is only designed to support
    reading or writing (not both).

    :param str directory: directory where information is saved
        (default: is cwd)
    '''
    def __init__(
        self,
        directory: Optional[Union[str, Path]] = None
    ):
        self.directory = Path.cwd() if directory is None else Path(directory)
        self._store: Optional[pd.HDFStore] = None

    def get_filename(self, at: datetime.datetime) -> Path:
        '''
        Generate filename based on the at time and the directory
        stored in object state

        :type at: class::`datetime.datetime`
        :param at: current timestamp used to generate the filename

        :rtype: Path
        :returns: filename
        '''
        return self.directory.joinpath(
            at.strftime('%Y'),
            at.strftime('%m'),
            at.strftime('%d'),
            f'sniffwave_{at.strftime("%Y%m%d_%H")}.h5')

    def get_store(self, at: datetime.datetime, **kwargs) -> pd.HDFStore:
        '''
        Set the hdf5 store based on the at time and the directory
        stored in object state.

        :type at: class::`datetime.datetime`
        :param at: current timestamp used to generate the filename

        :param kwargs: any paramters to pass to pd.HDFStore

        :return: :class:`pd.HDFStore`
        '''
        filename = self.get_filename(at)
        store_props = {
            'path': filename,
            'libver': 'latest',
            'swmr': True,
            'complib': 'zlib',
            'complevel': 9,
            **kwargs
        }

        if self._store is None:
            logging.info(f'HDF5 not set, open new store at {filename}')
        elif self._store.filename == filename:
            logging.debug(f'HDF5 has not change: {filename}')
            return self._store
        else:
            logging.debug(f'HDF5 has changed change: {filename}')
            self._store.close()
        # make the directory if it doesn't exist
        filename.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        self._store = pd.HDFStore(**store_props)
        return self._store

    @staticmethod
    def _format_df(
        df: pd.DataFrame
    ) -> None:
        '''
        Convert the types of the dataframe
        '''
        for column in df.columns:
            if column in DTYPES:
                df[column] = df[column].astype(DTYPES[column])

    def write(
        self,
        df: pd.DataFrame,
        at: datetime.datetime = datetime.datetime.now()
    ):
        '''
        Insert the dataframe into an HDF5 daily file
        based on the "at" time.

        :param df: dataframe to write
        :type at: class::`datetime.datetime`
        :param at: current timestamp used to generate the filename
        '''
        store = self.get_store(at, mode='a')
        Client._format_df(df)
        logging.debug(f'Writing following df\n:{df}')
        store.append(
            'channels', df,
            format='t',
            min_itemsize=MIN_ITEMSIZE_CHANNELS,
            index=False,
            data_columns=True)
        logging.debug('df write complete')

    def write_error(
        self,
        df: pd.DataFrame,
        at: datetime.datetime = datetime.datetime.now()
    ):
        '''
        Insert the dataframe into an HDF5 daily file
        based on the "at" time.

        :param df: dataframe to write

        :type at: class::`datetime.datetime`
        :param at: current timestamp used to generate the filename
        '''
        store = self.get_store(at, mode='a')
        Client._format_df(df)
        logging.debug(f'Writing following error df\n:{df}')
        store.append(
            'errors', df,
            format='t',
            min_itemsize=MIN_ITEMSIZE_ERRORS,
            index=False,
            data_columns=True)
        logging.debug('error df write complete')

    def close(self):
        '''
        Close the HDF5 store befor exiting
        '''
        if self._store is not None:
            self._store.close()

    def __del__(self):
        '''Desctructor'''
        self.close()
