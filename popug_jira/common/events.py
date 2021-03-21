from kafka.errors import KafkaError

def send_event(producer, topic, event):
    future = producer.send(topic, event.json())
    try:
        record_metadata = future.get(timeout=10)
    except KafkaError as e:
        print('Error when seding event:', e)

    # Successful result returns assigned partition and offset
    print('[CUD] send event: {} to topic `{}`, partition: {}, offset: {}'.format(
        event, record_metadata.topic, record_metadata.partition, record_metadata.offset))

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


class AccountCreatedCUD(EventBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class AccountChangedCUD(EventBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class AccountRoleChangedCUD(EventBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class TaskCreatedBE(EventBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class TaskAssignedBE(EventBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class TaskClosedBE(EventBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)