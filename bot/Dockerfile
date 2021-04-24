FROM python:3.8 as base

WORKDIR /build/

# create new venv
RUN python -m venv /build/
ENV PATH=/build/bin:$PATH

# install python requirements in a special folder
COPY requirements.txt .
RUN pip install -q --no-cache-dir -r requirements.txt


##### START NEW IMAGE : DEBUGGER #####
FROM python:3.8-slim as debug

# set the timezone
ENV TZ Europe/Moscow

# copy libs
COPY --from=base /build /requirements/
ENV PATH=/requirements/bin/:$PATH

# install debugger
RUN pip install --no-cache-dir ptvsd

# copy code
WORKDIR /code/
COPY ./src/ /code/

# run debugger
CMD ["python", "-m", "ptvsd", "--host 0.0.0.0", "--port 5678", "--wait", "main.py"]


##### START NEW IMAGE: PRODUCTION #####
FROM python:3.8-slim as prod

# set the user
USER 1000

# set the timezone
ENV TZ Europe/Moscow

# copy libs
COPY --from=base /build /requirements/
ENV PATH=/requirements/bin/:$PATH

# copy code
WORKDIR /code/
COPY ./src/ /code/

ENTRYPOINT ["python", "main.py"]