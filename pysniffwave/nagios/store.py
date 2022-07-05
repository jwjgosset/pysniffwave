import pathlib
from pysniffwave.sniffwave.parser import Channel
import logging
from typing import Dict, List, Union


class LatestArrivalWorker():
    def __init__(
        self,
        filepath: Union[str, pathlib.Path],
        changes: int
    ):
        # Convert a str path to a pathlib Path
        if isinstance(filepath, str):
            filepath = pathlib.Path(filepath)

        self.path = filepath

        self.channels: Dict[str, str] = {}

        # Open the file to initialize the dictionary
        if filepath.exists():

            with open(filepath, mode='r') as f:
                lines = f.readlines()

                for line in lines:
                    if line != '\n':
                        channel, timestamp = line.split(',')
                        self.channels[channel] = timestamp
        else:
            filepath.touch(mode=0o644)
            logging.warning(f"File {str(filepath)} did not exist, created")

        self.changes = changes
        self.currentchange = 0

    def add_latest_timestamp(
        self,
        channel_stats: Union[List[Channel], Channel]
    ):
        # Assemble data in string format

        # Ensure that channel_stats is iterable
        if isinstance(channel_stats, Channel):
            channel_stats = [channel_stats]

        for channel in channel_stats:
            # Convert scnl to string
            scnl = (f"{channel['network']}.{channel['station']}." +
                    f"{channel['location']}.{channel['channel']}")
            # Add timestamp to string
            self.channels[scnl] = channel['start_time']

        self.currentchange += 1

        if self.currentchange >= self.changes:
            self.currentchange = 0
            self.write_to_file()
            # Write to file

    def write_to_file(self):

        lines: str = ''

        for channel in self.channels:
            lines += f"{channel},{self.channels[channel]}\n"

        with open(str(self.path), mode='w') as f:
            f.write(lines)
