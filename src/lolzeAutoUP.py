import requests, asyncio, datetime, time, re, pprint, hashlib
import os
from .telegramAPI import TelegramAPI
from .lolzeBotApi import lolzeBotApi
import logging

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

class lolzeAutoUP(lolzeBotApi):
    def __init__(
        self, 
        token: str,
        methodBump: int,
        methodSticky: int,
        telegramToken: int,
        telegramUserIDs: int,
        urls: str, 
        limitSumOfBalace: int,
        proxies: dict = {},
        botName: str = '',
        sendReports: bool = False
    ) -> None:
        super().__init__(token)
        self.status = 'started'
        self.botName = botName
        self.METHODBUMP = self.getOrderByNumber(methodBump)
        self.METHODSTICKY = self.getOrderByNumber(methodSticky)
        self.sendReports = sendReports
        self.telegramTOKEN = telegramToken
        self.telegramUserID = telegramUserIDs
        self.telegramApi = TelegramAPI(self.telegramTOKEN) if self.telegramTOKEN != '' else None
        self.autoBuyUrls = urls
        self.limitSumOfBalace = limitSumOfBalace
        logging.basicConfig(filename='msg.log', filemode='a+', format='%(asctime)s\n%(message)s')

    async def __sendReport (self):
        while True:
            report = ''
            profile = self.getInfoAboutMe()
            balance = profile['balance']
            hold = profile['hold']
            accounts = self.getAccounts()
            linksCount = len(self.autoBuyUrls)
            purchasedCount = 0
            purchasedSum = 0
            paidCount = 0
            paidSum = 0
            purchasedAccounts = self.getPurchasedAccounts(order_by='pdate_to_down')
            for purchasedAccount in purchasedAccounts:
                a = self.getAccountInformation(purchasedAccount["item_id"])
                if (time.time() - a['buyer']['operation_date']) <= 24 * 60 * 60:
                    purchasedCount += 1
                    purchasedSum += a['price']
                else:
                    break
            else:
                purchasedCount = -1
            paidAccounts = self.getOwnedAccounts (shows=['paid'], order_by='pdate_to_down')['paid']
            for paidAccount in paidAccounts:
                a = self.getAccountInformation(paidAccount["item_id"])
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
            self.log(report)
            await asyncio.sleep(3600)
    
    def getAccounts(
        self, 
        order: str = 'price_to_down'
    ) -> dict:
        return self.sendRequest(pathData='user/items', params={'order_by':order})
    
    def sendTelegramMessage (
        self, 
        message: str
    ) -> None:
        try:
            if self.telegramApi is None:
                return
            for telegramID in self.telegramUserID:
                self.telegramApi.send_message(message, telegramID)
        except Exception as err:
            pass
    
    def log (
        self, 
        message: str
    ) -> None:
        message = message if self.botName == '' else f'{self.botName}:\n{message}'
        logging.warning(message)
        print (message)
        self.sendTelegramMessage(message)
    
    def getLastBumps (
        self, 
        count: int
    ) -> list:
        lastBumps = [0 for _ in range(count)]
        accounts = self.getOwnedAccounts(order_by='pdate_to_down')
        for accountShowType in accounts:
            for account in accounts[accountShowType][:count]:
                if account['published_date'] != account['refreshed_date']:
                    lastBumps.append(account['refreshed_date'])
                    lastBumps.sort(reverse=True)
                    if len(lastBumps) > count:
                        lastBumps.pop()
        return lastBumps
 
    async def __bump (self) -> None:
        self.log('Поднятие аккаунтов запущено')
        while True:
            marketPermissions = self.getMarketPermissions()
            if marketPermissions['hasAccessToMarket'] != True:
                raise Exception ('Нет доступа к маркету')
            if marketPermissions['canBumpOwnItem'] != True:
                raise Exception ('Нет прав на поднятия аккаунтов')
            countAvailableBumps = 0
            lastBumps = self.getLastBumps(marketPermissions['bumpItemCountInPeriod'])
            for lastBump in lastBumps:
                if time.time() - lastBump >= marketPermissions['bumpItemPeriod'] * 60 * 60:
                    countAvailableBumps += 1
            if countAvailableBumps <= 0:
                nextBumpDate = lastBumps.pop() + marketPermissions['bumpItemPeriod'] * 60 * 60
                sleepTime = nextBumpDate - time.time()
                nextBumpDate = datetime.datetime.fromtimestamp(nextBumpDate).strftime('%d-%m-%Y %H:%M:%S')
                self.log (f'Осталось поднятий: {countAvailableBumps}\nДата следующей попытки поднятия: {nextBumpDate}')
                sleepTime = sleepTime if sleepTime > 0 else 0
                await asyncio.sleep(sleepTime)
                continue
            accounts = self.getAccounts(order=self.METHODBUMP)
            for account in accounts['items']:
                if time.time() - account['refreshed_date'] > marketPermissions['bumpItemPeriod'] * 60 * 60:
                    pathData = f'{account["item_id"]}/bump'
                    response = self.sendRequest(pathData=pathData, method='POST')
                    if error := response.get('errors'):
                        self.log(f'Не удалось поднять аккаунт https://lzt.market/{account["item_id"]}\n{error}')
                        continue
                    self.log(f'Поднят аккаунт https://lzt.market/{account["item_id"]}')
                    if (countAvailableBumps := countAvailableBumps - 1) <= 0:
                        break
            else:
                nextBumpDate = datetime.datetime.fromtimestamp(3600 + time.time() ).strftime('%d-%m-%Y %H:%M:%S')
                self.log (f'Осталось поднятий: {countAvailableBumps}\nНет аккаунтов для поднятия. Следующая попытка поднятия {nextBumpDate}')
                await asyncio.sleep(3600)
     
    def getOrderByNumber (
        self, 
        number: int
    ) -> str:
        if number == 1:
            return 'price_to_up'
        elif number == 2:
            return 'price_to_down'
        elif number == 3:
            return 'pdate_to_up'
        else:
            return None
    
    async def __sticky(self) -> None:
        self.log('Закреплениие аккаунтов запущено')
        while True:
            accounts = self.getOwnedAccounts(shows=['active'], order_by=self.METHODSTICKY)
            gen = [account for account in accounts['active'] if account['canStickItem']]
            if gen != []:
                data = self.stickAccount(gen[0]["item_id"])
                if error := data.get('errors'):
                    self.log(f'Не удалось закрепить https://lzt.market/{gen[0]["item_id"]}\n{error}')
                    await asyncio.sleep(20)
                    continue
                self.log(f'Закреплен https://lzt.market/{gen[0]["item_id"]}')
            else:
                self.log(f'Нечего закреплять')
                await asyncio.sleep(600)
         
    async def __autoBuy (self) -> None:
        def parse_search_data (search_url: str):
            parse = re.search(r"https://lzt.market/([\w\-]+)/(.+)", search_url)
            if not parse:
                raise TypeError("Format search URL is invalid")
            category, search_params = parse.groups()
            return category, search_params
        self.log('Автоматическая покупка запущена')
        while True:
            for url in self.autoBuyUrls:
                category, search_params = parse_search_data(url['url'])
                accounts = self.sendRequest(f'{category}/{search_params}')
                for account in accounts['items']:
                    if account['canBuyItem']:
                        response = self.sendRequest(f'{account["item_id"]}/reserve', params={'price':account['price']}, method='POST')
                        if error := response.get('errors'):
                            self.log (f'Не удалось зарезервировать аккаунт https://lzt.market/{account["item_id"]}\n{error}')
                            continue
                        else:
                            self.log (f'Автобай зарезервировал аккаунт https://lzt.market/{account["item_id"]}')
                        balance = self.getInfoAboutMe()['balance']
                        if balance <= self.limitSumOfBalace:
                            self.log (f'Недостаточно средств для покупки аккаунта https://lzt.market/{account["item_id"]} \
                            \nВаш баланс: {balance}\tСтоимость аккаунта: {account["price"]}\t Ваш лимит {self.limitSumOfBalace}')
                            continue
                        res = self.sendRequest(f'{account["item_id"]}/fast-buy', params={'price':account['price']}, method='POST')
                        if error := res.get('errors'):
                            self.log (f'Не удалось купить аккаунт https://lzt.market/{account["item_id"]}\n{error}')
                            continue
                        self.log (f'Автобай купил аккаунт https://lzt.market/{account["item_id"]}')
                        break
                    else:
                        self.log (f'Автобай нашел аккаунт, но не смог его купить https://lzt.market/{account["item_id"]}')
            await asyncio.sleep(0)
    
    async def __controllerStatus (self) -> None:
        while True:
            if self.status == 'started':
                pass
            elif self.status == 'stop':
                raise lolzeAutoUpErrorStop(f'Остановка бота. Задан статус боту {self.status}')
            await asyncio.sleep(20)
    
    def setStatus (self, status):
        self.status = status
    
    async def run (self):
        while True:
            try:
                self.log('Бот запущен')
                if self.status == 'stop':
                    raise lolzeAutoUpErrorStop(f'Остановка бота. Задан статус боту {self.status}')
                tasks = []
                tasks.append(self.__controllerStatus())
                if self.sendReports == True:
                    tasks.append(self.__sendReport())
                if self.METHODBUMP is not None:
                    tasks.append(self.__bump())
                if self.METHODSTICKY is not None:
                    tasks.append(self.__sticky())
                if self.autoBuyUrls != []:
                    tasks.append(self.__autoBuy())
                tasks = list(map(asyncio.ensure_future, tasks))
                groupTask = asyncio.gather(*tasks)
                await groupTask
            except requests.exceptions.ConnectionError:
                self.log('Ошибка соединения с сайтом')
            except lolzeAutoUpErrorStop as err:
                self.log(f'Ошибка: {err}')
                return 0
            except Exception as err:
                self.log(f'Ошибка: {err}')
            finally:
                self.log('Завершение работы бота')
                for task in tasks:
                    task.cancel()
                await asyncio.sleep(5)
