import datetime
import logging
from dateutil.parser import parse
from pathlib import Path

import pymongo
from swiftly.client import StandardClient
from hashlib import md5

from pymongo import MongoClient, UpdateOne

from bf import settings

logging.basicConfig(format='%(asctime)-15s %(message)s')
logger = logging.getLogger(__name__)

app_path = Path(__file__).parent


def get_access_raw(marker=None, end=None, limit=10000, chunk_output=False):
    """
    This iterates over all logs in a container

    Useful when there are greater than 10,000 logs in a container, as most
    swift servers are configured to limit each request to that number.

    """
    c = StandardClient(**settings.swiftly_config)

    processing = True
    while processing:
        result = c.get_container(settings.LOG_CONTAINER,
                                 marker=marker,
                                 end_marker=end,
                                 limit=limit)[-1]

        if result:
            marker = result[-1]['name']
            if chunk_output:
                yield result
            else:
                for obj in result:
                    yield obj
        else:
            processing = False


def get_size_over_time():
    """
    Utility that returns a log date and size for each log in a container
    :return: timestamp, log size (in bytes)
    ":rtype: tuple
    """
    db = MongoClient(settings.MONGO_HOST, settings.MONGO_PORT).slogs

    for logs in get_access_raw(chunk_output=True):
        db.size_usage.insert_many([
            {"d": parse(x['last_modified']),
             "s": x['bytes']} for x in logs])
        print("Inserted {} new documents".format(len(logs)))
    print("Finished importing to mongodb")


def get_newest_log_in_db():
    """
    Useful to use as a marker when getting new logs from the swift container.
    :return: The name of the most recent log known to mongodb
    """
    db = MongoClient(settings.MONGO_HOST, settings.MONGO_PORT).slogs
    c = db.get_collection('access_raw').find({}).sort(
        [("name", pymongo.DESCENDING)]
    ).limit(1)

    if c.count() > 0:
        return c.next()["name"]


def get_today_as_string():
    return datetime.datetime.utcnow().strftime("%Y/%m/%d/%H")


def import_access_raw_to_mongo():
    db = MongoClient(settings.MONGO_HOST, settings.MONGO_PORT).slogs

    logs = [log['name'] for log in get_access_raw(marker=get_newest_log_in_db())]
    if logs:
        db.access_raw.insert_many([
            {"name": x,
             "is_processed": False} for x in logs])
        logger.info('Import complete')
    else:
        logger.info('No new logs to import')


def get_unprocessed_logs():
    db = MongoClient(settings.MONGO_HOST, settings.MONGO_PORT).slogs

    matches = db.access_raw.find({"is_processed": False})
    return list(matches)


def is_processed(log_name: str):
    """ A filter to check if a log has already been processed."""
    db = MongoClient(settings.MONGO_HOST, settings.MONGO_PORT).slogs

    match = db.access_raw.find_one({"name": log_name})
    if not match:
        return False
    return match['is_processed']


def get_start_end_times(hours=24):
    """
    Helper to get string formatted times for the last 4 hours
    :return: tuple containing start, end dates
    :rtype: tuple
    """
    _end = datetime.datetime.now()
    hours = datetime.timedelta(hours=hours)
    _start = _end - hours
    end = _end.strftime("%Y/%m/%d/%H")
    start = _start.strftime("%Y/%m/%d/%H")

    return start, end


def get_logs_by_date_range(start="2014/01/01/00", end="2017/08/20/05"):
    """ Gets a list of objects from a swift container between two dates

    :param start: A date string formatted like:  "YYYY/MM/DD/HH"
    :param end: Same as start
    :return: list of dictionaries representing swift objects
    """
    db = MongoClient(settings.MONGO_HOST, settings.MONGO_PORT).slogs

    matches = db.access_raw.find({"$and": [
        {"name": {"$lte": end}},
        {"name": {"$gte": start}},
    ]})
    return list(matches)


def line_is_valid(line):
    """
    Filter and validate log lines
    :param line: A single log line
    :rtype: bool
    """
    try:
        verb, obj, _, status = line.split()[8:12]
    except ValueError:
        return False
    return verb in ("DELETE", "PUT") and status.startswith('2')


def obj_name_is_valid(obj):
    """
    Validation are done checking "/account/container/object"
    :param obj:
    :rtype: bool
    """
    return len([item for item in obj.split('/') if len(item) > 0]) >= 3


def search_db_by_name(object_name):
    """
    Given an object name, return the object hash and search results
    :param object_name:
    :return: hash, search_results (dict)
    :rtype: tuple
    """
    db = MongoClient(settings.MONGO_HOST, settings.MONGO_PORT).slogs

    if object_name.startswith("/v1/"):
        object_name = object_name[4:]

    hash_obj = md5(bytes(object_name, encoding="UTF-8")).hexdigest()
    return hash_obj, db.slogs.find_one({"_id": hash_obj})


def create_or_update_db(log_name, object_hash_list):
    """ Create or update mongodb data

    Associates a hash with a log_name for a given list of hashes.
    Only a newer log_file names with overwrite the old value.
    (This works because of the date prefix on the log names)

    :param log_name: Name of log (Like those from access_raw)
    :param object_hash_list: A list of object md5 hashes
    """
    db = MongoClient(settings.MONGO_HOST, settings.MONGO_PORT).slogs
    access_raw = db.get_collection('access_raw')

    # Make a list of updates to batch write.
    update = [UpdateOne({"_id": obj},
                        {"$max": {  # Only update if log_name is newer than existing
                            "recent_log": log_name
                        }},
                        upsert=True) for obj in object_hash_list]
    db.slogs.bulk_write(update)

    # Mark this log as processed
    access_raw.update_one({"name": log_name}, {"$set": {'is_processed': True}})
