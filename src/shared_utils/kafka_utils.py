import json
import logging
import os
import time

from kafka import KafkaProducer, KafkaConsumer


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





#############################

# class KafkaUtils:

#     _producer = None

#     @classmethod
#     def get_producer(cls):

#         if cls._producer is None:

#             bootstrap_servers = os.getenv(
#                 "KAFKA_PRODUCER_SERVERS",
#                 "localhost:9092"
#             )

#             cls._producer = KafkaProducer(
#                 bootstrap_servers=bootstrap_servers,
#                 acks="all",
#                 retries=3,
#                 linger_ms=0,
#                 batch_size=16384,
#                 value_serializer=lambda x: json.dumps(
#                     x,
#                     default=str
#                 ).encode("utf-8"),
#                 key_serializer=lambda x: (
#                     x.encode("utf-8")
#                     if x else None
#                 ),
#             )

#         return cls._producer

#     @classmethod
#     def send_message(
#         cls,
#         topic: str,
#         value: dict,
#         key: str | None = None,
#         headers: list | None = None,
#         wait_for_ack: bool = False,
#     ):

#         producer = cls.get_producer()

#         future = producer.send(
#             topic,
#             key=key,
#             value=value,
#             headers=headers or [],
#         )

#         if wait_for_ack:

#             metadata = future.get(timeout=10)

#             return {
#                 "topic": metadata.topic,
#                 "partition": metadata.partition,
#                 "offset": metadata.offset,
#             }

#         return future

    @classmethod
    def create_consumer(
        cls,
        topics: list[str],
        *,
        group_id: str,
        bootstrap_servers: str | list[str] | None = None,
        client_id: str | None = None,
        auto_offset_reset: str = "latest",
        enable_auto_commit: bool = False,
    ):

        if bootstrap_servers is None:
            bootstrap_servers = os.getenv(
                "KAFKA_CONSUMER_SERVERS",
                "localhost:9092",
            )

        if isinstance(bootstrap_servers, str):
            bootstrap_servers = bootstrap_servers.split(",")

        return KafkaConsumer(
            *topics,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            client_id=client_id,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=enable_auto_commit,
            value_deserializer=lambda m: json.loads(
                m.decode("utf-8")
            ),
        )

    @classmethod
    def consume_forever(
        cls,
        *,
        topics: list[str],
        handler,
        group_id: str,
        bootstrap_servers: str | list[str] | None = None,
        client_id: str | None = None,
        auto_offset_reset: str = "latest",
        enable_auto_commit: bool = False,
        retry_seconds: int = 30,
    ):

        while True:

            consumer = None

            try:

                consumer = cls.create_consumer(
                    topics=topics,
                    group_id=group_id,
                    bootstrap_servers=bootstrap_servers,
                    client_id=client_id,
                    auto_offset_reset=auto_offset_reset,
                    enable_auto_commit=enable_auto_commit,
                )

                logging.info(
                    f"Listening on topics={topics}"
                )

                for message in consumer:

                    handler(
                        message=message,
                        consumer=consumer,
                    )

            except Exception as ex:

                logging.exception(
                    "Kafka consumer failed"
                )

                if consumer:
                    try:
                        consumer.close()
                    except Exception:
                        pass

                time.sleep(retry_seconds)

    @staticmethod
    def commit(consumer):

        consumer.commit()

    # @staticmethod
    # def close():

    #     if KafkaUtils._producer:
    #         KafkaUtils._producer.flush()
    #         KafkaUtils._producer.close()
    #         KafkaUtils._producer = None