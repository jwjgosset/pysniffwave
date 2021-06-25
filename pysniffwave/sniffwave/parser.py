'''
..  codeauthor:: Charles Blais <charles.blais@canada.ca>
'''
import logging
import re
import datetime

from typing import Optional, Union


class Channel(dict):
    '''Standard stat response'''


class ChannelError(dict):
    '''Special condition response'''


def parse(line: str) -> Optional[Union[Channel, ChannelError]]:
    '''
    Parse the line response of the sniffwave message.

    1. standard line with latecny
    2. error: gap, overlap, out-of-order

    For an example of each, see the content of the sniffwave_output.txt in the
    test folder.

    We cheat the process by simply grabbing all numeric values from the
    content.  We do this since sniffwave output aren't constant table
    like patterns are constant white space delimited (not a fan of the format).
    '''
    logging.info(f'Parsing line: {line}')
    # standard line with latency check (most common)
    if len(line) < 125:
        logging.warning('sniffwave line does not contain the \
minimum amount of 125 characters')
        return None

    # line must start with SCNL pattern
    if not re.match(r'^[A-Z0-9]+\.[A-Z0-9]+\.[A-Z0-9]+', line.lstrip()):
        logging.warning('Line does not contain SCNL pattern')
        return None
    scnl = line[0:16].strip().split('.')
    scnl_dict = {
        'station': scnl[0],
        'channel': scnl[1],
        'network': scnl[2],
        'location': '' if scnl[3] == '--' else scnl[3],
    }

    # get all numeric values from the line - SCNL pattern we don't care
    numbers = re.findall(r"\d+\.\d+|\d+", line[33:])
    if len(numbers) < 15:
        logging.warning('Line does not contain the minimum amount of numbers')
        return None

    # these are special condition flags
    if len(line) < 170:
        return ChannelError(
            **scnl_dict,
            error=line[16:].lstrip().split(' ')[0],
            start_time=datetime.datetime.fromtimestamp(float(numbers[7])),
            end_time=datetime.datetime.fromtimestamp(float(numbers[-1])),
            recorded_at=datetime.datetime.now(),
        )

    return Channel(
        **scnl_dict,
        n_samples=int(numbers[0]),
        sample_rate=float(numbers[1]),
        start_time=datetime.datetime.fromtimestamp(float(numbers[8])),
        n_bytes=int(numbers[-3]),
        data_latency=float(numbers[-2]),
        feeding_latency=float(numbers[-1]),
        recorded_at=datetime.datetime.now(),
    )
