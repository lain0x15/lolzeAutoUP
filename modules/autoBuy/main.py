import re

def searchAcc (
    self,
    url
) -> dict:
    parse = re.search(r"https://lzt.market/([\w\-]+)/(.+)", url)
    if not parse:
        raise TypeError("Format search URL is invalid")
    category, search_params = parse.groups()
    return self.sendRequest(f'{category}/{search_params}', typeRequest='searchRequest')

def addErrorBougth (self, account):
    self.tmpVarsForModules['autoBuy']['boughtError'].append (
        {
            'item_id': account["item_id"]
        }
    )

def addSuccessBought (self, account):
    self.tmpVarsForModules['autoBuy']['boughtSuccess'].append (
        {
            'item_id': account["item_id"]
        }
    )

def buyAcc (
        self,
        item_id: int,
        price: int,
        buyWithoutValidation = False
) -> dict:
    params = {'price':price, 'buy_without_validation':1} if buyWithoutValidation else {'price':price}
    return self.sendRequest(f'{item_id}/fast-buy', params=params, method='POST', typeRequest='request')

def run (self, marketURLs, limitSumOfBalace=0, attemptsBuyAccount=3) -> None:
    if 'autoBuy' not in self.tmpVarsForModules:
        self.tmpVarsForModules.update ({'autoBuy':{'boughtError':[], 'boughtSuccess':[]}})
    self.log('Автоматическая покупка запущена')
    for url in marketURLs:
        accounts = searchAcc(self, url=url)
        self.log(f'Аккаунтов найдено {accounts["totalItems"]} по ссылке {url}')
        for account in accounts['items']:
            buyErrorEvents = [event for event in self.tmpVarsForModules['autoBuy'].get('boughtError', []) if event['item_id'] == account['item_id']]
            boughtSuccessEvents = [event for event in self.tmpVarsForModules['autoBuy'].get('boughtSuccess', []) if event['item_id'] == account['item_id']]
            if account['canBuyItem'] and len(buyErrorEvents) < attemptsBuyAccount and len(boughtSuccessEvents) == 0:
                balance = self.sendRequest('me', typeRequest='request')['user']['balance']
                if balance - account['price'] < limitSumOfBalace:
                    self.log (f'Недостаточно средств для покупки аккаунта https://lzt.market/{account["item_id"]} \
                    \nВаш баланс: {balance}\tСтоимость аккаунта: {account["price"]}\t Ваш лимит {limitSumOfBalace}', logLevel='info')
                    addErrorBougth(self, account)
                    continue
                res = buyAcc(self,item_id=account['item_id'], price=account['price'])
                if error := res.get('errors'):
                    self.log (f'Не удалось купить аккаунт https://lzt.market/{account["item_id"]}\n{error}', logLevel='info')
                    addErrorBougth(self, account)
                    continue
                self.log (f'Автобай купил аккаунт https://lzt.market/{account["item_id"]}', logLevel='info')
                addSuccessBought(self, account)
                break
            else:
                self.log (f'Автобай нашел аккаунт, но не смог его купить https://lzt.market/{account["item_id"]}')
    return 0