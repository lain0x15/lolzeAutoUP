from schema import Schema, SchemaError, And, Or, Optional

configSchema = Schema ({
    'pagesPerUrl': int,
    'marketURLs': [{
        'url': str,
        'searchTransactionsTitle': [str]
    }]
})