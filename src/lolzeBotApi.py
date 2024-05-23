import requests, asyncio, time, re, pprint

class lolzeBotApiException(Exception):
    def __init__(self, typeError=None):
        if typeError == 'invalid_token':
            self.message = 'invalid lolze token'
        else:
            self.message = 'unknown lolze error'
    def __str__(self):
        return f'{self.message}'

class lolzeBotApi:
    def __init__(
        self, 
        clients: list
    ):
        self.__base_url_market = "https://api.lzt.market/"
        self.__clients = clients
    
    def sendRequest (
        self, 
        pathData: str, 
        method: str = 'GET',
        params: dict = {},
        headersRewrite = {},
        payload = ""
    ) -> dict:
        client = self.__clients.pop(0)
        try:
            lastSendRequest = client.get ('lastSendRequest', time.time())
            if (t := time.time() - lastSendRequest) < 3:
                time.sleep(3 - t)
            headers = {
                "accept": "application/json",
                "authorization": f"Bearer {client['token']}"
            }
            headers.update (headersRewrite)
            url = self.__base_url_market + pathData
            if method == 'GET':
                response = requests.get (url, params=params, headers=headers, proxies=client.get('proxy'), data="")
            elif method == 'POST':
                if payload == "":
                    response = requests.post (url, params=params, headers=headers, proxies=client.get('proxy'))
                else:
                    response = requests.post (url, params=params, headers=headers, proxies=client.get('proxy'), data=payload)
            elif method == 'DELETE':
                response = requests.delete (url, params=params, headers=headers, proxies=client.get('proxy'))
            else:
                raise Exception (f'Неправильный метод {method}, ожидается GET, POST, DELETE')
            if response.status_code == 200:
                response = response.json()
            elif response.status_code == 400:
                raise Exception(f'Сайт выдал ошибку {response.status_code}\nпри запросе к ссылке {url}\n{response.content.decode("unicode-escape")}')
            elif response.status_code == 403:
                response = response.json()
            elif response.status_code == 429:
                raise Exception(f'Слишком много запросов к api сайта. Сайт выдал ошибку {response.status_code}')
            else:
                raise Exception(f'Сайт выдал ошибку {response.status_code}')
            self.__lastSendRequest = time.time()
            if response.get('error') in ['invalid_token']:
                raise lolzeBotApiException(typeError = response['error'])
            return response
        finally:
            client.update ({'lastSendRequest':time.time()})
            self.__clients.append(client)
     
    def addTag (self, item_id, tag_id):
        return self.sendRequest(f'{item_id}/tag?tag_id={tag_id}', method='POST')
            
    def getOwnedAccounts (
        self, 
        shows: list = ['active', 'paid', 'deleted', 'awaiting'],
        limitPagesInShow: int = 1, 
        order_by: str = 'price_to_down'
    ) -> dict: 
        result = {}
        for show in shows:
            tempResult = []
            page = 1
            while True:
                if limitPagesInShow > 0 and limitPagesInShow <= page - 1:
                    break
                acconuts = self.sendRequest(f'user//items?page={page}&show={show}&order_by={order_by}')['items']
                if acconuts == []:
                    break
                page += 1
                for account in acconuts:
                    tempResult.append({'item_id':account['item_id'],
                            'item_state': account['item_state'],
                            'published_date': account['published_date'],
                            'refreshed_date': account['refreshed_date'],
                            'price': account['price'],
                            'is_sticky': account['is_sticky'],
                            'canStickItem': account['canStickItem'],
                            'canUnstickItem': account['canUnstickItem'],
                            'canUpdateItemStats': account['canUpdateItemStats'],
                            'tags': account['tags']
                        }
                    )
            result.update ({f'{show}':tempResult})
        return result
    
    def getMarketPermissions (self) -> dict:
        permissions = self.sendRequest("/me")['user']['permissions']['market']
        result = { 
            'stickItem': permissions['stickItem'],
            'bumpItemCountInPeriod': permissions['bumpItemCountInPeriod'],
            'bumpItemPeriod': permissions['bumpItemPeriod'],
            'canBumpOwnItem': permissions['canBumpOwnItem'],
            'hasAccessToMarket': permissions['hasAccessToMarket']
        }
        return result
    def reserveAcc (
            self,
            item_id: int,
            price: int
    ) -> dict:
        return self.sendRequest(f'{item_id}/reserve', params={'price':price}, method='POST')

    def buyAcc (
            self,
            item_id: int,
            price: int,
            buyWithoutValidation = False
    ) -> dict:
        params = {'price':price, 'buy_without_validation':1} if buyWithoutValidation else {'price':price}
        return self.sendRequest(f'{item_id}/fast-buy', params=params, method='POST')

    def searchAcc (
        self,
        url
    ) -> dict:
        parse = re.search(r"https://lzt.market/([\w\-]+)/(.+)", url)
        if not parse:
            raise TypeError("Format search URL is invalid")
        category, search_params = parse.groups()
        return self.sendRequest(f'{category}/{search_params}')

    def bumpAccount (
        self, 
        item_id: int
    ) -> dict:
        response = self.sendRequest(f'{item_id}/bump', method='POST')
        return response
        
    def stickAccount (
        self, 
        item_id: int
    ) -> dict:
        response = self.sendRequest(f'{item_id}/stick', method='POST')
        return response
    
    def unstickAccount (
        self, 
        item_id: int
    ) -> dict:
        response = self.sendRequest(f'{item_id}/stick', method='DELETE')
        return response

    def bumpAccount (
        self,
        item_id: int
    ) -> dict:
        return self.sendRequest(f'{item_id}/bump', method='POST')

    def getInfoAboutMe (self) -> dict:
        response = self.sendRequest('me')
        result = {
            'user_id': response['user']['user_id'],
            'balance': response['user']['balance'],
            'hold': response['user']['hold']
        }
        return result
        
    def getAccountInformation (
        self, 
        item_id: int
    ) -> dict:
        response = self.sendRequest(f'{item_id}')
        result = {
            'buyer': response['item']['buyer'],
            'price': response['item']['price'],
            'category_id': response['item']['category_id']
        }
        return result

    def getPurchasedAccounts (
            self,
            order_by: str ='pdate_to_down'
    ):
        return self.sendRequest(f'/user//orders?order_by={order_by}')['items']

    def reSellAccount (self, item_id, percent=0, price=-1, title='', title_en=''):
        iCanSellcategory_id = [13,]
        response = self.sendRequest(f'{item_id}')
        if response['item']['category_id'] not in iCanSellcategory_id:
            return {'errors':'На данный момент перепродажа данной категории не поддерживается'}
        
        title = title if title else response['item']['title']
        title_en = title_en if title_en else response['item']['title_en']
        category_id = response['item']['category_id']
        price = price if price >= 0 else response['item']['price']
        price = round (price + price * percent/100)
        login = response['item']['loginData']['login']
        password = response['item']['loginData']['password']
        raw = response['item']['loginData']['raw']
        currency = response['item']['price_currency']

        has_email_login_data = 'false'
        email_login_data = ''
        email_type = 'autoreg'
        
        if emailLoginData := response['item'].get('emailLoginData'):
            has_email_login_data = 'true'
            email_login_data = emailLoginData['raw']
            email_type = response['item']['email_type']
        
        payload = f"-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"has_email_login_data\"\r\n\r\n{has_email_login_data}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"email_login_data\"\r\n\r\n{email_login_data}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"email_type\"\r\n\r\n{email_type}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"login\"\r\n\r\n{login}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"password\"\r\n\r\n{password}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"login_password\"\r\n\r\n{raw}\r\n-----011000010111000001101001--"

        response = self.sendRequest(
                            pathData=f"item/fast-sell?title={title}&title_en={title_en}&price={price}&currency={currency}b&item_origin=resale&category_id={category_id}",
                            headersRewrite={'content-type': 'multipart/form-data; boundary=---011000010111000001101001'},
                            payload=payload,
                            method="POST"
                         )
        return response