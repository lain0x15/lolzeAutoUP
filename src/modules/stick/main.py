import time

def run (self, methodSticky: str) -> int:
    '''
        Закрепляет аккунты
        self - класс lolzeAutoUP
        methodSticky - метод по которому будут выбираться аккаунты для закрепления
            доступные значения "price_to_up" - сначало дешёвые, "price_to_down" - сначало дорогие, "pdate_to_up" - Старые (по заливу)
        возвращает время в которое его следует запустить в следующий раз
    '''
    self.log('Закреплениие аккаунтов запущено')
    while True:
        accounts = self.lolzeBotApi.getOwnedAccounts(shows=['active'], order_by=methodSticky)
        gen = [account for account in accounts['active'] if account['canStickItem']]
        if gen != []:
            data = self.lolzeBotApi.stickAccount(gen[0]["item_id"])
            if error := data.get('errors'):
                self.log(f'Не удалось закрепить https://lzt.market/{gen[0]["item_id"]}\n{error}', logLevel='info')
                return 0
            self.log(f'Закреплен https://lzt.market/{gen[0]["item_id"]}', logLevel='info')
        else:
            self.log(f'Нечего закреплять', logLevel='info')
            break
    return time.time() + 600