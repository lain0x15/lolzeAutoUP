import datetime, time, json, logging, importlib
from .telegramAPI import TelegramAPI
from .lolzeBotApi import lolzeBotApi
from pathlib import Path
from logging.handlers import RotatingFileHandler


class lolzeAutoUpErrorStop(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'lolzeAutoUpErrorStop, {self.message}'
        else:
            return 'lolzeAutoUpErrorStop has been raised'

class lolzeAutoUP:
    def __init__(
        self, 
        configFilePath = 'config.json',
        tmpFolderPath = 'files/tmp',
        modulesPath = 'src/modules',
        filesPath = 'files'
    ) -> None:
        self.__configFilePath = configFilePath
        self.__tmpFolderPath = Path(tmpFolderPath)
        self.__modulesPath = Path(modulesPath)
        self.filesPath = Path (filesPath)
        self.__status = 'running'
        self.__events = []
        self.__config = {}
        self.__modulesInfo = {}
        handler = RotatingFileHandler(filename=self.__tmpFolderPath / 'msg.log', mode='a+', maxBytes=50*1024*1024, 
                                         backupCount=1, encoding=None, delay=False)
        logging.basicConfig(level=logging.NOTSET, handlers=[handler])

    def addEvent (self, event):
        if len(self.__events) > 1000:
            self.__events.pop(0)
        self.__events.append (event)
        eventsFilePath = self.__tmpFolderPath / 'events.json'
        with open(eventsFilePath, 'w') as eventsFile: 
            json.dump(self.__events, eventsFile) 
    
    def getEvents (self):
        eventsFilePath = self.__tmpFolderPath / 'events.json'
        if eventsFilePath.is_file():
            with open(eventsFilePath, 'r') as eventsFile:
                self.__events = json.load(eventsFile)
        return self.__events

    def __loadConfig(self):
        self.log (f'Проверяю существование файла конфигурации: {self.__configFilePath}')
        configFilePath = Path(self.__configFilePath)
        if configFilePath.is_file():
            self.log ('Файл конфигурации существует')
        else:
            raise Exception (f'Не существует файла конфигурации {self.__configFilePath}')
        self.log ('Загружаю данные из файла конфигурации')
        with open (configFilePath) as config:
            tmpConfig = json.load(config)
            if sorted(tmpConfig.items()) != sorted(self.__config.items()):
                self.__config = tmpConfig
                self.log ('Конфигурация загружена успешно')
                return {'status': 'changed'}
            else:
                self.log ('Конфигурация загружена успешно. Изменений в конфигурации нету')
                return {'status': 'ok'}
        
    def sendTelegramMessage (
        self, 
        message: str
    ) -> None:
        try:
            if self.telegramApi is None:
                return
            for telegramID in self.__config.get('telegram')['userIDs']:
                self.telegramApi.send_message(message, telegramID)
        except Exception as err:
            pass
    
    def log (
        self, 
        message: str,
        logLevel: str = 'debug'
    ) -> None:
        print (message)
        if logLevel == 'info':
            logging.info(message)
        elif logLevel == 'error':
            logging.error(message)
        else:
            logging.debug(message)
        if telegramConfig := self.__config.get('telegram'):
            if logLevel in telegramConfig['logLevel']:
                self.sendTelegramMessage(message)
   
    def run (self):
        while self.__status == 'running':
            try:
                if self.__loadConfig()['status'] == 'changed':
                    clients = [x.copy() for x in self.__config['lolze']['clients']]
                    clients = [client for client in  clients if client.pop('enabled', True)]
                    self.lolzeBotApi = lolzeBotApi(clients)
                    self.telegramApi = TelegramAPI(self.__config.get('telegram')['token']) if self.__config.get('telegram')['enabled'] else ''
                for module in self.__config['modules']:
                    if self.__config['modules'][module]['enabled'] == True and self.__modulesInfo.get(module, {}).get('nextRun', 0) <= time.time():
                        params = self.__config['modules'][module]['params']
                        spec = importlib.util.spec_from_file_location('run', self.__modulesPath / f'{module}/main.py')
                        moduleExec = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(moduleExec)
                        nextRun = moduleExec.run(self, **params)
                        self.__modulesInfo.update({module: {'nextRun': nextRun}})
            except Exception as err:
                self.log(f'Ошибка: {err}. Перезапускаюсь.', logLevel='error')
            finally:
                pass