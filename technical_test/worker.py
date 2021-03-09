#!/usr/bin/env python
import os
import sys

import pika
import time

from technical_test import helpers, tasks

LOG = helpers.get_logger(__name__)


def main():
    db_client = helpers.get_db_client()

    time_sleep = 5
    while True:
        try:
            rabbit_client = helpers.get_queue_client(db_client)
            break
        except pika.exceptions.AMQPConnectionError:
            LOG.info(f'try reconnection in {time_sleep}s')
            time.sleep(time_sleep)
            time_sleep = time_sleep * 2
            continue

    rabbit_client.register_task(tasks.SendValidationCodeEmailTask)
    LOG.info('worker listening')
    rabbit_client.listen()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
