from flask import Flask
from multiprocessing import Process, Value
from time import sleep

import datetime
import graypy
import logging
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
DELAY_START = os.environ.get('DELAY_START', False) == "true"
GRAYLOG_HOST = os.environ.get('GRAYLOG_HOST', None)
GRAYLOG_PORT = int(os.environ.get('GRAYLOG_PORT', 12201))
GRAYLOG_LOCALNAME = os.environ.get('GRAYLOG_LOCALNAME', 'docker-status')

app = Flask(__name__)

checks = {}

class NoRedirectHTTPErrorProcessor(urllib2.HTTPErrorProcessor):
    def http_response(self, request, response):
        return response

    https_response = http_response

url_opener = urllib2.build_opener(NoRedirectHTTPErrorProcessor)

if GRAYLOG_HOST is not None:
    logger = logging.getLogger('status_logger')
    if DEBUG:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    graylog_handler = graypy.GELFHandler(
        GRAYLOG_HOST,
        GRAYLOG_PORT,
        localname=GRAYLOG_LOCALNAME
    )
    logger.addHandler(graylog_handler)

@app.route("/")
def status():
    for (host, (status, timestamp, process)) in checks.items():
        if (status.value not in OK_STATUSES or
            timestamp.value < int(
                (datetime.datetime.now() - datetime.timedelta(
                    seconds=TEST_INTERVAL*2
                )).strftime("%s")
            )
           ):
            return "Fail", 500

    return "OK", 200

def checker(host, status, timestamp):
    get_path = os.environ.get("%s_GET_PATH" % host, "/")
    use_host_ip = os.environ.get("%s_CONNECT_IP" % host, False) == 'true'

    if use_host_ip:
        check_host = os.environ.get("%s_PORT_80_TCP_ADDR" % host)
    else:
        check_host = host.lower()

    log_adapter = logging.LoggerAdapter(
        logging.getLogger('status_logger'),
        {
            'status_host': host,
            'status_check_host': check_host
        }
    )

    while True:
        try:
            result = url_opener.open("http://%s%s" % (check_host, get_path),
                                     timeout=HTTP_TIMEOUT)
            status.value = result.getcode()
        except Exception as e:
            status.value = getattr(e, 'code', -1)
            log_str = "Failed check. Host: %s, path: %s" % (
                check_host,
                get_path
            )
            log_adapter.error(log_str, exc_info=1)
            print log_str
            traceback.print_exc()

        timestamp.value = int(datetime.datetime.now().strftime('%s'))
        log_str = "%s %s %s" % (datetime.datetime.now(), host, status.value)
        if status.value in OK_STATUSES:
            log_adapter.info(log_str)
        else:
            log_adapter.error(log_str)
        print(log_str)
        sys.stdout.flush()
        sleep(TEST_INTERVAL)

if __name__ == "__main__":
    hosts = [ var.split('_PORT_80_TCP')[0] for var in os.environ
              if re.match('[A-Z0-9_]+_PORT_80_TCP$', var) ]

    # De-dupe hosts. We take the one with the shortest name for each IP address
    host_ips = {}
    for host in hosts:
        host_ips.setdefault(os.environ.get("%s_PORT_80_TCP_ADDR" % host),
                            []).append(host)
    hosts = []
    for ip, ip_hosts in host_ips.items():
        hosts.append(sorted(ip_hosts, key=len)[0])

    for host in hosts:
        status = Value('i', -1)
        timestamp = Value('i', -1)
        process = Process(target=checker, args=(host, status, timestamp))
        process.start()
        checks[host] = (status, timestamp, process)

        if DELAY_START:
            sleep(TEST_INTERVAL)

    app.run(host=LISTEN_HOST, port=LISTEN_PORT, debug=DEBUG)
