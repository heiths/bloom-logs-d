import gzip
import io
import time
from hashlib import md5
from pathlib import Path

from pymongo.errors import BulkWriteError
from swiftly.client import StandardClient

from bf import settings
from bf.helpers import line_is_valid, is_processed, create_or_update_db

app_path = Path(__file__).parent


def get_log_data(name):
    """ Function to get the log lines for processing

    :param name: (string) Name of the log in the access_raw container
    """
    c = StandardClient(**settings.swiftly_config)
    res = c.get_object(settings.LOG_CONTAINER, name, stream=False)

    gz = gzip.GzipFile(mode='rb', fileobj=io.BytesIO(res[-1]))
    with io.TextIOWrapper(io.BufferedReader(gz)) as f:
        for line in f:
            if line_is_valid(line):
                yield line


def process_log(log_name):
    """ The internal interface for processing a single log
    :param log_name: Name of the file name which contains the swift object
    """
    if is_processed(log_name):
        print("log already processed: {}".format(log_name))
        return

    seen = set()
    for line in get_log_data(log_name):
        parts = line.split()
        verb, object_name, _, status = parts[8:12]
        if str(object_name).startswith("/v1/"):
            object_name = object_name[4:]
        _name = bytes(object_name, encoding="UTF-8")
        seen.add(md5(_name).hexdigest())

    if seen:
        try:

            create_or_update_db(log_name, list(seen))
        except BulkWriteError as e:
            print("- " * 20)
            print("{} : {}".format(e.code, e.details))


def search_swift_logs(object_name, log_name):
    """ Search a swift logfile for an object

    :param object_name: The swift object you want to find
    :param log_name: The log file to search
    :return:
    """
    log_data = get_log_data(log_name)
    for line in log_data:
        if object_name in line:
            yield line


def parse_line(line):
    """ Extracts commonly used elements from the log line

    :param line: A full swift proxy log line (string)
    :return: A dict of common line elements
    """
    line = line.split()
    if line[-1] is '0':
        timestamp = float(line[-2])
    else:
        timestamp = float(line[-1])
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(timestamp))
    return {
        "timestamp": timestamp,
        "method": line[8],
        "status": line[11],
        "raw": "".join(line),
        "ip": line[5],
        "obj": line[9],
        "request_path": line[12],
        "transaction_id": line[18]
    }
