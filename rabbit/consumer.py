"""
Module defines a `Consumer` class responsible for handling RabbitMQ message.
"""
import os
import json
import pika

from utils.logger import LOGGER

class Consumer:

    def __init__(self, queue: str, prefetch_count: int, callback) -> None:
        """
        Initializes the consumer with necessary configurations.
        """
        self._connection = None
        self._channel = None
        self._prefetch_count = prefetch_count
        self._queue = queue
        self._rmq_url = os.environ.get("RMQ_URL", "amqp://user:password@rabbitmq:5672")

        self._callback = callback

    def create_connection(self):
        """
        Establish connection to RabbitMQ using AsyncioConnection.

        :rtype: pika.adapters.blocking_connection.BlockingConnection
        :return: AsyncioConnection object
        """
        LOGGER.info(f"Connecting to {self._rmq_url}")
        connection = pika.BlockingConnection(pika.URLParameters(self._rmq_url))
        return connection

    def open_channel(self):
        """
        Opens a new channel for communication with RabbitMQ.
        """
        return self._connection.channel()

    def set_qos(self):
        """
        Set the QoS (quality of service) for message prefetching.
        """
        if self._prefetch_count < 1:
            LOGGER.warning("Prefetch count is less than 1, setting to default (1).")
            self._prefetch_count = 1

        self._channel.basic_qos(prefetch_count=self._prefetch_count)
        LOGGER.info(f'QOS set to: {self._prefetch_count}')

    def on_request(self, ch, basic_deliver, props, body):
        """
        Handles an incoming RPC request.

        :param pika.channel.Channel ch: The channel object through which the message was received.
        :param pika.Spec.Basic.Deliver basic_deliver: Delivery details (e.g., delivery tag).
        :param pika.Spec.BasicProperties props: Message properties
        :param bytes body: The message body (in JSON format).
        """
        LOGGER.info(f'Get request from main service, message #{basic_deliver.delivery_tag}')
        json_data = json.loads(body.decode('utf-8'))
        response = self._callback(json_data)

        ch.basic_publish(
            exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(correlation_id=props.correlation_id),
            body=str(response)
        )
        ch.basic_ack(delivery_tag=basic_deliver.delivery_tag)
        LOGGER.info(f'Send response to main service and acknowledge message #{basic_deliver.delivery_tag}')

    def start_consuming(self):
        """
        Starts the consumer to listen for incoming messages.
        """
        with self.create_connection() as connection:
            self._connection = connection

            self._channel = self.open_channel()

            self._channel.queue_declare(queue=self._queue)
            self.set_qos()

            self.add_on_cancel_callback()
            self._channel.basic_consume(queue=self._queue, on_message_callback=self.on_request)
            try:
                LOGGER.info("Awaiting RPC requests")
                self._channel.start_consuming()
            except KeyboardInterrupt:
                LOGGER.info("Stopping consumer")
                self._channel.stop_consuming()

    def add_on_cancel_callback(self):
        """
        Add a callback when RabbitMQ cancels message consumption.
        """
        LOGGER.info('Adding consumer cancellation callback')
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        """
        Callback when RabbitMQ cancels a consumer.

        :param pika.frame.Method method_frame: The Basic.Cancel frame
        """
        LOGGER.info(f'Consumer was cancelled remotely, shutting down: {method_frame}')
        if self._channel:
            self._channel.close()
