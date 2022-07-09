import pathlib
from pysniffwave.nagios.arrival_metrics import LatestArrivalWorker
from pysniffwave.sniffwave.parser import Channel, parse
from typing import List
import pytest


@pytest.fixture(scope='session')
def worker():
    arrival_worker = LatestArrivalWorker(
        filepath='tests/data/latest_arrival.csv',
        changes=2
    )
    channels: List[Channel] = []
    with open('tests/sniffwave_output.txt') as sniff_file:
        for line in sniff_file.readlines():
            channel = parse(line)
            if isinstance(channel, Channel):
                channels.append(channel)

    arrival_worker.add_latest_timestamp(channels)
    return arrival_worker


# @pytest.mark.usefixtures('test_open_arrival_file')
def test_LatestArrivalWorker(worker: LatestArrivalWorker):
    # Parse the test data

    assert isinstance(worker.path, pathlib.Path)

    assert 'FR.SMPL.00.BHZ' in worker

    assert worker.currentchange == 1

    test_sniff_string = ('  MGR.HHZ.IV.-- (0x32 0x30) 0 s4 484 100.0 ' +
                         '2010/06/22 20:10:38.29 (1277237438.2900) 2010/06/' +
                         '22 14:10:41.12 (1277215841.1200) 0x00 0x00 i73 m52' +
                         ' t19 len2000 [D:322.9s F:20.9s]')

    newchannel = parse(test_sniff_string)

    print(newchannel)

    if isinstance(newchannel, Channel):
        worker.add_latest_timestamp(newchannel)

    assert worker.currentchange == 0

    with open(worker.path, mode='r') as f:
        lines = f.readlines()
        assert 'IV.MGR..HHZ,2010-06-22 14:10:36.290000,322.9,20.9\n' not in \
            lines
        assert 'IV.MGR..HHZ,2010-06-22 20:10:38.290000,322.9,20.9\n' in lines


def test_total_latency(worker: LatestArrivalWorker):
    assert worker['MN.TIP..HHZ'].total_latency() == 6.4


def test_gtlt(worker: LatestArrivalWorker):
    assert worker['MN.VTS..BHZ'] > worker['CH.PLONS..HHE']
    assert worker['IV.CRAC..EHN'] < worker['IV.CIGN..HHN']


def test_str(worker: LatestArrivalWorker):
    test_string = str(worker['CH.MUGIO..HHN'])
    assert test_string == 'CH.MUGIO..HHN, 2010-06-22T14:15:40.358300, 3.0s'


def test_new_worker():
    newpath = pathlib.Path('tests/data/newfile.csv')
    assert not newpath.exists()
    LatestArrivalWorker(newpath, 0)
    assert newpath.exists()
    newpath.unlink()


def test_sorted_list(worker: LatestArrivalWorker):
    sorted_list = worker.sort_list()
    assert sorted_list[0].channel == 'IV.MGR..HHN'
