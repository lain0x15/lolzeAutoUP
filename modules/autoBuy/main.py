import re, jinja2
from urllib import response

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

def run (self, marketURLs, limitSumOfBalace=0, attemptsBuyAccount=3) -> None:
    if 'autoBuy' not in self.tmpVarsForModules:
        self.tmpVarsForModules.update ({'autoBuy':{'boughtError':[], 'boughtSuccess':[]}})
    self.log('Автоматическая покупка запущена')
    for url in marketURLs:
        accounts = searchAcc(self, url=url['url'])
        self.log(f'Аккаунтов найдено {accounts["totalItems"]} по ссылке {url["url"]}')
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
                
                if url.get('autoSellOptions', {}).get('enabled', False):
                    for attempt in range (url['autoSellOptions'].get('attemptsSell', 3)):
                        try:
                            item = self.sendRequest(f'{account["item_id"]}', typeRequest='request')['item']
                            
                            title = url['autoSellOptions'].get('title', item['title'])
                            title_en = url['autoSellOptions'].get('title_en', item['title_en'])
                            price = url['autoSellOptions'].get('price', 99999)
                            percent = url['autoSellOptions'].get('percent', 0)/100
                            tags = url['autoSellOptions'].get('tags', [])
                            
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

                    if addTags := url['autoSellOptions'].get('tags', []):
                        tagsAdd (self, tags=addTags, itemID=response["item"]["item_id"])
            else:
                self.log (f'Автобай нашел аккаунт, но не смог его купить https://lzt.market/{account["item_id"]}')
    return 0