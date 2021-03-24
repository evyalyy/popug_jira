
class SchemaRegistryEntry(object):

    def __init__(self, schema_type, handler):
        self.schema_type = schema_type
        self.handler = handler

    def __str__(self):
        return 'SchemaRegistryEntry(type={}, handler={})'.format(self.schema_type, self.handler)

    def __repr__(self):
        return self.__str__()

class SchemaRegistry(object):

    def __init__(self):
        self.schemas = {}

    def register(self, version, schema_type, handler=None):
        if not version in self.schemas:
            self.schemas[version] = dict()

        curr_version_schemas = self.schemas[version]

        schema_name = schema_type.__name__
        if schema_name in curr_version_schemas:
            raise KeyError('Schema {} already in schemas for version {}'.format(schema_name, version))

        curr_version_schemas[schema_name] = SchemaRegistryEntry(schema_type, handler)

    def _get_curr_version_schemas(self, version):
        if not version in self.schemas:
            raise KeyError('Version {} is not registered'.format(version))

        return self.schemas[version]

    def _get_schema_by_name(self, version, schema_name):

        curr_version_schemas = self._get_curr_version_schemas(version)

        if schema_name not in curr_version_schemas:
            raise KeyError('Schema {} not registered for version {}'.format(schema_name, version))

        return curr_version_schemas[schema_name]

    def has_registered_schema(self, version, event):

        curr_version_schemas = self._get_curr_version_schemas(version)

        return event.__class__.__name__ in curr_version_schemas

    def get_schema_from_meta(self, meta):
        return self._get_schema_by_name(meta.version, meta.event_type)
