import time, datetime

def getLastBumps (
    self, 
    count: int
) -> list:
    lastBumps = [0 for _ in range(count)]
    accounts = self.lolzeBotApi.getOwnedAccounts(order_by='pdate_to_down')
    for accountShowType in accounts:
        for account in accounts[accountShowType]:
            if account['published_date'] != account['refreshed_date']:
                lastBumps.append(account['refreshed_date'])
                lastBumps.sort(reverse=True)
                if len(lastBumps) > count:
                    lastBumps.pop()
    return lastBumps
 
def run (self, methodBump) -> None:
    self.log('Поднятие аккаунтов запущено')
    self.log('Проверяю разрешения на маркет')
    marketPermissions = self.lolzeBotApi.getMarketPermissions()
    if marketPermissions['hasAccessToMarket'] != True or marketPermissions['canBumpOwnItem'] != True:
        raise Exception ('Нет доступа к маркету или Нет прав на поднятия аккаунтов')
    else:
        self.log('Права на поднятие аккаунтов присутствуют')

    countAvailableBumps = 0
    lastBumps = getLastBumps(self, marketPermissions['bumpItemCountInPeriod'])
    for lastBump in lastBumps:
        if time.time() - lastBump >= marketPermissions['bumpItemPeriod'] * 60 * 60:
            countAvailableBumps += 1
    if countAvailableBumps <= 0:
        nextBumpDate = lastBumps.pop() + marketPermissions['bumpItemPeriod'] * 60 * 60
        sleepTime = nextBumpDate - time.time()
        nextBumpDate = datetime.datetime.fromtimestamp(nextBumpDate).strftime('%d-%m-%Y %H:%M:%S')
        self.log (f'Осталось поднятий: {countAvailableBumps}\nДата следующей попытки поднятия: {nextBumpDate}', logLevel='info')
        sleepTime = sleepTime if sleepTime > 0 else 0
        return time.time() + sleepTime

    accounts = self.lolzeBotApi.getOwnedAccounts(shows=['active'], order_by=methodBump)['active']
    for account in accounts:
        if time.time() - account['refreshed_date'] > marketPermissions['bumpItemPeriod'] * 60 * 60:
            response = self.lolzeBotApi.bumpAccount(item_id = account["item_id"])
            if error := response.get('errors'):
                self.log(f'Не удалось поднять аккаунт https://lzt.market/{account["item_id"]}\n{error}', logLevel='info')
                continue
            self.log(f'Поднят аккаунт https://lzt.market/{account["item_id"]}', logLevel='info')
            if (countAvailableBumps := countAvailableBumps - 1) <= 0:
                break
    else:
        nextBumpDate = datetime.datetime.fromtimestamp(3600 + time.time() ).strftime('%d-%m-%Y %H:%M:%S')
        self.log (f'Осталось поднятий: {countAvailableBumps}\nНет аккаунтов для поднятия. Следующая попытка поднятия {nextBumpDate}', logLevel='info')
        return time.time() + 3600