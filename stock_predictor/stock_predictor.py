"""
Stock Predictor Service.

Module implements a service that predicts future stock returns using a regression model
based on historical profitability, trading volume and market index.

It uses a `GradientBoostingRegressor` model to perform the prediction.
"""
import os

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from rabbit.consumer import Consumer
from utils.logger import LOGGER


class StockPredictor:

    def __init__(self) -> None:
        """
        Initializes the StockPredictor.
        """
        self._gb_model = GradientBoostingRegressor()
        self._scaler = StandardScaler()
        self._service_name: str = "stock-predictor"

        self._rmq = Consumer(
            os.environ.get("RMQ_SERVICE_QUEUE", f"{self._service_name}.queue"),
            int(os.environ.get("prefetch_count", 1)),
            self.predict_stock_return
        )
        self.train_model()

    def train_model(self):
        """
        Trains the GradientBoostingRegressor model using sample data.
        """
        data = pd.DataFrame({
            'historical_returns': [0.05, 0.04, 0.06, 0.03, 0.07],
            'volume': [100000, 150000, 120000, 130000, 110000],
            'market_index': [3000, 3050, 3020, 3080, 3100],
            'future_return': [0.06, 0.05, 0.07, 0.04, 0.08]
        })

        features = data[['historical_returns', 'volume', 'market_index']]
        labels = data['future_return']

        x_train, _, y_train, _ = train_test_split(features, labels, test_size=0.2, random_state=42)

        x_train_scaled = self._scaler.fit_transform(x_train)
        self._gb_model.fit(x_train_scaled, y_train)

        LOGGER.info("Predict stock model is trained")

    def predict_stock_return(self, data: dict):
        """
        Predicts future stock return based on new input data.

        :param dict data: A dictionary containing stock metrics for classification.
        """
        input_data = pd.DataFrame(
            [[
                np.mean(data['historical_returns']),
                np.mean(data['volume']),
                np.mean(data['market_index'])
            ]],
            columns=['historical_returns', 'volume', 'market_index']
        )
        input_data_scaled = self._scaler.transform(input_data)

        future_return = self._gb_model.predict(input_data_scaled)[0]

        return future_return


def start_service():
    """
    Starts the Stock Predictor service.
    """
    stock_predictor = StockPredictor()

    LOGGER.info("Start Stock Predictor")
    stock_predictor._rmq.start_consuming()


if __name__ == '__main__':
    start_service()
