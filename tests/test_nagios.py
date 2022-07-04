from pysniffwave.nagios.store import get_arrival_file, store_latest_timestamp
from pysniffwave.sniffwave.parser import Channel, parse
from typing import List


# Test if the missing file is successfully created
# @pytest.fixture(scope='session')
def setup_arrival_file():
    directory = './tests/data'
    filename = 'test_latest_arrival'

    test_file = get_arrival_file(
        directory=directory,
        filename=filename)

    yield test_file


# @pytest.mark.usefixtures('test_open_arrival_file')
def test_store_latest_timestamp():
    channels: List[Channel] = []

    # Parse the test data
    with open('tests/sniffwave_output.txt') as sniff_file:
        for line in sniff_file.readlines():
            channel = parse(line)
            if isinstance(channel, Channel):
                channels.append(channel)

    # Open the test output file and make sure it exists
    lat_file = setup_arrival_file()
    # assert pathlib.Path('./tests/data/test_latest_arrival').exists()

    for file in lat_file:
        # Store the parsed data
        store_latest_timestamp(
            file_path=file,
            channel_stats=channels
        )
        with open(file, mode='r') as f:
            assert 'IV.MGR..HHZ,2010-06-22 14:10:36.290000\n' in f.readlines()

    test_sniff_string = ('  MGR.HHZ.IV.-- (0x32 0x30) 0 s4 484 100.0 ' +
                         '2010/06/22 14:10:38.29 (1277215836.2900) 2010/06/' +
                         '22 14:10:41.12 (1277215841.1200) 0x00 0x00 i73 m52' +
                         ' t19 len2000 [D:322.9s F:20.9s]')

    channel = parse(test_sniff_string)

    for file in lat_file:
        store_latest_timestamp(
            file_path=file,
            channel_stats=channel
        )

        with open(file, mode='r') as f:
            lines = f.readlines()
            assert 'IV.MGR..HHZ,2010-06-22 14:10:36.290000\n' not in lines
            assert 'IV.MGR..HHZ,2010-06-22 14:10:38.290000\n' in lines
