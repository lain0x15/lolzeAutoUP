from schema import Schema, SchemaError, And, Or, Optional

configSchema = Schema ({
    'pagesPerUrl': int,
    Optional('save_in_file'): bool,
    Optional('retry_page_count'): bool,
    'marketURLs': [{
        'url': str,
        'searchTransactionsTitle': [str]
    }]
})