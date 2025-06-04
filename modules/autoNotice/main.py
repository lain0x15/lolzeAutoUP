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

def run (self, marketURLs) -> None:
    self.log('Автоматическое оповещение запущено')
    res = []
    for url in marketURLs:
        accounts = searchAcc(self, url=url['url'])
        self.log(f'Аккаунтов найдено {accounts["totalItems"]} по ссылке {url["url"]}')
        for item in accounts['items']:
            for transaction in item.get('fortniteTransactions'):
                if transaction['title'] in url['searchTransactionsTitle']:
                    res.append(f'https://lzt.market/{item["item_id"]}')
    self.log(res, logLevel='info')