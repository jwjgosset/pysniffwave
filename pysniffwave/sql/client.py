'''
Database handle
===============

..  codeauthor:: Charles Blais
'''
import logging
from typing import Union, Optional

import datetime

import pandas as pd

import pysniffwave.sniffwave.parser as parser

from .database import init_db, db_session
from .models import Channel, ChannelError, Base


class Client(object):
    '''
    Client for sql database
    '''
    def __init__(self):
        # Initialize database session
        init_db()

    def _find(
        self,
        Table: Base,
        starttime: datetime.datetime,
        endtime: datetime.datetime,
        network: Optional[str] = None,
        station: Optional[str] = None,
        location: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> pd.DataFrame:
        '''
        Search the stat database based on parameters

        :param starttime: start time of insert
        :param endtime: end time of insert
        :param str network: network code
        :param str station: station code
        :param str location: location code
        :param str channel: channel code

        :rtype: pd.Dataframe
        '''
        query = db_session.query(Table).filter(
            Table.recorded_at.between(starttime, endtime)
        )
        if network:
            query.filter(Table.network == network)
        if station:
            query.filter(Table.station == station)
        if location:
            query.filter(Table.location == location)
        if channel:
            query.filter(Table.channel == channel)
        return pd.DataFrame([stat.__dict__ for stat in query.all()])

    def find(self, *args, **kwargs) -> pd.DataFrame:
        '''
        Find the channel

        .. see:: _find
        '''
        return self._find(
            Channel,
            *args,
            **kwargs,
        )

    def find_error(self, *args, **kwargs) -> pd.DataFrame:
        '''
        Find the special stat condition

        .. see:: _find
        '''
        return self._find(
            ChannelError,
            *args,
            **kwargs,
        )

    def insert_channel_error(
        self,
        channel: parser.ChannelError
    ) -> None:
        '''
        Insert ChannelError in database
        '''
        entry = ChannelError(**channel)
        logging.info(f'Adding new channel error {entry}')
        db_session.add(entry)
        db_session.commit()

    def insert_channel(
        self,
        channel: parser.Channel
    ) -> None:
        '''
        Insert Channel in database
        '''
        entry = Channel(**channel)
        logging.info(f'Adding new channel {entry}')
        db_session.add(entry)
        db_session.commit()

    def insert(
        self,
        channel: Union[parser.Channel, parser.ChannelError]
    ) -> None:
        '''
        Insert pick or picks in the database
        '''
        if isinstance(channel, parser.ChannelError):
            return self.insert_channel_error(channel)
        return self.insert_channel(channel)
