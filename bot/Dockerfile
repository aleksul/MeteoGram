FROM python:3.8-slim-buster

WORKDIR /code

RUN apt-get update && apt install -y gcc g++ make
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt
RUN apt -qq purge -y gcc g++ make && apt -qq clean -y && apt -qq autoremove -y

ENV BotToken="1061976169:AAFUJ1rnKXmhbMN5POAPk1DxdY0MPQZlwuk"
#ENV BotToken="1258153191:AAGosyTwZfoGuBPpZ7RV6jSdwPvRyVtvyTI"  # DEBUG
ENV ADMIN_IDs="196846654,463145322"

# setting timezone
ENV TZ Europe/Moscow

COPY *.py ./

ENTRYPOINT ["python", "main.py"]
