import pathlib
from pysniffwave.nagios.store import LatestArrivalWorker
from pysniffwave.sniffwave.parser import Channel, parse
from typing import List


# @pytest.mark.usefixtures('test_open_arrival_file')
def test_LatestArrivalWorker():
    channels: List[Channel] = []

    # Parse the test data
    with open('tests/sniffwave_output.txt') as sniff_file:
        for line in sniff_file.readlines():
            channel = parse(line)
            if isinstance(channel, Channel):
                channels.append(channel)

    arrival_worker = LatestArrivalWorker(
        filepath='tests/data/latest_arrival.csv',
        changes=2
    )

    assert isinstance(arrival_worker.path, pathlib.Path)

    arrival_worker.add_latest_timestamp(channels)

    assert 'FR.SMPL.00.BHZ' in arrival_worker.channels

    assert arrival_worker.currentchange == 1

    test_sniff_string = ('  MGR.HHZ.IV.-- (0x32 0x30) 0 s4 484 100.0 ' +
                         '2010/06/22 20:10:38.29 (1277237438.2900) 2010/06/' +
                         '22 14:10:41.12 (1277215841.1200) 0x00 0x00 i73 m52' +
                         ' t19 len2000 [D:322.9s F:20.9s]')

    newchannel = parse(test_sniff_string)

    print(newchannel)

    arrival_worker.add_latest_timestamp(newchannel)

    assert arrival_worker.currentchange == 0

    with open(arrival_worker.path, mode='r') as f:
        lines = f.readlines()
        assert 'IV.MGR..HHZ,2010-06-22 14:10:36.290000,322.9,20.9\n' not in \
            lines
        assert 'IV.MGR..HHZ,2010-06-22 20:10:38.290000,322.9,20.9\n' in lines
