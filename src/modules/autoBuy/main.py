def run (self, marketURLs, limitSumOfBalace=0, attemptsBuyAccount=3) -> None:
    self.log('Автоматическая покупка запущена')
    for url in marketURLs:
        accounts = self.lolzeBotApi.searchAcc(url=url['url'])
        self.log(f'Аккаунтов найдено {accounts["totalItems"]} по ссылке {url["url"]}')
        for account in accounts['items']:
            buyErrorEvents = [event for event in self.getEvents() if event['type'] == 'buy' and event['item_id'] == account['item_id'] and event.get('status') == 'error']
            if account['canBuyItem'] and len(buyErrorEvents) < attemptsBuyAccount:
                balance = self.lolzeBotApi.getInfoAboutMe()['balance']
                if balance - account['price'] < limitSumOfBalace:
                    self.log (f'Недостаточно средств для покупки аккаунта https://lzt.market/{account["item_id"]} \
                    \nВаш баланс: {balance}\tСтоимость аккаунта: {account["price"]}\t Ваш лимит {limitSumOfBalace}', logLevel='info')
                    continue
                res = self.lolzeBotApi.buyAcc(item_id=account['item_id'], price=account['price'], buyWithoutValidation=url.get('buyWithoutValidation', False))
                if error := res.get('errors'):
                    self.log (f'Не удалось купить аккаунт https://lzt.market/{account["item_id"]}\n{error}', logLevel='info')
                    self.addEvent(
                        {
                            'type':'buy',
                            'item_id': account["item_id"],
                            'status': 'error',
                            'category_id': account['category_id'],
                            'marketURL': url
                        }
                    )
                    continue
                self.log (f'Автобай купил аккаунт https://lzt.market/{account["item_id"]}', logLevel='info')
                self.addEvent(
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
                self.log (f'Автобай нашел аккаунт, но не смог его купить https://lzt.market/{account["item_id"]}')
    return 0