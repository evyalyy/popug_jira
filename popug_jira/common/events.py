from kafka.errors import KafkaError
from marshmallow import Schema, fields
import json


class EventMetaSchema(Schema):
    event_type = fields.Str()
    version = fields.Int()
    producer = fields.Str()


class AccountCreatedCUDSchema(Schema):
    meta = fields.Nested(EventMetaSchema)
    account_id = fields.Int()
    name = fields.Str()
    email = fields.Email()
    roles = fields.List(fields.Int())


class AccountChangedCUDSchema(Schema):
    meta = fields.Nested(EventMetaSchema)
    account_id = fields.Int()
    name = fields.Str()
    email = fields.Email()
    roles = fields.List(fields.Int())


class TaskCreatedBESchema(Schema):
    meta = fields.Nested(EventMetaSchema)
    task_id = fields.Int()
    description = fields.Str()


class TaskAssignedBESchema(Schema):
    meta = fields.Nested(EventMetaSchema)
    task_id = fields.Int()
    assignee_id = fields.Int()


class TaskClosedBESchema(Schema):
    meta = fields.Nested(EventMetaSchema)
    task_id = fields.Int()
    assignee_id = fields.Int()


from typing import List, Any
from pydantic import BaseModel

class EventMetaSchema2(BaseModel):
    event_type: str
    version: int
    producer: str

class AccountCreatedCUDSchema2(BaseModel):
    account_id: int
    name: str
    email: str
    roles: List[int]

class AccountChangedCUDSchema2(BaseModel):
    account_id: int
    name: str
    email: str
    roles: List[int]

class EventSchema(BaseModel):
    meta: EventMetaSchema2
    body: Any


schemas = {}
schemas2 = {}


class SchemaRegistryEntry(object):

    def __init__(self, schema_type, handler):
        self.schema_type = schema_type
        self.handler = handler

    def __str__(self):
        return 'SchemaRegistryEntry(type={}, handler={})'.format(self.schema_type, self.handler)

    def __repr__(self):
        return self.__str__()


def register_schema(version, schema_type, handler=None):
    global schemas
    global schemas2
    if not version in schemas:
        schemas[version] = dict()
        schemas2[version] = dict()
    schemas[version][schema_type.__name__] = schema_type
    schemas2[version][schema_type.__name__] = SchemaRegistryEntry(schema_type, handler)


def get_schema_by_type(version, event_type):
    global schemas
    if not version in schemas:
        raise ValueError('No version {} in schemas'.format(version))
    return schemas[version][event_type.__name__]


# def get_schema_by_type2(version, event_type):
#     global schemas2
#     if not version in schemas2:
#         raise ValueError('No version {} in schemas2'.format(version))
#     return schemas2[version][event_type.__name__]

def has_registered_schema(version, event):
    global schemas2
    if not version in schemas2:
        return False

    print('[has_registered_schema]. event: {}, event_type: {} schemas2: {}'.format(event, event.__class__.__name__, schemas2))
    return event.__class__.__name__ in schemas2[version]

def get_schema_by_name(version, event_name):
    global schemas
    if not version in schemas:
        raise ValueError('No version {} in schemas'.format(version))

    return schemas[version][event_name]


register_schema(1, AccountCreatedCUDSchema)
register_schema(1, AccountChangedCUDSchema)
register_schema(1, TaskCreatedBESchema)
register_schema(1, TaskAssignedBESchema)
register_schema(1, TaskClosedBESchema)



def send_event(producer, topic, version, event_type, body, body2):

    if not has_registered_schema(version, body2):
        print('ERROR, schema version {} for event {} not registered'.format(version, body2))
        return
    meta2 = EventMetaSchema2(version=version, event_type=body2.__class__.__name__, producer=producer.config['client_id'])
    event = EventSchema(meta=meta2, body=body2)
    print(body2)
    print(event)
    print('EVENT JSON:', event.json())

    schema_type = get_schema_by_type(version, event_type)
    meta = {'version': version, 'event_type': schema_type.__name__, 'producer': producer.config['client_id']}
    body['meta'] = meta

    errors = schema_type().validate(body)
    
    if len(errors) > 0:
        raise ValueError('Validation errors: {}'.format(errors))

    future = producer.send(topic, body)
    try:
        record_metadata = future.get(timeout=10)
    except KafkaError as e:
        print('Error when seding event:', e)

    # Successful result returns assigned partition and offset
    print('[EVENT] send event: {} to topic `{}`, partition: {}, offset: {}'.format(
        body, record_metadata.topic, record_metadata.partition, record_metadata.offset))


def get_schema_type_from_meta(message_json, version):
    meta = message_json['meta']
    if meta['version'] != version:
        print('[{}][ERROR] wrong version (required: {}). meta: {}'.format(label, version, meta))
        return None

    return get_schema_by_name(version, meta['event_type'])


def consume_accounts(message_json, label, EmployeeModel):

    event = EventSchema(**message_json)
    print(event.meta)
    schema_type = get_schema_type_from_meta(message_json, 1)
    if schema_type is None:
        # Need some handling of unexpected version
        print('Incompatible version')
        return

    errors = schema_type().validate(message_json)
    
    if len(errors) > 0:
        print('[{}][ERROR] consume validation errors: {}'.format(label, errors))
        return

    account_id = message_json['account_id']

    if schema_type == AccountCreatedCUDSchema:
        emp = EmployeeModel.objects.create(id=account_id,
                                            name=message_json['name'],
                                            roles=message_json['roles'])
        emp.save()
    elif schema_type == AccountChangedCUDSchema:
        try:
            emp = EmployeeModel.objects.get(id=account_id)
            emp.name = message_json['name']
            emp.roles = message_json['roles']
            emp.save()
        except EmployeeModel.DoesNotExist:
            print('[{}][ERROR] account {} does not exist'.format(label, account_id))


def consumer_func(consumer, func, label, *args):
    print('[{}] CONSUMER STARTED'.format(label))
    while True:
        for message in consumer:
            # message value and key are raw bytes -- decode if necessary!
            # e.g., for unicode: `message.value.decode('utf-8')`
            print ("[{}] consumed {}:{}:{}: key={} value={}".format(label, message.topic, message.partition,
                                                  message.offset, message.key,
                                                  message.value))
            parsed_message = json.loads(message.value.decode('ascii'))
            print('[{}] meta: {}'.format(label, parsed_message['meta']))

            func(parsed_message, label, *args)


def make_event(**kwargs):
    return kwargs
