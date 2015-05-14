from ubuntu:14.04

ADD requirements.txt /

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get -y upgrade && \
    apt-get install -y python python-dev python-setuptools python-pip && \
    pip install -r requirements.txt

ADD docker_status.py /

ENTRYPOINT [ "python", "/docker_status.py" ]

EXPOSE 80
