FROM python:3.8-slim-buster

WORKDIR /code

COPY requirements.txt .
RUN pip install -q --no-cache-dir -r requirements.txt && rm requirements.txt

ENV MeteostationIP="192.168.0.175"
#ENV DEBUG=''

# setting timezone
ENV TZ Europe/Moscow

COPY *.py ./

ENTRYPOINT ["python", "main.py"]
