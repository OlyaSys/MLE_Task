FROM python:3.12

WORKDIR /stock_predictor

COPY stock_predictor/requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY stock_predictor/stock_predictor.py service.py
COPY rabbit ./rabbit
COPY utils ./utils

CMD ["python", "service.py"]
