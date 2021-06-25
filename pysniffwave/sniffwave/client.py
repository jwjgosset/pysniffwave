'''
..  codeauthor:: Charles Blais <charles.blais@canada.ca>
'''
import logging
import queue
import subprocess
import time

from typing import Union, List

from pysniffwave.thread import StoppableThread
from pysniffwave.workers.worker import Worker
from .parser import parse


class Sniffwave(StoppableThread):
    '''
    Sniffwave handler
    '''
    def __init__(
        self,
        queues: Union[queue.Queue, List[queue.Queue]],
        cmd_args: Union[str, List[str]] = 'WAVE_RING',
        max_lines: int = -1,
        max_fails: int = -1,
        *args, **kwargs
    ):
        '''
        :type queue: :class:`queue.Queue` or [:class:`queue.Queue`, ...]
        :param queue: queues

        :type cmd_args: str or [str,...]
        :param str cmd_args: wave identifier

        :param int max_lines: maximum amount of lines to decode
        :param int max_tries: maximum amount of failed attempts
        '''
        super().__init__(*args, **kwargs)
        self.cmd_args = ' '.join(cmd_args) \
            if isinstance(cmd_args, list) else cmd_args
        self.queues = [queues] if not isinstance(queues, list) else queues
        self.max_lines = max_lines
        self.max_fails = max_fails

    def run(self):
        '''
        Execute sniffwave program and listen for packets
        stop if told to stop
        '''
        current_fails = self.max_fails

        try:
            logging.info(f'Executing: sniffwave {self.cmd_args}')
            proc = subprocess.Popen(
                f'sniffwave {self.cmd_args}',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except FileNotFoundError:
            logging.error('The sniffwave program could not be found, make sure \
it exists in the system PATH')
            return

        while not self.is_stopped \
                and self.max_lines != 0 \
                and current_fails != 0:
            # we first check if there is a return code (it stopped?)
            if proc.returncode is not None:
                logging.error(f'sniffwave has a rcode {proc.returncode}')
                logging.error(proc.stderr.read())
                break

            logging.debug(f'Waiting for sniffwave (count: {self.max_lines}, \
fail decount: {current_fails})')
            line = proc.stdout.readline()

            # do nothing if the line is empty
            if not line:
                if current_fails > 0:
                    logging.debug(f'Reducing max fail count: {current_fails}')
                    current_fails -= 1
                continue

            # parse the content of the line
            stat = parse(line.decode('utf-8'))

            if stat is None:
                if current_fails > 0:
                    logging.debug(f'Reducing max fail count: {current_fails}')
                    current_fails -= 1
                continue

            # reset fail count
            current_fails = self.max_fails
            # add message to all queues
            for q in self.queues:
                q.put(stat)

            # maximum of lines to read
            if self.max_lines > 0:
                logging.debug(f'Reducing max line count: {self.max_lines}')
                self.max_lines -= 1

        # terminate the process
        logging.info('Stopping sniffwave gracefully')
        proc.terminate()
        return proc.wait(timeout=1.0)


def start(
    myworkers: Union[Worker, List[Worker]],
    cmd_args: str = 'WAVE_RING',
    healthcheck: int = 1,
    max_lines: int = -1,
    max_fails: int = -1,
):
    '''
    Start reading content of the sniffwave and send to the worker

    :type myworkers: :class:`Worker` or [:class:`Worker`, ...]
    :param myworkers: worker(s) to pass decoded sniffwave information via queue

    :type cmd_args: str or [str,...]
    :param str cmd_args: wave identifier

    :param int healthcheck: interval time in seconds to check if all
        threads are running
    :param int max_lines: maximum amount of lines to decode
    :param int max_tries: maximum amount of failed attempts
    '''
    if not isinstance(myworkers, list):
        myworkers = [myworkers]

    # create queues for each worker
    myqueues: List[queue.Queue[dict]] = []
    for myworker in myworkers:
        myqueue: queue.Queue[dict] = queue.Queue()
        myqueues.append(myqueue)
        # set the queue and start my worker thread
        myworker.set_queue(myqueue)
        myworker.start()

    # start the listening process
    mysniff = Sniffwave(
        myqueues,
        cmd_args=cmd_args,
        max_lines=max_lines,
        max_fails=max_fails)
    mysniff.start()

    # infinite check if thread is still running
    while True:
        logging.info('Health check: sniffwave')
        if not mysniff.is_alive():
            logging.info('Sniffwave stopped...')
            break
        for myworker in myworkers:
            logging.info('Health check: worker')
            if not myworker.is_alive():
                logging.info('Worker stopped...')
                break
        time.sleep(healthcheck)

    # indicate both thread to stop
    mysniff.stop()
    for myworker in myworkers:
        myworker.stop()
    mysniff.join()
    for myworker in myworkers:
        myworker.join()
