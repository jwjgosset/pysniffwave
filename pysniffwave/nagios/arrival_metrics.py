from datetime import datetime
import pathlib
from dataclasses import dataclass
from pysniffwave.nagios.check_arrival import ArrivalThresholds
from pysniffwave.nagios.models import NagiosOutputCode, NagiosRange
from pysniffwave.sniffwave.parser import Channel
import logging
from typing import Dict, List, Union


# Data class for results of the Stale check
@dataclass
class StaleResults:
    code: NagiosOutputCode
    count: int


# Data class for the results of the Timely check
@dataclass
class TimelyResults:
    code: NagiosOutputCode
    critical: int
    warning: int


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

    def check_fresh_arrival(
        self,
        current_time: datetime,
        thresholds: ArrivalThresholds
    ) -> StaleResults:
        '''
        Check the number of stale (older than 1 hour) channels

        Parameters
        ----------
        current_time: datetime
            The time to compare the start timestamps against

        crit_range: str
            The number of stale channels required to return a CRITICAL state

        warn_range: str
            The number of stale channels required to return a WARNING state

        Returns
        -------
        StaleResults: Object containing the resulting NagiosOutputCode and the
        count of stale channels
        '''
        stale_channels = 0
        for channel in self:
            channel_age = current_time - (self[channel]).start_time
            if channel_age.total_seconds() > 3600:
                stale_channels += 1

        if NagiosRange(thresholds.crit_range).in_range(stale_channels):
            state = NagiosOutputCode.critical
        elif NagiosRange(thresholds.warn_range).in_range(stale_channels):
            state = NagiosOutputCode.warning
        else:
            state = NagiosOutputCode.ok

        return StaleResults(
            code=state,
            count=stale_channels
            )

    def check_timely_arrival(
        self,
        thresholds: ArrivalThresholds
    ) -> TimelyResults:
        '''
        Parameters
        ----------
        crit_time: float
            The limit on latency in seconds before a channel is considered for
            the critical threshold

        warn_time: float
            The limit on latency in seconds before a channel is considered for
            the warning threshold

        crit_count: str
            The number of required channels with latency above the crit_time
            threshold for the check to return a critical state

        warn_count: str
            The number of required channels with latency above the warn_time
            threshold for the check to return a warning state

        Returns
        -------
        TimelyResults: Object containing the resulting NagiosOutputCode and
        counts of the critical and warning channels
        '''
        critical = 0
        warning = 0

        # Count the channels in the critical and warning latency thresholds
        for channel in self:
            if NagiosRange(thresholds.crit_time).in_range(
                    self[channel].total_latency()):
                critical += 1
            if NagiosRange(thresholds.warn_time).in_range(
                    self[channel].total_latency()):
                warning += 1

        # Decide on the state
        if NagiosRange(thresholds.crit_count).in_range(critical):
            state = NagiosOutputCode.critical
        elif NagiosRange(thresholds.warn_count).in_range(warning):
            state = NagiosOutputCode.warning
        else:
            state = NagiosOutputCode.ok

        return TimelyResults(
            code=state,
            critical=critical,
            warning=warning)

    def sort_list(self) -> List[ArrivalStat]:
        '''
        Returns a sorted list of ArrivalStatistics, sorted by lowest latency
        first
        '''
        stat_list = list(self.values())
        stat_list.sort(key=lambda x: x.total_latency(), reverse=True)
        return stat_list
