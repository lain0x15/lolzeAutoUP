from schema import Schema, SchemaError, And, Or, Optional

configSchema = Schema ({
    'tag': str,
    'periodInSeconds': int
})