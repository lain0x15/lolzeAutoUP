import re, yaml
from urllib import response
from datetime import datetime

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

def run (self, marketURLs, pagesPerUrl, save_in_file=False) -> None:
    if 'autoNotice' not in self.tmpVarsForModules:
        self.tmpVarsForModules.update ({'autoNotice':{'exclude': []}})
    self.log('Автоматическое оповещение запущено')
    for url in marketURLs:
        page = 1
        while True:
            res = []
            accounts = searchAcc(self, url=url['url'] + f'&page={page}')
            self.log(f'Аккаунтов найдено {accounts["totalItems"]} по ссылке {url["url"]}'+ f'&page={page}')
            for item in accounts['items']:
                for transaction in item.get('fortniteTransactions'):
                    if transaction['title'] in url['searchTransactionsTitle']:
                        if item["item_id"] not in self.tmpVarsForModules['autoNotice']['exclude']:
                            if len(self.tmpVarsForModules['autoNotice']['exclude']) >= 10000:
                                self.tmpVarsForModules['autoNotice']['exclude'].pop(0)
                            self.tmpVarsForModules['autoNotice']['exclude'].append(item["item_id"])
                            res.append(f'https://lzt.market/{item["item_id"]}')
                            if save_in_file:
                                try:
                                    with open(self.logFolderPath / 'autoNotice.yml', encoding='utf-8') as file:
                                        data = yaml.safe_load(file)
                                    if data == None:
                                        data = {}
                                except FileNotFoundError:
                                    data = {}
                                with open(self.logFolderPath / 'autoNotice.yml', "w", encoding='utf-8') as file:
                                    data.update({
                                        item["item_id"]:{
                                            '0_url': f'https://lzt.market/{item["item_id"]}',
                                            '1_transaction': [it['title'] for it in item.get('fortniteTransactions')],
                                            '3_add_date': datetime.now()
                                        }
                                    })
                                    yaml.dump(data, file, default_flow_style=False, allow_unicode=True)
                        break
            if res:
                self.log(f'По ссылке {url["url"]}&page={page} найдены\n{res}', logLevel='info')
            if accounts['totalItems'] <= accounts['perPage'] * page:
                break
            elif pagesPerUrl <= page:
                break
            page = page + 1