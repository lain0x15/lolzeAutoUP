import re, jinja2
from urllib import response

def searchAcc (self, url):
    '''
        Поиск аккаунтов по ссылке.
        На вход принимает ссылку. Выдает массив найденных аккаунтов
    '''
    parse = re.search(r"https://lzt.market/([\w\-]+)/(.+)", url)
    if not parse:
        raise TypeError("Format search URL is invalid")
    category, search_params = parse.groups()
    return self.sendRequest(f'{category}/{search_params}', typeRequest='searchRequest')

def addErrorBought (self, account):
    if len(self.tmpVarsForModules['autoBuy']['boughtError']) > 2000:
        self.tmpVarsForModules['autoBuy']['boughtError'].pop(0)
    self.tmpVarsForModules['autoBuy']['boughtError'].append (
        {
            'item_id': account["item_id"]
        }
    )

def addSuccessBought (self, account):
    if len(self.tmpVarsForModules['autoBuy']['boughtSuccess']) > 2000:
        self.tmpVarsForModules['autoBuy']['boughtSuccess'].pop(0)
    self.tmpVarsForModules['autoBuy']['boughtSuccess'].append (
        {
            'item_id': account["item_id"]
        }
    )

def checkCanIbuyAcc (self, account, limitSumOfBalace, attemptsBuyAccount):
    '''
        Проверяет можно ли купить аккаунт
        Возвращает True или False
    '''
    buyErrorEvents = [event for event in self.tmpVarsForModules['autoBuy'].get('boughtError', []) if event['item_id'] == account['item_id']]
    boughtSuccessEvents = [event for event in self.tmpVarsForModules['autoBuy'].get('boughtSuccess', []) if event['item_id'] == account['item_id']]
    
    if not account['canBuyItem']:
        self.log (f'Вы не можете купить аккаунт https://lzt.market/{account["item_id"]}')
        return False

    if len(boughtSuccessEvents) != 0:
        self.log (f'Уже куплен https://lzt.market/{account["item_id"]}')
        return False

    if len(buyErrorEvents) >= attemptsBuyAccount:
        self.log (f'Слишком много неудачных попыток купить аккаунт https://lzt.market/{account["item_id"]}')
        return False

    balance = self.sendRequest('me', typeRequest='request')['user']['balance']
    if balance - account['price'] < limitSumOfBalace:
        self.log (f'Недостаточно средств для покупки аккаунта https://lzt.market/{account["item_id"]} \
        \nВаш баланс: {balance}\tСтоимость аккаунта: {account["price"]}\t Ваш лимит {limitSumOfBalace}', logLevel='info')
        return False
    return True

def buyAcc (
        self,
        item_id: int,
        price: int,
        buyWithoutValidation = False
) -> dict:
    params = {'price':price, 'buy_without_validation':1} if buyWithoutValidation else {'price':price}
    return self.sendRequest(f'{item_id}/fast-buy', params=params, method='POST', typeRequest='request')

def tagsAdd (self, tags, itemID):
    userTagsID = self.sendRequest("/me", typeRequest='request')['user']['tags']
    tmp = {}
    [tmp.update({userTagsID[userTagID]['title']:userTagID}) for userTagID in userTagsID]
    userTagsID = tmp
    for addTag in tags:
        tag_id = userTagsID.get(addTag, None)
        if tag_id:
            response = self.sendRequest(f'{itemID}/tag?tag_id={tag_id}', method='POST', typeRequest='request')
            if error := response.get('errors'):
                self.log (f'Не удалось добавить тэг к аккаунту https://lzt.market/{itemID}\n{error}', logLevel='info')
        else:
            self.log (f'Ну существует тега {addTag}. Данный тэг не будет добавлен к аккаунту', logLevel='info')

def sellAcc (self, item_id, autoSellOptions):
    for attempt in range (autoSellOptions.get('attemptsSell', 3)):
        try:
            item = self.sendRequest(f'{item_id}', typeRequest='request')['item']

            title = autoSellOptions.get('title', item['title'])
            title_en = autoSellOptions.get('title_en', item['title_en'])
            price = autoSellOptions.get('price', 99999)
            percent = autoSellOptions.get('percent', 0)/100
            tags = autoSellOptions.get('tags', [])

            title = jinja2.Template (title).render(item=item)
            title_en = jinja2.Template (title_en).render(item=item)
            price = int(jinja2.Template (str(price)).render(item=item))
            price = price + price * percent

            category_id = item['category_id']
            login = item['loginData']['login']
            password = item['loginData']['password']
            raw = item['loginData']['raw']
            currency = item['price_currency']

            has_email_login_data = 'false'
            email_login_data = ''
            email_type = 'autoreg'

            if emailLoginData := item.get('emailLoginData'):
                has_email_login_data = 'true'
                email_login_data = emailLoginData['raw']
                email_type = item['email_type']

            payload = f"-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"has_email_login_data\"\r\n\r\n{has_email_login_data}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"email_login_data\"\r\n\r\n{email_login_data}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"email_type\"\r\n\r\n{email_type}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"login\"\r\n\r\n{login}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"password\"\r\n\r\n{password}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"login_password\"\r\n\r\n{raw}\r\n-----011000010111000001101001--"

            response = self.sendRequest(
                pathData=f"item/fast-sell?title={title}&title_en={title_en}&price={price}&currency={currency}b&item_origin=resale&category_id={category_id}",
                headersRewrite={'content-type': 'multipart/form-data; boundary=---011000010111000001101001'},
                payload=payload,
                method="POST", 
                typeRequest='request'
            )

            if error := response.get('errors'):
                raise Exception(f'Ошибка выставления на продажу {error}')

            self.log (f'Выставлен на продажу https://lzt.market/{response["item"]["item_id"]}', logLevel='info')
            break
        except Exception as err:
            self.log(f'Попытка выставления на продажу #{attempt + 1} неудачная. | {err}', logLevel='info')
    else:
        raise Exception('Не удалось выставить на продажу https://lzt.market/{response["item"]["item_id"]}')
    if addTags := autoSellOptions.get('tags', []):
        tagsAdd (self, tags=addTags, itemID=response["item"]["item_id"])
    return True

def run (self, marketURLs, limitSumOfBalace=0, attemptsBuyAccount=3, buyWithoutValidation=False) -> None:
    if 'autoBuy' not in self.tmpVarsForModules:
        self.tmpVarsForModules.update ({'autoBuy':{'boughtError':[], 'boughtSuccess':[]}})
    self.log('Автоматическая покупка запущена')
    for url in marketURLs:
        accounts = searchAcc(self, url=url['url'])
        self.log(f'Аккаунтов найдено {accounts["totalItems"]} по ссылке {url["url"]}')
        for account in accounts['items']:
            if not checkCanIbuyAcc (self, account=account, limitSumOfBalace=limitSumOfBalace, attemptsBuyAccount=attemptsBuyAccount):
                addErrorBought(self, account)
                continue
            res = buyAcc(self, item_id=account['item_id'], price=account['price'], buyWithoutValidation=buyWithoutValidation)
            if error := res.get('errors'):
                self.log (f'Не удалось купить аккаунт https://lzt.market/{account["item_id"]}\n{error}', logLevel='info')
                addErrorBought(self, account)
                continue
            self.log (f'Автобай купил аккаунт https://lzt.market/{account["item_id"]}', logLevel='info')
            addSuccessBought(self, account)
            if url.get('autoSellOptions', {}).get('enabled', False):
                if sellAcc(self, item_id=account["item_id"], autoSellOptions=url['autoSellOptions']):
                    break