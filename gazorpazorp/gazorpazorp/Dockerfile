FROM python:3.10-slim

WORKDIR /usr/src/app

COPY common/common /usr/src/app/common

COPY common/requirements.txt /usr/temp/

RUN pip install --no-cache-dir -r /usr/temp/requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/usr/src/app"

COPY gazorpazorp/app /usr/src/app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000"]