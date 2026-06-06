import json
import os

from kafka import KafkaProducer, KafkaConsumer


def get_producer():
    broker = os.getenv("KAFKA_BROKER")
    return KafkaProducer(
        bootstrap_servers=[broker],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

def get_consumer(topic):
    return KafkaConsumer(
        topic,
        bootstrap_servers=os.getenv("KAFKA_BROKER"),
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True
    )