from flask import Flask
from multiprocessing import Process, Value
from time import sleep

import datetime
import os
import re
import urllib2
import sys
import traceback

OK_STATUSES = [ 200, 301, 302 ]
HTTP_TIMEOUT = os.environ.get('HTTP_TIMEOUT', 30)
TEST_INTERVAL = os.environ.get('TEST_INTERVAL', 30)
DEBUG = os.environ.get('DEBUG', False) == "true"
LISTEN_HOST = os.environ.get('LISTEN_HOST', '0.0.0.0')
LISTEN_PORT = os.environ.get('LISTEN_PORT', '80')

app = Flask(__name__)

checks = {}

class NoRedirectHTTPErrorProcessor(urllib2.HTTPErrorProcessor):
    def http_response(self, request, response):
        return response

    https_response = http_response

url_opener = urllib2.build_opener(NoRedirectHTTPErrorProcessor)

@app.route("/")
def status():
    if len([ host for (host, check) in checks.items()
             if check[0].value not in OK_STATUSES ]) == 0:
        status = 200
        message = "OK"
    else:
        status = 500
        message = "Fail"

    return message, status

def checker(host, status):
    get_path = os.environ.get("%s_GET_PATH" % host, "/")

    while True:
        try:
            result = url_opener.open("http://%s%s" % (host, get_path),
                                     timeout=HTTP_TIMEOUT)
            status.value = result.getcode()
        except Exception as e:
            status.value = getattr(e, 'code', -1)
            traceback.print_exc()

        print datetime.datetime.now(), host, status.value
        sys.stdout.flush()
        sleep(TEST_INTERVAL)

if __name__ == "__main__":
    hosts = [ var.split('_')[0] for var in os.environ
              if re.match('[A-Z0-9]+_PORT_80_TCP$', var) ]

    for host in hosts:
        status = Value('i', -1)
        process = Process(target=checker, args=(host, status))
        process.start()
        checks[host] = (status, process)

    app.run(host=LISTEN_HOST, port=LISTEN_PORT, debug=DEBUG)
