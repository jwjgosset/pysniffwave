import datetime

from pysniffwave.sql.client import Client


def test_client_find():
    '''
    Test the print worker
    '''
    client = Client()

    now = datetime.datetime.now()
    # start the worker thread
    print(client.find(
        now - datetime.timedelta(days=10),
        now,
    ))
