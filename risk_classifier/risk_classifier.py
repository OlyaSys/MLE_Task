"""
Risk Classifier Service.

Module implements a service that classifies risk categories (e.g., Low Risk, High Risk)
based on certain financial indicators like volatility, average return and market correlation.

It uses a `RandomForestClassifier` model to perform the classification
"""
import os

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from rabbit.consumer import Consumer
from utils.logger import LOGGER


class RiskClassifier:

    def __init__(self):
        """
        Initializes the RiskClassifier.
        """
        self._rf_model = RandomForestClassifier()
        self._scaler = StandardScaler()
        self._risk_labels = {0: 'Low Risk', 1: 'High Risk'}
        self._service_name: str = "risk-classifier"

        self._rmq = Consumer(
            os.environ.get("RMQ_SERVICE_QUEUE", f"{self._service_name}.queue"),
            int(os.environ.get("prefetch_count", 1)),
            self.classify_stock_risk
        )
        self.train_model()

    def train_model(self):
        """
        Trains the RandomForestClassifier model using sample data.
        """
        data = pd.DataFrame({
            'volatility': [0.2, 0.15, 0.3, 0.25],
            'average_return': [0.05, 0.03, 0.02, 0.06],
            'market_correlation': [0.8, 0.75, 0.9, 0.85],
            'risk_category': [0, 0, 1, 1]  # 0 - низкий, 1 - высокий
        })

        features = data[['volatility', 'average_return', 'market_correlation']]
        labels = data['risk_category']

        x_train, _, y_train, _ = train_test_split(features, labels, test_size=0.2, random_state=42)

        x_train_scaled = self._scaler.fit_transform(x_train)
        self._rf_model.fit(x_train_scaled, y_train)

        LOGGER.info("Risk model is trained")

    def classify_stock_risk(self, data: dict):
        """
        Classifies the risk level based on input data.

        :param dict data: A dictionary containing stock metrics for classification.
        """
        input_data = pd.DataFrame(
            [[
                data['volatility'],
                data['average_return'],
                data['market_correlation']
            ]],
            columns=['volatility', 'average_return', 'market_correlation']
        )
        input_data_scaled = self._scaler.transform(input_data)

        risk_category = self._rf_model.predict(input_data_scaled)[0]
        return self._risk_labels[risk_category]


def start_service():
    """
    Starts the Risk Classifier service.
    """
    risk_clf = RiskClassifier()

    LOGGER.info("Start Risk Classifier")
    risk_clf._rmq.start_consuming()


if __name__ == '__main__':
    start_service()
