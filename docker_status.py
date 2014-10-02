from flask import Flask
from multiprocessing import Process, Value
from time import sleep

import datetime
import os
import re
import urllib2
import sys

OK_STATUSES = [ 200, 301, 302 ]
HTTP_TIMEOUT = os.environ.get('HTTP_TIMEOUT', 30)
TEST_INTERVAL = os.environ.get('TEST_INTERVAL', 30)
DEBUG = os.environ.get('DEBUG', False) == "true"
LISTEN_HOST = os.environ.get('LISTEN_HOST', '0.0.0.0')
LISTEN_PORT = os.environ.get('LISTEN_PORT', '80')

app = Flask(__name__)

checks = {}

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
    while True:
        try:
            result = urllib2.urlopen("http://%s/" % host, timeout=HTTP_TIMEOUT)
            status.value = result.getcode()
        except (urllib2.URLError) as e:
            status.value = getattr(e, 'code', -1)
        except:
            status.value = -1

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
