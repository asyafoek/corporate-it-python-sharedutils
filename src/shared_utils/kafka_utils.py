import json
import os
from kafka import KafkaProducer


class KafkaUtils:

    _producer = None

    @classmethod
    def get_producer(cls):

        if cls._producer is None:

            bootstrap_servers = os.getenv(
                "KAFKA_PRODUCER_SERVERS",
                "localhost:9092"
            )

            cls._producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                acks="all",
                retries=3,
                linger_ms=0,
                batch_size=16384,
                value_serializer=lambda x: json.dumps(
                    x,
                    default=str
                ).encode("utf-8"),
                key_serializer=lambda x: (
                    x.encode("utf-8")
                    if x else None
                ),
            )

        return cls._producer

    @classmethod
    def send_message(
        cls,
        topic: str,
        value: dict,
        key: str | None = None,
        headers: list | None = None,
        wait_for_ack: bool = False,
    ):

        producer = cls.get_producer()

        future = producer.send(
            topic,
            key=key,
            value=value,
            headers=headers or [],
        )

        if wait_for_ack:

            metadata = future.get(timeout=10)

            return {
                "topic": metadata.topic,
                "partition": metadata.partition,
                "offset": metadata.offset,
            }

        return future

    @classmethod
    def flush(cls):

        if cls._producer:
            cls._producer.flush()

    @classmethod
    def close(cls):

        if cls._producer:
            cls._producer.flush()
            cls._producer.close()
            cls._producer = None