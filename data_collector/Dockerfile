FROM python:3.8-slim-buster

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache -r requirements.txt

ENV MeteostationIP="192.168.0.175"
#ENV DEBUG=''

COPY *.py ./

ENTRYPOINT ["python", "main.py"]
