import asyncio, datetime, time, pprint, hashlib
import os
from .telegramAPI import TelegramAPI
from .lolzeBotApi import lolzeBotApi
import logging
from pathlib import Path
import json
from logging.handlers import RotatingFileHandler
from jinja2 import Template


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
        templatesFolderPath = 'files/templates',
        tmpFolderPath = 'files/tmp'
    ) -> None:

        self.__configFilePath = configFilePath
        self.__templatesFolderPath = Path(templatesFolderPath)
        self.__tmpFolderPath = Path(tmpFolderPath)
        self.__status = 'running'
        self.__events = []
        self.__config = {}
        handler = RotatingFileHandler(filename=self.__tmpFolderPath / 'msg.log', mode='a+', maxBytes=50*1024*1024, 
                                         backupCount=1, encoding=None, delay=False)
        logging.basicConfig(level=logging.NOTSET, handlers=[handler])

        self.__modules = {
            "bump": {
                "run": self.__bump,
                "nextRun": 0
            },
            "sendReports": {
                "run": self.__sendReport,
                "nextRun": 0
            },
            "stick": {
                "run": self.__sticky,
                "nextRun": 0
            },
            "autoBuy": {
                "run": self.__autoBuy,
                "nextRun": 0
            },
            "autoSell": {
                "run": self.__autoSell,
                "nextRun": 0
            },
            "autoUpdateInfo": {
                "run": self.__autoUpdateInfo,
                "nextRun": 0
            }
        }

    def __addEvent (self, event):
        if len(self.__events) > 1000:
            self.__events.pop(0)
        self.__events.append (event)
        eventsFilePath = self.__tmpFolderPath / 'events.json'
        with open(eventsFilePath, 'w') as eventsFile: 
            json.dump(self.__events, eventsFile) 
    
    def __getEnevnts (self):
        eventsFilePath = self.__tmpFolderPath / 'events.json'
        if eventsFilePath.is_file():
            with open(eventsFilePath, 'r') as eventsFile:
                self.__events = json.load(eventsFile)
        return self.__events

    def __loadConfig(self):
        self.__log (f'Проверяю существование файла конфигурации: {self.__configFilePath}')
        configFilePath = Path(self.__configFilePath)
        if configFilePath.is_file():
            self.__log ('Файл конфигурации существует')
        else:
            raise Exception (f'Не существует файла конфигурации {self.__configFilePath}')
        self.__log ('Загружаю данные из файла конфигурации')
        with open (configFilePath) as config:
            tmpConfig = json.load(config)
            if sorted(tmpConfig.items()) != sorted(self.__config.items()):
                self.__config = tmpConfig
                self.__log ('Конфигурация загружена успешно')
                return {'status': 'changed'}
            else:
                self.__log ('Конфигурация загружена успешно. Изменений в конфигурации нету')
                return {'status': 'ok'}

    def __sendReport (self):
        report = ''
        profile = self.__lolzeBotApi.getInfoAboutMe()
        balance = profile['balance']
        hold = profile['hold']
        accounts = self.getAccounts()
        linksCount = len(self.__config['modules']['autoBuy']['params']['marketURLs'])
        purchasedCount = 0
        purchasedSum = 0
        paidCount = 0
        paidSum = 0
        purchasedAccounts = self.__lolzeBotApi.getPurchasedAccounts(order_by='pdate_to_down')
        for purchasedAccount in purchasedAccounts:
            a = self.__lolzeBotApi.getAccountInformation(purchasedAccount["item_id"])
            if (time.time() - a['buyer']['operation_date']) <= 24 * 60 * 60:
                purchasedCount += 1
                purchasedSum += a['price']
            else:
                break
        else:
            purchasedCount = -1
        paidAccounts = self.__lolzeBotApi.getOwnedAccounts (shows=['paid'], order_by='pdate_to_down')['paid']
        for paidAccount in paidAccounts:
            a = self.__lolzeBotApi.getAccountInformation(paidAccount["item_id"])
            if (time.time() - a['buyer']['operation_date']) <= 24 * 60 * 60:
                paidCount += 1
                paidSum += a['price']
            else:
                break
        else:
            paidCount = -1
        report += f'Баланс: {balance} + {hold}\n'
        report += f'Кол-во аккаунтов: {accounts["totalItems"]}\n'
        report += f'На сумму: {accounts["totalItemsPrice"]}\n'
        report += f'Закреплённых аккаунтов: {accounts["userItemStates"]["stickied"]["item_count"]}\n'
        report += f'Ссылок в автобае: {linksCount}\n'
        report += f'Куплено за 24 часа: {purchasedCount} на сумму {purchasedSum}\n'
        report += f'Продано за 24 часа: {paidCount} на сумму {paidSum}'
        self.__log(report, logLevel='info')
        self.__modules['sendReports']['nextRun'] = time.time() + 3600
    
    def getAccounts(
        self, 
        order: str = 'price_to_down'
    ) -> dict:
        return self.__lolzeBotApi.sendRequest(pathData='user/items', params={'order_by':order})
    
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
    
    def __log (
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

    def getLastBumps (
        self, 
        count: int
    ) -> list:
        lastBumps = [0 for _ in range(count)]
        accounts = self.__lolzeBotApi.getOwnedAccounts(order_by='pdate_to_down')
        for accountShowType in accounts:
            for account in accounts[accountShowType]:
                if account['published_date'] != account['refreshed_date']:
                    lastBumps.append(account['refreshed_date'])
                    lastBumps.sort(reverse=True)
                    if len(lastBumps) > count:
                        lastBumps.pop()
        return lastBumps
 
    def __bump (self, methodBump) -> None:
        self.__log('Поднятие аккаунтов запущено')
        self.__log('Проверяю разрешения на маркет')
        marketPermissions = self.__lolzeBotApi.getMarketPermissions()
        if marketPermissions['hasAccessToMarket'] != True or marketPermissions['canBumpOwnItem'] != True:
            raise Exception ('Нет доступа к маркету или Нет прав на поднятия аккаунтов')
        else:
            self.__log('Права на поднятие аккаунтов присутствуют')

        countAvailableBumps = 0
        lastBumps = self.getLastBumps(marketPermissions['bumpItemCountInPeriod'])
        for lastBump in lastBumps:
            if time.time() - lastBump >= marketPermissions['bumpItemPeriod'] * 60 * 60:
                countAvailableBumps += 1
        if countAvailableBumps <= 0:
            nextBumpDate = lastBumps.pop() + marketPermissions['bumpItemPeriod'] * 60 * 60
            sleepTime = nextBumpDate - time.time()
            nextBumpDate = datetime.datetime.fromtimestamp(nextBumpDate).strftime('%d-%m-%Y %H:%M:%S')
            self.__log (f'Осталось поднятий: {countAvailableBumps}\nДата следующей попытки поднятия: {nextBumpDate}', logLevel='info')
            sleepTime = sleepTime if sleepTime > 0 else 0
            self.__modules['bump']['nextRun'] = time.time() + sleepTime
            return
        accounts = self.__lolzeBotApi.getOwnedAccounts(shows=['active'], order_by=methodBump)['active']
        for account in accounts:
            if time.time() - account['refreshed_date'] > marketPermissions['bumpItemPeriod'] * 60 * 60:
                response = self.__lolzeBotApi.bumpAccount(item_id = account["item_id"])
                if error := response.get('errors'):
                    self.__log(f'Не удалось поднять аккаунт https://lzt.market/{account["item_id"]}\n{error}', logLevel='info')
                    continue
                self.__log(f'Поднят аккаунт https://lzt.market/{account["item_id"]}', logLevel='info')
                if (countAvailableBumps := countAvailableBumps - 1) <= 0:
                    break
        else:
            nextBumpDate = datetime.datetime.fromtimestamp(3600 + time.time() ).strftime('%d-%m-%Y %H:%M:%S')
            self.__log (f'Осталось поднятий: {countAvailableBumps}\nНет аккаунтов для поднятия. Следующая попытка поднятия {nextBumpDate}', logLevel='info')
            self.__modules['bump']['nextRun'] = time.time() + 3600

    def __sticky(self, methodSticky) -> None:
        self.__log('Закреплениие аккаунтов запущено')
        while True:
            accounts = self.__lolzeBotApi.getOwnedAccounts(shows=['active'], order_by=methodSticky)
            gen = [account for account in accounts['active'] if account['canStickItem']]
            if gen != []:
                data = self.__lolzeBotApi.stickAccount(gen[0]["item_id"])
                if error := data.get('errors'):
                    self.__log(f'Не удалось закрепить https://lzt.market/{gen[0]["item_id"]}\n{error}', logLevel='info')
                    return
                self.__log(f'Закреплен https://lzt.market/{gen[0]["item_id"]}', logLevel='info')
            else:
                self.__log(f'Нечего закреплять', logLevel='info')
                self.__modules['stick']['nextRun'] = time.time() + 600
                break
         
    def __autoBuy (self, marketURLs, limitSumOfBalace=0, attemptsBuyAccount=3) -> None:
        self.__log('Автоматическая покупка запущена')
        for url in marketURLs:
            accounts = self.__lolzeBotApi.searchAcc(url=url['url'])
            self.__log(f'Аккаунтов найдено {accounts["totalItems"]} по ссылке {url["url"]}')
            for account in accounts['items']:
                buyErrorEvents = [event for event in self.__getEnevnts() if event['type'] == 'buy' and event['item_id'] == account['item_id'] and event.get('status') == 'error']
                if account['canBuyItem'] and len(buyErrorEvents) < attemptsBuyAccount:
                    balance = self.__lolzeBotApi.getInfoAboutMe()['balance']
                    if balance - account['price'] < limitSumOfBalace:
                        self.__log (f'Недостаточно средств для покупки аккаунта https://lzt.market/{account["item_id"]} \
                        \nВаш баланс: {balance}\tСтоимость аккаунта: {account["price"]}\t Ваш лимит {limitSumOfBalace}', logLevel='info')
                        continue
                    res = self.__lolzeBotApi.buyAcc(item_id=account['item_id'], price=account['price'], buyWithoutValidation=url.get('buyWithoutValidation', False))
                    if error := res.get('errors'):
                        self.__log (f'Не удалось купить аккаунт https://lzt.market/{account["item_id"]}\n{error}', logLevel='info')
                        self.__addEvent(
                            {
                                'type':'buy',
                                'item_id': account["item_id"],
                                'status': 'error',
                                'category_id': account['category_id'],
                                'marketURL': url
                            }
                        )
                        continue
                    self.__log (f'Автобай купил аккаунт https://lzt.market/{account["item_id"]}', logLevel='info')
                    self.__addEvent(
                        {
                            'type':'buy',
                            'item_id': account["item_id"],
                            'status': 'success',
                            'category_id': account['category_id'],
                            'marketURL': url
                        }
                    )
                    break
                else:
                    self.__log (f'Автобай нашел аккаунт, но не смог его купить https://lzt.market/{account["item_id"]}')
    
    def __autoSell(self, percent):
        self.__log('Автоматическая продажа запущена')
        events = self.__getEnevnts()
        reSellEventsItemID = [event['item_id'] for event in events if event['type']=='reSell']
        buyEvents = [event for event in events if event['type']=='buy' and event.get('status')=='success' and event['item_id'] not in reSellEventsItemID]
        title = ''
        title_en = ''
        price = -1
        for buyEvent in buyEvents:
            if buyEvent['marketURL'].get('autoSellOptions', {}) != {}:
                if buyEvent['marketURL']['autoSellOptions']['enabled']:
                    percent = buyEvent['marketURL']['autoSellOptions'].get('percent', percent)
                    if buyEvent['marketURL']['autoSellOptions'].get('template'):
                        path = self.__templatesFolderPath / buyEvent['marketURL']['autoSellOptions']['template']
                        with open(path) as templateFile:
                            templateData = Template(templateFile.read())
                        item = self.__lolzeBotApi.sendRequest(f'{buyEvent["item_id"]}')['item']
                        additionalVars = {}
                        additionalVarsFolderPath = Path(self.__templatesFolderPath) / 'additionalVars'
                        additionalVarsFiles = Path(additionalVarsFolderPath).glob('*')
                        files = [x for x in additionalVarsFiles if x.is_file()]
                        for file in files:
                            with open (file, 'r') as f:
                                additionalVars.update(json.load(f))
                        jsonTemplate = templateData.render(item=item, additionalVars=additionalVars).encode('utf-8')
                        jsonTemplate = json.loads(jsonTemplate)
                        title = jsonTemplate.get('title')
                        title_en = jsonTemplate.get('title_en')
                        price = jsonTemplate.get('price', -1)
                else:
                    continue
            response = self.__lolzeBotApi.reSellAccount(item_id=buyEvent['item_id'], percent=percent, price=price, title=title, title_en=title_en)
            if error := response.get('errors'):
                self.__addEvent(
                    {
                        'type':'reSell',
                        'status': 'error',
                        'item_id': buyEvent["item_id"]
                    }
                )
                self.__log (f'Не удалось выставить на продажу https://lzt.market/{buyEvent["item_id"]}\n{error}', logLevel='info')
                return
            self.__log (f'Выставлен на продажу https://lzt.market/{response["item"]["item_id"]}', logLevel='info')
            self.__addEvent(
                {
                    'type':'reSell',
                    'status': 'success',
                    'item_id': buyEvent["item_id"]
                }
            )
            #Добавление тега к аккаунту
            if addTags := buyEvent['marketURL']['autoSellOptions'].get('tags', []):
                userTagsID = self.__lolzeBotApi.sendRequest("/me")['user']['tags']
                tmp = {}
                [tmp.update({userTagsID[userTagID]['title']:userTagID}) for userTagID in userTagsID]
                userTagsID = tmp
                for addTag in addTags:
                    tag_id = userTagsID.get(addTag, None)
                    if tag_id:
                        response = self.__lolzeBotApi.addTag(item_id=response["item"]["item_id"], tag_id=tag_id)
                        if error := response.get('errors'):
                            self.__log (f'Не удалось добавить тэг к аккаунту https://lzt.market/{response["item"]["item_id"]}\n{error}', logLevel='info')
                    else:
                        self.__log (f'Ну существует тега {addTag}. Данный тэг не будет добавлен к аккаунту', logLevel='info')
                 
    def __autoUpdateInfo (self, tag, periodInSeconds):
        self.__log('Автоматическое обновление информации об аккаунтах запущено')
        accounts = self.__lolzeBotApi.getOwnedAccounts(shows=['active'], limitPagesInShow=5)['active']
        tags = self.__lolzeBotApi.sendRequest("/me")['user']['tags']
        for tagID in tags:
            if tags[tagID]['title'] == tag:
                tagId = tagID
                break
        else:
            self.__log (f'Тег {tag} не существует, обновление информации об аккаунтах завершено с ошибкой', logLevel='info')
            tagId = -1
        accountsForUpdateInfo = [account for account in accounts if tagId in account['tags'] and account['canUpdateItemStats']]
        for account in accountsForUpdateInfo:
            response = self.__lolzeBotApi.sendRequest(f'{account["item_id"]}/check-account', method='POST')
            if error := response.get('errors'):
                self.__log (f'Не удалось обновить информацию https://lzt.market/{account["item_id"]}\n{error}', logLevel='info')
                continue
            self.__log (f'Обновлена информация https://lzt.market/{account["item_id"]}\n', logLevel='info')
        self.__modules['autoUpdateInfo']['nextRun'] = time.time() + periodInSeconds
        nextStart = datetime.datetime.fromtimestamp(self.__modules['autoUpdateInfo']['nextRun']).strftime('%d-%m-%Y %H:%M:%S')
        self.__log (f'Следующая обновление информации {nextStart}', logLevel='info')

    def run (self):
        while self.__status == 'running':
            try:
                if self.__loadConfig()['status'] == 'changed':
                    clients = [x.copy() for x in self.__config['lolze']['clients']]
                    clients = [client for client in  clients if client.pop('enabled', True)]
                    self.__lolzeBotApi = lolzeBotApi(clients)
                    self.telegramApi = TelegramAPI(self.__config.get('telegram')['token']) if self.__config.get('telegram')['enabled'] else ''
                for module in self.__config['modules']:
                    if self.__config['modules'][module]['enabled'] == True and self.__modules[module]['nextRun'] <= time.time():
                        params = self.__config['modules'][module]['params']
                        self.__modules[module]['run'](**params)
            except Exception as err:
                self.__log(f'Ошибка: {err}. Перезапускаюсь.', logLevel='error')
            finally:
                pass