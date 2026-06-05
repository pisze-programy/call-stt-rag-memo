import json
import os

from kafka import KafkaProducer

def get_producer():
    broker = os.getenv("KAFKA_BROKER")
    return KafkaProducer(
        bootstrap_servers=[broker],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )