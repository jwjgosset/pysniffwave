import pysniffwave.sniffwave.client as sniffwave


def test_parse():
    '''
    Test parsing the content safely out of a sample file
    '''
    fp = open('tests/sniffwave_output.txt', 'r')
    for line in fp.readlines():
        print(sniffwave.parse(line))
    fp.close()
    assert False
