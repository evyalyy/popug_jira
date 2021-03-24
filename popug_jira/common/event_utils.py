from kafka.errors import KafkaError
import json

from typing import List, Any
from pydantic import BaseModel


class EventMeta(BaseModel):
    event_type: str
    version: int
    producer: str


class Event(BaseModel):
    meta: EventMeta
    body: Any


def send_event(producer, topic, schema_registry, version, event):

    if not schema_registry.has_registered_schema(version, event):
        print('ERROR, schema version {} for event {} not registered'.format(version, event))
        return

    meta = EventMeta(version=version, event_type=event.__class__.__name__, producer=producer.config['client_id'])
    event_to_send = Event(meta=meta, body=event)
    print('EVENT JSON:', event_to_send.json())

    future = producer.send(topic, event_to_send.json())
    try:
        record_metadata = future.get(timeout=10)
    except KafkaError as e:
        print('Error when sending event:', e)
        return

    # Successful result returns assigned partition and offset
    print('[EVENT] sent event to topic `{}`, partition: {}, offset: {}'.format(
            record_metadata.topic, record_metadata.partition, record_metadata.offset))


def consume_events(consumer, schema_registry, label):
    print('[{}] CONSUMER STARTED'.format(label))
    while True:
        for message in consumer:
            # message value and key are raw bytes -- decode if necessary!
            # e.g., for unicode: `message.value.decode('utf-8')`
            print ("[{}] consumed {}:{}:{}: key={} value={}".format(label, message.topic, message.partition,
                                                  message.offset, message.key,
                                                  message.value))

            parsed_message = json.loads(json.loads(message.value.decode('ascii')))

            event = Event(**parsed_message)
            schema_entry = schema_registry.get_schema_from_meta(event.meta)

            event_body = schema_entry.schema_type(**event.body)

            schema_entry.handler(event_body)
