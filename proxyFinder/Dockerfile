FROM python:3.8 as base

WORKDIR /build/

# create new venv
RUN python -m venv /build/
ENV PATH=/build/bin:$PATH

# install python requirements in venv
COPY requirements.txt .
RUN pip install -q --no-cache-dir -r requirements.txt


##### START NEW IMAGE: PRODUCTION #####
FROM python:3.8-slim as prod

# set the timezone
ENV TZ Europe/Moscow

# copy libs
COPY --from=base /build /requirements/
ENV PATH=/requirements/bin/:$PATH

# copy code
WORKDIR /code/
COPY ./src/ /code/

ENTRYPOINT ["python", "main.py"]