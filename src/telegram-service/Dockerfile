FROM python:3.8-slim-buster

WORKDIR /code
# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# setting timezone
ENV TZ Europe/Moscow

COPY ./code /code

ENTRYPOINT ["python", "main.py"]
