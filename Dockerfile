FROM python:3.10-bullseye

RUN mkdir -p /home/app/bookmark

ENV APP_DIR = '/home/app/bookmark'

# RUN apt-get update -y && apt-get install telnet build-essential python3-dev -y

WORKDIR ${APP_DIR}

ENV PYTHONPATH='/home/app/bookmark'

COPY requirements.txt /home/app/bookmark
RUN pip install -r /home/app/bookmark/requirements.txt

COPY . /home/app/bookmark

CMD ["python", "/home/app/bookmark/app.py"]
