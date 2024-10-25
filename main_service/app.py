"""
Module implements a Flask API to handle requests for prediction by investor portfolio.
It communicates with services via RabbitMQ using an RPC client.
"""
import os

from flask import Flask, request, abort, jsonify

from rabbit.rpc_client import RpcClient
from utils.logger import LOGGER

app = Flask(__name__)


@app.route('/v1/prediction', methods=['POST'])
def prediction():
    """
    Endpoint to predict stock and classify risk.

    :return: JSON response with stock symbol, risk category and stock prediction.
    :rtype: JSON
    """
    if not request.json:
        abort(400, description="Request must contain JSON data.")


    try:
        stock_symbol = request.get_json().get('stock_symbol')
        if not stock_symbol:
            abort(400, description="The 'stock_symbol' field is required in the request.")

        rpc_client = RpcClient()

        risk_slf_queue = os.environ.get("RMQ_RISK_CLF_QUEUE", "risk_clf.queue")
        stock_pred_queue = os.environ.get("RMQ_STOCK_PRED_QUEUE", "stock_pred.queue")

        LOGGER.info(f"Processing request for {stock_symbol}")

        try:
            risk_res = rpc_client.call_service(risk_slf_queue, request.data)
        except Exception as e:
            logger.error(f"Error calling risk classification service: {e}")
            abort(500, description="Error in the risk classification service.")

        try:
            pred_stock_res = rpc_client.call_service(stock_pred_queue, request.data)
        except Exception as e:
            logger.error(f"Error calling stock prediction service: {e}")
            abort(500, description="Error in the stock prediction service.")

        res = {
            "stock_symbol": request.get_json()['stock_symbol'],
            "risk_category": risk_res.decode('utf-8'),
            "stock_prediction": pred_stock_res.decode('utf-8')
        }

        LOGGER.info(f"Successfully processed request for {stock_symbol}")

        return jsonify(res), 201

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        abort(500, description="Internal server error.")


if __name__ == '__main__':
    """
    Start the Flask server with the given host and port.
    """
    app_host = os.environ.get("APP_HOST", "localhost")
    app_port = os.environ.get("APP_PORT", 8000)

    app.run(host=app_host, port=app_port, debug=True)
