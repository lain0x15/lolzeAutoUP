import time

def run (self, methodSticky: str) -> int:
    '''
        Закрепляет аккунты
        methodSticky - метод по которому будут выбираться аккаунты для закрепления
            доступные значения "price_to_up" - сначало дешёвые, "price_to_down" - сначало дорогие, "pdate_to_up" - Старые (по заливу)
    '''
    if 'stick' not in self.tmpVarsForModules:
        self.tmpVarsForModules.update ({'stick':{}})
    if self.tmpVarsForModules['stick'].get('nextRun', 0) <= time.time():
        self.log('Закреплениие аккаунтов запущено')
        while True:
            accounts = self.sendRequest(f'user//items?page=1&show=active&order_by={methodSticky}', typeRequest='request')['items']
            gen = [account for account in accounts if account['canStickItem']]
            if gen != []:
                data = self.sendRequest(f'{gen[0]["item_id"]}/stick', typeRequest='request', method='POST')
                if error := data.get('errors'):
                    self.log(f'Не удалось закрепить https://lzt.market/{gen[0]["item_id"]}\n{error}', logLevel='info')
                    return 0
                self.log(f'Закреплен https://lzt.market/{gen[0]["item_id"]}', logLevel='info')
            else:
                self.log(f'Нечего закреплять', logLevel='info')
                break
        self.tmpVarsForModules['stick'].update ({'nextRun': time.time() + 600})