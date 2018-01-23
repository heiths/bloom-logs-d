import schedule
import time
import requests

from bf.helpers import import_access_raw_to_mongo


def create_bloom():
    """
    Process unprocessed logs once per hour
    :return: True when the filters for each logs file is created
    """

    requests.get("http://127.0.0.1/process")


def update_access_raw():
    """ Updates access_raw mongodb collection """

    import_access_raw_to_mongo()


schedule.every().hour.do(create_bloom)
schedule.every().hour.do(update_access_raw)

while True:
    schedule.run_pending()
    time.sleep(1)
