import time
import datetime

def run (self, tag, periodInSeconds):
    if 'autoUpdateInfo' not in self.tmpVarsForModules:
        self.tmpVarsForModules.update ({'autoUpdateInfo':{}})
    if self.tmpVarsForModules['autoUpdateInfo'].get('nextRun', 0) <= time.time():
        self.log('Автоматическое обновление информации об аккаунтах запущено')
        accounts = self.sendRequest(f'user//items?page=1&show=active', typeRequest='request')['items']
        tags = self.sendRequest("/me", typeRequest='request')['user']['tags']
        for tagID in tags:
            if tags[tagID]['title'] == tag:
                tagId = tagID
                break
        else:
            self.log (f'Тег {tag} не существует, обновление информации об аккаунтах завершено с ошибкой', logLevel='error')
            tagId = -1
        accountsForUpdateInfo = [account for account in accounts if tagId in account['tags'] and account['canUpdateItemStats']]
        for account in accountsForUpdateInfo:
            response = self.sendRequest(f'{account["item_id"]}/check-account', method='POST', typeRequest='request')
            if error := response.get('errors'):
                self.log (f'Не удалось обновить информацию https://lzt.market/{account["item_id"]}\n{error}', logLevel='info')
                continue
            self.log (f'Обновлена информация https://lzt.market/{account["item_id"]}\n', logLevel='info')
        nextRun = time.time() + periodInSeconds
        nextStart = datetime.datetime.fromtimestamp(nextRun).strftime('%d-%m-%Y %H:%M:%S')
        self.log (f'Следующая обновление информации {nextStart}', logLevel='info')
        self.tmpVarsForModules['autoUpdateInfo'].update ({'nextRun': nextRun})