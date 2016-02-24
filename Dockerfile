FROM ubuntu:14.04

RUN apt-get update && \
    apt-get install -y python python-flask && \
    rm -rf /var/lib/apt/lists/*

ADD docker_status.py /

ENTRYPOINT [ "python", "/docker_status.py" ]

EXPOSE 80
