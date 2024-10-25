FROM python:3.12

WORKDIR /main_service

COPY main_service/requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY main_service/app.py .
COPY rabbit ./rabbit
COPY utils ./utils

CMD ["python", "app.py"]
