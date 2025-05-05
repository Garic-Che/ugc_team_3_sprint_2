from confluent_kafka import Consumer, KafkaException
import logging

logger = logging.getLogger(__name__)

class KafkaConsumer:
    def __init__(self, config: dict):
        self.consumer = Consumer(config)

    def consume(self, topic: str, callback):
        self.consumer.subscribe([topic])
        try:
            while True:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    raise KafkaException(msg.error())

                try:
                    callback(msg.value().decode('utf-8'))
                    self.consumer.commit(msg)  # Подтверждение после успешной обработки
                except Exception as e:
                    logger.error(f"Processing failed: {e}")
                    # Можно добавить dead-letter queue

        except KeyboardInterrupt:
            logger.info("Graceful shutdown...")
        finally:
            self.consumer.close()