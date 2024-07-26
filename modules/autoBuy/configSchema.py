from schema import Schema, SchemaError, And, Or, Optional

configSchema = Schema ({
    Optional('limitSumOfBalace'): int,
    Optional('attemptsBuyAccount'): int,
    'marketURLs': [{
        'url': str,
        Optional('buyWithoutValidation'): bool,
        Optional('autoSellOptions'):{
            'enabled': bool,
            Optional('title'): str,
            Optional('title_en'): str,
            Optional('attemptsSell'): int,
            Optional('price'): int,
            Optional('percent'): int,
            Optional('tags'): list
        }
    }]
})