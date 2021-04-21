FROM python:3.8-slim-buster as base

WORKDIR /build/

# install python requirements in a special folder
COPY ./requirements.txt /build/requirements.txt
RUN pip install -q --target /build/ --no-cache-dir -r requirements.txt

##### START NEW IMAGE : DEBUGGER #####
FROM base as debug

# set the timezone
ENV TZ Europe/Moscow
# select folder with python requirements
ENV PYTHONPATH="/build/"
# set debug
ENV MeteostationIP="DEBUG"

# install debugger
RUN pip install ptvsd

# copy code
WORKDIR /code/
COPY ./src/ /code/

# run debugger
CMD ["python", "-m", "ptvsd", "--host 0.0.0.0", "--port 5679", "--wait", "main.py"]


##### START NEW IMAGE: PRODUCTION #####
FROM python:3.8-alpine as prod

# set the user
USER 1000

# set ip
ENV MeteostationIP="192.168.0.175"

# set the timezone
ENV TZ Europe/Moscow

# copy libs
WORKDIR /requirements/
COPY --from=base /build/ /requirements/
ENV PYTHONPATH="/requirements/"

# copy code
WORKDIR /code/
COPY ./src/ /code/

ENTRYPOINT ["python", "main.py"]
