from schema import Schema, SchemaError, And, Or, Optional

configSchema = Schema ({
    'marketURLs': [{
        'url': str
    }]
})