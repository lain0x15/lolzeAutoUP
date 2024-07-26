from schema import Schema, SchemaError, And, Or, Optional

configSchema = Schema ({
    'methodSticky': Or('pdate_to_up', 'price_to_down', 'price_to_up')
})