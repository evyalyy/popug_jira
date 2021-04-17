from django.db import OperationalError

from kafka.errors import KafkaError
import json
import logging
import uuid

from typing import List, Any
from pydantic import BaseModel

logger = logging.getLogger('root')


class EventMeta(BaseModel):
    event_type: str
    version: int
    producer: str
    event_id: str


class Event(BaseModel):
    meta: EventMeta
    body: Any


def send_event(producer, topic, schema_registry, version, event):

    if not schema_registry.has_registered_schema(version, event):
        logger.error('[{}] schema version {} for event {} not registered'.format(producer.config['client_id'], version, event))
        raise

    meta = EventMeta(version=version,
                     event_type=event.__class__.__name__,
                     producer=producer.config['client_id'],
                     event_id=str(uuid.uuid4()))

    event_to_send = Event(meta=meta, body=event)
    logger.debug('[{}] EVENT JSON: {}'.format(meta.producer,event_to_send.json()))

    future = producer.send(topic, event_to_send.json())
    try:
        record_metadata = future.get(timeout=10)
    except KafkaError as e:
        logger.error('[{}] Error when sending event: {}'.format(meta.producer,str(e)))
        raise

    # Successful result returns assigned partition and offset
    logger.debug('[{}] sent event to topic `{}`, partition: {}, offset: {}'.format(meta.producer,
            record_metadata.topic, record_metadata.partition, record_metadata.offset))


def consume_events(consumer, schema_registry, label):
    logger.info('[{}] CONSUMER STARTED'.format(label))
    while True:
        for message in consumer:
            logger.debug ("[{}] consumed {}:{}:{}: key={} value={}".format(label, message.topic, message.partition,
                                                  message.offset, message.key,
                                                  message.value))

            parsed_message = json.loads(message.value.decode('ascii'))

            event = Event(**parsed_message)
            try:
                schema_entry = schema_registry.get_schema_from_meta(event.meta)
                event_body = schema_entry.schema_type(**event.body)
            except KeyError as e:
                logger.warning('[{}] event ignored: {}'.format(label, str(e)))
                continue

            consumed = False
            while not consumed and schema_entry.handler:
                try:
                    schema_entry.handler(event_body)
                except OperationalError:
                    continue
                except Exception as e:
                    logger.error('[{}] {}'.format(label, e))
                    break
                consumed = True
