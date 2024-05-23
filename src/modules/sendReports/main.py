import time

def getAccounts(
    self, 
    order: str = 'price_to_down'
) -> dict:
    return self.lolzeBotApi.sendRequest(pathData='user/items', params={'order_by':order})

def run (self):
    self.log('Запущен модуль отправки репортов')
    report = ''
    profile = self.lolzeBotApi.getInfoAboutMe()
    balance = profile['balance']
    hold = profile['hold']
    accounts = getAccounts(self)
    purchasedCount = 0
    purchasedSum = 0
    paidCount = 0
    paidSum = 0
    purchasedAccounts = self.lolzeBotApi.getPurchasedAccounts(order_by='pdate_to_down')
    for purchasedAccount in purchasedAccounts:
        a = self.lolzeBotApi.getAccountInformation(purchasedAccount["item_id"])
        if (time.time() - a['buyer']['operation_date']) <= 24 * 60 * 60:
            purchasedCount += 1
            purchasedSum += a['price']
        else:
            break
    else:
        purchasedCount = -1
    paidAccounts = self.lolzeBotApi.getOwnedAccounts (shows=['paid'], order_by='pdate_to_down')['paid']
    for paidAccount in paidAccounts:
        a = self.lolzeBotApi.getAccountInformation(paidAccount["item_id"])
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
    report += f'Куплено за 24 часа: {purchasedCount} на сумму {purchasedSum}\n'
    report += f'Продано за 24 часа: {paidCount} на сумму {paidSum}'
    self.log(report, logLevel='info')
    return time.time() + 3600