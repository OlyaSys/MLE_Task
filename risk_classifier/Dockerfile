FROM python:3.12

WORKDIR /risk_classifier

COPY risk_classifier/requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY risk_classifier/risk_classifier.py service.py
COPY rabbit ./rabbit
COPY utils ./utils

CMD ["python", "service.py"]
