#!/usr/bin/env python
import argparse
import json
import time
from pprint import pprint as pp

import requests

from bf.settings import PROCESS_URL, UPDATE_DB_URL, SEARCH_URL, TASKS_URL


class Triage:
    def __init__(self):
        self.ap = argparse.ArgumentParser(prog='triage.py',
                                          usage='%(prog)s /acct/container/object \n'
                                                '       %(prog)s --update-db full/partial \n'
                                                '       %(prog)s --process-logs')

        self.ap.add_argument('object', nargs='?', help='A single swift object formatted as: account/container/object')
        self.ap.add_argument('--process-logs', '-p', nargs='?', help='Process logs from access_raw', const='logs')
        self.ap.add_argument('--update-db', '-u', nargs="?", help='Update the access_raw log full/partial')

        self.namespace = self.ap.parse_args()

    def bulk_processing_logs(self):
        resp = requests.get(PROCESS_URL)
        print(resp.json())
        exit()

    def update_logs_db(self):
        payload = {'is_full': False}
        if self.namespace.update_db == 'full':
            payload['is_full'] = True

        resp = requests.post(UPDATE_DB_URL, data=json.dumps(payload),
                             headers={'content-type': 'application/json'})
        print(resp.json()['message'])

    def search_swift_object(self):
        payload = {'object': self.namespace.object}

        return requests.post(SEARCH_URL, data=json.dumps(payload),
                             headers={'content-type': 'application/json'})

    def print_response(self, resp):
        print(" ========== RESULTS =========== ")
        state = resp.json()['state']
        if state == "INVALID":
            print(resp.json()['error'])  # INVALID
            exit()

        task_id = resp.json()['task_id']
        start_time = time.time()

        while state == "PENDING":
            r = requests.get("{}/{}".format(TASKS_URL, task_id))
            state = r.json()['state']
            print("state {}".format(state))
            if state == "SUCCESS":
                pp(r.json()['result'])
            time.sleep(2)

        end_time = time.time()
        print("total_time  -- {}".format(end_time - start_time))


if __name__ == "__main__":
    triage = Triage()

    if triage.namespace.process_logs:
        triage.bulk_processing_logs()

    elif triage.namespace.object:
        triage.print_response(triage.search_swift_object())

    elif triage.namespace.update_db:
        triage.update_logs_db()
    else:
        print("Application called incorrectly, Check the help")

