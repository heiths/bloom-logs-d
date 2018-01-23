from pathlib import Path

from celery import Celery
from celery import states
from celery.utils import uuid
from celery.utils.log import get_task_logger
from flask import Flask, request, jsonify, make_response, render_template, send_from_directory

from bf import settings
from bf.helpers import get_unprocessed_logs, obj_name_is_valid, search_db_by_name, import_access_raw_to_mongo
from bf.log_processor import process_log, search_swift_logs, parse_line

logger = get_task_logger(__name__)

app = Flask(__name__)
app.config.update(
    broker_url=settings.CELERY_BROKER_URL,
    result_backend=settings.CELERY_BACKEND
)

celery = Celery(app.name, broker=settings.CELERY_BROKER_URL)
celery.conf.update(app.config)
if settings.TESTING:
    celery.conf['debug'] = True
celery.conf.task_routes = {
    'app.get_match': {'queue': 'search'},
}
app.secret_key = 'JmN~/S@.B*-c-HvUkV^ZmgD;mccW3xG2}`fC3:K:4[mG$m:J@}N{:6;`_a,m?!Gn?zc%9n'

APP_DIR = Path(__file__).parent

task_annotations = {
    'app.process_log': {'rate_limit': settings.PROCESS_LOG_RATE_LIMIT},
    'app.get_match': {'rate_limit': settings.SEARCH_QUEUE_RATE_LIMIT}
}


@app.route('/')
def home():
    return render_template('base.html')


@app.route('/update', methods=['POST'])
def update_db():
    import_access_raw_to_mongo()
    return jsonify({"message": "Update complete"})


@app.route('/process', methods=['GET'])
def process():
    """ Kickoff log processing for any unprocessed logs
    """
    unprocessed_logs = get_unprocessed_logs()
    for obj in unprocessed_logs:
        process_log_task.delay(obj['name'])

    return jsonify({"state": "SUBMITTED", "result": "{} logs will be processed".format(len(unprocessed_logs))})


@celery.task(name='app.process_log')
def process_log_task(log_name):
    """ Task wrapper for processing a single log
    Filter a log file and upsert the result in mongo
    :param log_name: Full name of a log from access_raw
    """
    process_log(log_name)


@app.route('/tasks/<task_id>', methods=['GET'])
def check_task_status(task_id):
    """ Check and return the status of a given task

    :param task_id: The id for a celery async task
    :return: A json response indicating the task state and result if state is not pending
    """
    task = celery.AsyncResult(task_id)

    state = task.state
    response = {'state': state}

    if state == states.SUCCESS:
        response['result'] = task.result
    elif state == states.FAILURE:
        response['error'] = task.info

    app.logger.debug(task)
    return make_response(jsonify(response))


@app.route('/search', methods=['POST'])
def search():
    """ The api endpoint for searching swift logs for PUT and DELETES
    :return: A json response indicating the job is being processed
    """

    if not request.is_json:
        return jsonify(error='expected json')
    try:
        query_obj = request.get_json()['object']
        if isinstance(query_obj, list):
            query_obj = query_obj[0]
    except KeyError:
        return jsonify(state="FAILURE", error="""Expected "object" key. Example:  {"object": "some/test/obj.jpg"}""")

    app.logger.debug(query_obj)

    if not obj_name_is_valid(query_obj):
        app.logger.debug("Invalid object {}".format(query_obj))
        return jsonify(state="INVALID", error='Invalid Object. Expected format: "account/container/object_name')

    hash_obj, result = search_db_by_name(query_obj)

    if not result:
        return jsonify({"state": "MISSING", "result": "No object found", "task_id": None})

    task = get_match.apply_async(
        args=[query_obj, result['recent_log']],
        queue='search',
        routing_key='app.get_match',
        task_id='search-id-{}'.format(uuid())
    )

    return jsonify(
        {
            "state": "PENDING",
            "task_id": task.task_id,
            "result": {
                "object_hash": hash_obj,
                "recent_log": result['recent_log']
            },

        })


@celery.task(name='app.get_match')
def get_match(obj, log):
    """ Get full log line for an object/log file
    """
    return {"result": [parse_line(i) for i in search_swift_logs(obj, log)]}


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'invalid url'}), 404)


@app.route('/static/<path:filename>')
def send_static(filename):
    """ Quick and easy way to serve static files.
    """
    return send_from_directory('bf/static', filename)


if __name__ == '__main__':
    app.run()
