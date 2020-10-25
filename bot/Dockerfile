FROM python:3.8-slim-buster

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache -r requirements.txt 

COPY *.py ./

ENV BotToken="1061976169:AAFUJ1rnKXmhbMN5POAPk1DxdY0MPQZlwuk"
#ENV BotToken="1258153191:AAGosyTwZfoGuBPpZ7RV6jSdwPvRyVtvyTI"  # DEBUG
ENV ADMIN_IDs="196846654,463145322"

ENTRYPOINT ["python", "main.py"]
