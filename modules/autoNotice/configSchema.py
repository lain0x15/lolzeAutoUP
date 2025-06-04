from schema import Schema, SchemaError, And, Or, Optional

configSchema = Schema ({
    'pagePerUrl': int,
    'marketURLs': [{
        'url': str,
        'searchTransactionsTitle': [str]
    }]
})