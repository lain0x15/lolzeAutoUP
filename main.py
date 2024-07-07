import requests, json, logging, time, importlib
from pathlib import Path
from logging.handlers import RotatingFileHandler

class lolzeAutoUPException(Exception):
    pass

class lolzeAutoUP:
    def __init__(self):
        self.baseFolder = Path(__file__).parent
        self.configFilePath =  self.baseFolder / 'config.json'
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
            tmpConfig = json.load(config)
            if sorted(tmpConfig.items()) != sorted(self.config.items()):
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
        print(msg)
        handler(msg)

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

    def run (self):
        while True:
            self.__loadConfig(self.configFilePath)
            for module in self.config['modules']:
                if self.config['modules'][module].get('enabled', False):
                    params = self.config['modules'][module]['params']
                    spec = importlib.util.spec_from_file_location('run', self.modulesFolderPath / f'{module}/main.py')
                    moduleExec = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(moduleExec)
                    moduleExec.run(self, **params)

if __name__ == '__main__':
    lolzeAutoUpBot = lolzeAutoUP()
    lolzeAutoUpBot.run()