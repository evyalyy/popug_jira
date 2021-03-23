from kafka.errors import KafkaError
from marshmallow import Schema, fields

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

class AccountRoleChangedCUDSchema(Schema):
    meta = fields.Nested(EventMetaSchema)
    account_id = fields.Int()
    roles = fields.List(fields.Int())

schemas = {}

def register_schema(schemas, version, sch):
    if not version in schemas:
        schemas[version] = dict()
    schemas[version][sch.__name__] = sch

def get_schema_by_type(version, event_type):
    global schemas
    if not version in schemas:
        raise ValueError('No version {} in schemas'.format(version))
    return schemas[version][event_type.__name__]

def get_schema_by_name(version, event_name):
    global schemas
    if not version in schemas:
        raise ValueError('No version {} in schemas'.format(version))

    return schemas[version][event_name]

register_schema(schemas, 1, AccountCreatedCUDSchema)
register_schema(schemas, 1, AccountChangedCUDSchema)
register_schema(schemas, 1, AccountRoleChangedCUDSchema)


def send_event(producer, topic, version, event_type, body):
    sch = get_schema_by_type(version, event_type)
    meta = {'version': version, 'event_type': sch.__name__, 'producer': producer.config['client_id']}
    body['meta'] = meta

    errors = sch().validate(body)
    
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


def make_event(**kwargs):
    return kwargs


class EventBase(object):

    def __init__(self, **kwargs):
        self.attributes  = kwargs

    def __str__(self):
        return '{}({})'.format(type(self).__name__, ','.join(map(lambda item: '{}={}'.format(item[0], item[1]),self.attributes.items())))

    def json(self):
        out = {}
        for k,v in self.attributes.items():
            out[k] = v
        out['type'] = type(self).__name__
        return out


# class AccountCreatedCUD(EventBase):

#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)


# class AccountChangedCUD(EventBase):

#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)


# class AccountRoleChangedCUD(EventBase):

#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)


class TaskCreatedBE(EventBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class TaskAssignedBE(EventBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class TaskClosedBE(EventBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)