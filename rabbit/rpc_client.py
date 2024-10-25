"""
RPC Client Module for RabbitMQ.
"""
import os
import uuid

import pika

from utils.logger import LOGGER


class RpcClient():

    def __init__(self):
        """
        Initializes the RPC client.
        """
        self._rmq_url = os.environ.get("RMQ_URL", 'amqp://user:password@rabbitmq:5672')
        self.connection = pika.BlockingConnection(pika.URLParameters(self._rmq_url))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        )

        self.response = None
        self.corr_id = None

    def on_response(self, ch, basic_deliver, props, body):
        """
        Callback function to handle responses from the service.

        :param pika.channel.Channel ch: The channel object through which the message was received.
        :param pika.Spec.Basic.Deliver basic_deliver: Delivery details (e.g., delivery tag).
        :param pika.Spec.BasicProperties props: Message properties
        :param bytes body: The message body (in JSON format).
        """
        if self.corr_id == props.correlation_id:
            self.response = body

    def call_service(self, queue_name: str, request_data: str):
        """
        Sends a request to a service via RabbitMQ and waits for the response.

        :param str queue_name: Name of the RabbitMQ queue.
        :param str request_data: Data to be sent to the service.
        """
        LOGGER.info(f"Requesting service {queue_name}")
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=request_data
        )
        while self.response is None:
            self.connection.process_data_events(time_limit=None)
        return self.response
