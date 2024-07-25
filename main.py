import requests, logging, time, importlib, yaml
from schema import Schema, SchemaError, And, Or, Optional
from pathlib import Path
from logging.handlers import RotatingFileHandler

class lolzeAutoUPException(Exception):
    pass

class lolzeAutoUP:
    def __init__(self):
        self.baseFolder = Path(__file__).parent
        self.configFilePath =  self.baseFolder / 'config.yaml'
        self.logFolderPath = self.baseFolder / 'logs'
        self.modulesFolderPath = self.baseFolder / 'modules'
        self.config = {}
        self.lastReques = {
            'request': time.time(),
            'searchRequest': time.time()
        }
        self.tmpVarsForModules = {}
        handler = RotatingFileHandler(filename=self.logFolderPath / 'lolzeAutoUP.log', mode='a+', maxBytes=50*1024*1024, 
                                         backupCount=1, encoding='utf-8-sig', delay=False)
        logging.basicConfig(level=logging.NOTSET, handlers=[handler])

    def __loadConfig(self, configFilePath):
        self.log (f'Проверяю существование файла конфигурации: {configFilePath}', logLevel='debug')
        configFilePath = Path(configFilePath)
        if configFilePath.is_file():
            self.log ('Файл конфигурации существует', logLevel='debug')
        else:
            raise Exception (f'Не существует файла конфигурации {configFilePath}')
        self.log ('Загружаю данные из файла конфигурации', logLevel='debug')
        with open (configFilePath, encoding='utf-8-sig') as config:
            tmpConfig = yaml.load(config, Loader=yaml.FullLoader)
            if sorted(tmpConfig.items()) != sorted(self.config.items()):
                if not self.__checkConfig (tmpConfig):
                    raise lolzeAutoUPException('Неправильный конфиг')
                self.config = tmpConfig
                self.log ('Конфигурация загружена успешно', logLevel='debug')
                return {'status': 'changed'}
            else:
                self.log ('Конфигурация загружена успешно. Изменений в конфигурации нету', logLevel='debug')
                return {'status': 'ok'}

    def log (self, msg, logLevel: str = 'debug'):
        handlers = {
            'info': lambda msg: logging.info(msg),
            'debug': lambda msg: logging.debug(msg),
            'error': lambda msg: logging.error(msg),
        }
        allowedLoglevels = [*handlers.keys()]

        handler = handlers.get(logLevel, lolzeAutoUPException (f'Ошибка в функции log, неправильно задан logLevel. Значение {logLevel}, допустимые значения {allowedLoglevels}'))
        if isinstance(handler, Exception):
            raise handler

        terminalLevels = self.config.get('logs', {}).get('terminalLevels', allowedLoglevels)
        if logLevel in terminalLevels:
            print(msg)

        telegramLevels = self.config.get('logs', {}).get('telegramLevels', allowedLoglevels)
        if logLevel in telegramLevels:
            pass
        handler(msg)

    def __checkConfig (self, config):
        config_schema = Schema({
            Optional('debug'): bool,
            'lolze': {
                'token': Or(str, error='Неправильное значение token в конфигурации'),
                'proxy': dict,
                'baseURLmarket': str,
                'rateLimit': {
                    'request': Or(int, float, error='Неправильное значение request в конфигурации'),
                    'searchRequest': Or(int, float, error='Неправильное значение searchRequest в конфигурации')
                }
            },
            Optional ('logs'): {
                Optional('terminalLevels'): [Or('info', 'debug', 'error', error='Неправильное значения параметра terminalLevels в конфигурации')],
                Optional('telegramLevels'): [Or('info', 'debug', 'error', error='Неправильное значения параметра telegramLevels в конфигурации')]
            },
            'modules': dict
        })
        module_config_schema = Schema ({
            Optional('enabled'): bool,
            'params': dict
        })

        try:
            config_schema.validate (config)
        except SchemaError as error:
            raise error
        for module in config['modules']:
            try:
                module_config_schema.validate(config['modules'][module])
                configSchemaPath = self.modulesFolderPath / f'{module}/configSchema.py'
                if configSchemaPath.is_file():
                    self.log (f'Файл configSchema.py для модуля {module} существует', logLevel='debug')
                    spec = importlib.util.spec_from_file_location('main', configSchemaPath)
                    configSchema = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(configSchema)
                    configSchema.configSchema.validate(config['modules'][module]['params'])
                else:
                    self.log (f'Не существует файл configSchema.py для модуля {module}. Проверка параметров для данного модуля осуществятся не будет', logLevel='debug')
            except SchemaError as error:
                raise Exception(f'Ошибка в конфигурационном файле в разделе модуля {module} | {error}')
        return True
        
    def sendRequest (
        self, 
        pathData: str, 
        method: str = 'GET',
        params: dict = {},
        headersRewrite = {},
        payload = None,
        typeRequest: str = "searchRequest"
    ) -> dict:
        
        token = self.config['lolze']['token']
        proxy = self.config['lolze']['proxy']
        baseURLmarket = self.config['lolze']['baseURLmarket']
        
        if typeRequest == 'searchRequest':
            rateLimit = self.config['lolze']['rateLimit'][typeRequest]
        elif typeRequest  == 'request':
            rateLimit = self.config['lolze']['rateLimit'][typeRequest]
        else:
            raise lolzeAutoUPException(f'Ошибка в функции sendRequest. Неправильно указан typeRequest. Значение {typeRequest}')
            
        if (t := time.time() -  self.lastReques[typeRequest]) < rateLimit:
            time.sleep(rateLimit - t)
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {token}"
        }
        headers.update (headersRewrite)
        url = baseURLmarket + pathData
        methods = {
            'GET': requests.get,
            'POST': requests.post,
            'DELETE': requests.delete
        }
        handlers = {
            200: lambda response: response.json(),
            400: lambda response: Exception(f'Сайт выдал ошибку {response.status_code}\nпри запросе к ссылке {url}\n{response.content.decode("unicode-escape")}'),
            403: lambda response: response.json(),
            429: lambda response: Exception(f'Слишком много запросов к api сайта. Сайт выдал ошибку {response.status_code}')
        }
        if method not in methods:
            raise Exception(f'Неправильный метод {method}, ожидается GET, POST, DELETE')
            
        response = methods[method](url, params=params, headers=headers, timeout=(10, 600), proxies=proxy, data=payload)
        handler = handlers.get(response.status_code, lambda response: Exception(f'Сайт выдал ошибку {response.status_code}'))
        
        try:
            result = handler(response)
        finally:
            self.lastReques[typeRequest] = time.time()

        if isinstance(result, Exception):
            raise result
            
        if result.get('error') in ['invalid_token']:
            raise lolzeAutoUPException(response['error'])
        return result

    def getMarketPermissions (self) -> dict:
        permissions = self.sendRequest("/me", typeRequest='request')['user']['permissions']['market']
        result = { 
            'stickItem': permissions['stickItem'],
            'bumpItemCountInPeriod': permissions['bumpItemCountInPeriod'],
            'bumpItemPeriod': permissions['bumpItemPeriod'],
            'canBumpOwnItem': permissions['canBumpOwnItem'],
            'hasAccessToMarket': permissions['hasAccessToMarket']
        }
        return result

    def getOwnedAccounts (
        self, 
        shows: list = ['active', 'paid', 'deleted', 'awaiting'],
        limitPagesInShow: int = 1, 
        order_by: str = 'price_to_down'
    ) -> dict: 
        result = {}
        for show in shows:
            tempResult = []
            page = 1
            while True:
                if limitPagesInShow > 0 and limitPagesInShow <= page - 1:
                    break
                acconuts = self.sendRequest(f'user//items?page={page}&show={show}&order_by={order_by}', typeRequest='request')['items']
                if acconuts == []:
                    break
                page += 1
                for account in acconuts:
                    tempResult.append({'item_id':account['item_id'],
                            'item_state': account['item_state'],
                            'published_date': account['published_date'],
                            'refreshed_date': account['refreshed_date'],
                            'price': account['price'],
                            'is_sticky': account['is_sticky'],
                            'canStickItem': account['canStickItem'],
                            'canUnstickItem': account['canUnstickItem'],
                            'canUpdateItemStats': account['canUpdateItemStats'],
                            'tags': account['tags']
                        }
                    )
            result.update ({f'{show}':tempResult})
        return result

    def run (self):
        while True:
            try:
                self.__loadConfig(self.configFilePath)
            except Exception as err:
                self.log(err)
                continue
            for module in self.config['modules']:
                self.__loadConfig(self.configFilePath)
                if self.config['modules'][module].get('enabled', False):
                    params = self.config['modules'][module]['params']
                    spec = importlib.util.spec_from_file_location('run', self.modulesFolderPath / f'{module}/main.py')
                    moduleExec = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(moduleExec)
                    try:
                        moduleExec.run(self, **params)
                    except Exception as err:
                        self.log(f'Ошибка в модуле {module} | {err}')
                        if self.config.get('debug', False):
                            raise err

if __name__ == '__main__':
    lolzeAutoUpBot = lolzeAutoUP()
    lolzeAutoUpBot.run()