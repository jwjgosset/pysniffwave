from datetime import datetime
import pathlib
from dataclasses import dataclass
from pysniffwave.sniffwave.parser import Channel
import logging
from typing import Dict, List, Union


@dataclass
class ArrivalStat:
    '''
    Class for storing arrival information for a channel

    Properties
    ----------
    channel: str
        The scnl format name for the channel

    start_time: datetime
        The start time of the last sample recorded by sniffwave

    data_latency: float
        The data latency of the last sample recorded by sniffwave

    feeding_latency: float
        The feeding latency of the last sample recorded by sniffwave
    '''
    channel: str
    start_time: datetime
    data_latency: float
    feeding_latency: float

    def total_latency(self) -> float:
        '''
        Return total latency
        '''
        return self.data_latency + self.feeding_latency

    def __gt__(self, other) -> bool:
        '''
        Compare based on total latency
        '''
        return self.total_latency() > other.total_latency()

    def __lt__(self, other) -> bool:
        '''
        Compare based on total latency
        '''
        return self.total_latency() < other.total_latency()

    def __str__(self) -> str:
        '''
        Return string format for Nagios check results
        '''
        latency = self.total_latency()
        return f"{self.channel}, {self.start_time.isoformat()}, {latency}s"


class LatestArrivalWorker(Dict[str, ArrivalStat]):
    ''' Class for managing arrival statistics'''
    def __init__(
        self,
        filepath: Union[str, pathlib.Path],
        changes: int
    ):
        '''
        Initialize the object by ensuring the output file exists, and reading
        its contents if it does

        Parameters
        ----------
        filepath: str | Path
            String or Path object pointing at the desired file location

        changes: int
            The number of changes before the file is updated
        '''
        # Convert a str path to a pathlib Path
        if isinstance(filepath, str):
            filepath = pathlib.Path(filepath)

        self.path = filepath

        # Open the file to initialize the dictionary
        if filepath.exists():

            # Load the lines from file
            with open(filepath, mode='r') as f:
                lines = f.readlines()

                # Populate the internal dictionary of ArrivalStat objects with
                # the information from file
                for line in lines:
                    if line != '\n':
                        channel, start_timestring, data_latency, \
                            feeding_latency = line.split(',')

                        # Handle strings with or without nanoseconds
                        try:
                            start_time = datetime.strptime(
                                start_timestring, '%Y-%m-%d %H:%M:%S.%f')
                        except ValueError:
                            start_time = datetime.strptime(
                                start_timestring, '%Y-%m-%d %H:%M:%S')

                        # Channel code is used as dictionary key so data can
                        # be easily replaced
                        self[channel] = ArrivalStat(
                            channel=channel,
                            start_time=start_time,
                            data_latency=float(data_latency),
                            feeding_latency=float(feeding_latency))
        else:
            # Create a new file if it doesn't exist
            filepath.touch(mode=0o644)
            logging.warning(f"File {str(filepath)} did not exist, created")

        # Initialize counter of changes
        self.changes = changes
        self.currentchange = 0

    def add_latest_timestamp(
        self,
        channel_stats: Union[List[Channel], Channel]
    ):
        '''
        Stores the output of the sniffwave parser

        Parameters
        ----------
        channel_stats: Channel | List[Channel]
            A single or list of Channel objects from the pysniffwave parser
        '''
        # Ensure that channel_stats is iterable
        if isinstance(channel_stats, Channel):
            channel_stats = [channel_stats]

        for channel in channel_stats:
            # Convert scnl to string
            scnl = (f"{channel['network']}.{channel['station']}." +
                    f"{channel['location']}.{channel['channel']}")
            # Add timestamp to string
            self[scnl] = ArrivalStat(
                channel=scnl,
                start_time=channel['start_time'],
                data_latency=channel['data_latency'],
                feeding_latency=channel['feeding_latency']
            )
        self.currentchange += 1

        if self.currentchange >= self.changes:
            self.currentchange = 0
            self.write_to_file()

    def write_to_file(
            self,
    ):
        '''
        Write the recorded arrival statistics to file
        '''
        lines: str = ''

        # Convert the internal dictionary to a string format
        for channel in self:
            lines += (f"{channel},{self[channel].start_time}," +
                      f"{self[channel].data_latency}," +
                      f"{self[channel].feeding_latency}\n")

        # Write to file, overwriting it's contents
        with open(str(self.path), mode='w') as f:
            f.write(lines)

    def sort_list(self) -> List[ArrivalStat]:
        '''
        Returns a sorted list of ArrivalStatistics, sorted by highest latency
        first
        '''
        stat_list = list(self.values())
        stat_list.sort(key=lambda x: x.total_latency(), reverse=True)
        return stat_list
