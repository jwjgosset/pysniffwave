from datetime import datetime
import logging
import pathlib
from typing import List
from dataclasses import dataclass


@dataclass
class ChannelLatency:
    channel: str
    timestamp: datetime
    latency: float


@dataclass
class ChannelLatencies:
    channels: List[ChannelLatency]


def read_timestamp_file(
    file_location: str
) -> List[str]:
    file_path = pathlib.Path(file_location)
    if not file_path.exists():
        logging.error(f'File not found: {file_location}')
        raise FileNotFoundError

    else:
        with open(file_path, mode='r') as f:
            lines = f.readlines()

        return lines


def get_latencies(
    lines: List[str],
    time: datetime
) -> ChannelLatencies:

    channel_latencies = ChannelLatencies([])

    for line in lines:
        channel, timestring = line.split(',')
        timestamp = datetime.strptime(timestring, '%Y-%m-%d %H:%M:%S.%f')
        latency = (time - timestamp).total_seconds()
        channel_stats = ChannelLatency(
            channel=channel,
            timestamp=timestamp,
            latency=latency
        )
        channel_latencies.channels.append(channel_stats)

    return channel_latencies
