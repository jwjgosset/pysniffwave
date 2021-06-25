import pysniffwave.sniffwave.client as sniffwave
from pysniffwave.workers.print import PrintWorker
from pysniffwave.workers.sql import SQLWorker
from pysniffwave.workers.hdf5 import HDF5Worker


def test_worker_print():
    '''
    Test the print worker
    '''
    # start the worker thread
    myworker = PrintWorker(timeout=5)
    sniffwave.start(myworker, max_lines=10, max_fails=10)


def test_worker_sqlite():
    '''
    Test the sql worker
    '''
    # start the worker thread
    myworker = SQLWorker(timeout=5)
    sniffwave.start(myworker, max_lines=10, max_fails=10)


def test_worker_hdf5():
    '''
    Test the hdf5 worker
    '''
    # start the worker thread
    myworker = HDF5Worker(timeout=5)
    sniffwave.start(myworker, max_lines=10, max_fails=10)
