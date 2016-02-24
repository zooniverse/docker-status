FROM python:2.7-alpine

COPY requirements.txt /requirements.txt

RUN pip install -r /requirements.txt

ADD docker_status.py /

CMD [ "python", "/docker_status.py" ]

EXPOSE 80
