from schema import Schema, SchemaError, And, Or, Optional

configSchema = Schema ({
    'pagesPerUrl': int,
    Optional('save_in_file'): bool,
    'marketURLs': [{
        'url': str,
        'searchTransactionsTitle': [str]
    }]
})