FROM python:3.10

WORKDIR /usr/src/app

COPY common/common /usr/src/app/common

COPY common/requirements.txt /usr/temp/

RUN pip install --no-cache-dir -r /usr/temp/requirements.txt

COPY tools/gradio_app1 /usr/src/app

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/usr/src/app"

EXPOSE 7860


CMD ["python", "./app.py"]
