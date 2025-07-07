from schema import Schema, SchemaError, And, Or, Optional

configSchema = Schema ({
    'pagesPerUrl': int,
    Optional('save_in_file'): bool,
    Optional('retry_page_count'): int,
    'marketURLs': [{
        'url': str,
        'searchTransactionsTitle': [str]
    }]
})