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
    for url in marketURLs:
        accounts = searchAcc(self, url=url['url'])
        for acc in range(11):
            print(acc)
        self.log(f'Аккаунтов найдено {accounts["totalItems"]} по ссылке {url["url"]}')