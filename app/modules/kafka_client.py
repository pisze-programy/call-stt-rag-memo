import json
import os

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer


class KafkaManager:
    _producer: AIOKafkaProducer | None = None

    @classmethod
    async def get_producer(cls) -> AIOKafkaProducer:
        if cls._producer is None:
            cls._producer = AIOKafkaProducer(
                bootstrap_servers=[os.getenv("KAFKA_BROKER")],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all'
            )
            assert cls._producer is not None
            await cls._producer.start()
        return cls._producer

    @classmethod
    async def stop_producer(cls):
        if cls._producer is not None:
            await cls._producer.stop()
            cls._producer = None

    @classmethod
    def get_consumer(cls, topic: str, group_id: str) -> AIOKafkaConsumer:
        return AIOKafkaConsumer(
            topic,
            group_id=group_id,
            bootstrap_servers=os.getenv("KAFKA_BROKER"),
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=False
        )


async def send_event(topic: str, payload: dict):
    producer = await KafkaManager.get_producer()
    await producer.send_and_wait(topic, value=payload)