'''
Sniffwave logger
================

Utility for logging sniffwave information to HDF5 files.
Could be modified for SQL if required...

..  codeauthor:: Charles Blais
'''
import logging
import argparse
from pathlib import Path


import pysniffwave.sniffwave.client as sniffwave
from pysniffwave.workers.hdf5 import HDF5Worker


DEFAULT_DIRECTORY = Path().cwd()
DEFAULT_TIMEOUT = 10


def main():
    '''
    See module description
    '''
    parser = argparse.ArgumentParser(description='Run create origin script')
    parser.add_argument(
        'cmd_args',
        nargs='+',
        help='Command arguments to send to sniffave (ex: "WAVE_RING"). \
See "sniffwave" for more information.')
    parser.add_argument(
        '-v', '--verbose',
        action='count',
        default=0,
        help='Verbosity')
    parser.add_argument(
        '-d', '--directory',
        default=DEFAULT_DIRECTORY,
        help=f'Directory to store HDF5 archive (default: {DEFAULT_DIRECTORY})')
    parser.add_argument(
        '-t', '--timeout',
        default=DEFAULT_TIMEOUT,
        type=int,
        help=f'Timeout condition (default: {DEFAULT_TIMEOUT}s)')
    parser.add_argument(
        '-m', '--max-lines',
        default=-1,
        type=int,
        help='Max amount of line to process (-1 for infinite) (default: -1)')
    parser.add_argument(
        '-M', '--max-fails',
        default=10,
        type=int,
        help='Max amount of allowed sniffwave fails (-1 for infinite) \
(default: 10)')

    args = parser.parse_args()

    # Set logging level
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s %(funcName)s:\
            %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.WARNING - (args.verbose * 10))

    # start the worker thread
    myworker = HDF5Worker(
        directory=args.directory,
        timeout=args.timeout)
    sniffwave.start(
        myworker,
        cmd_args=args.cmd_args,
        max_lines=args.max_lines,
        max_fails=args.max_fails)
