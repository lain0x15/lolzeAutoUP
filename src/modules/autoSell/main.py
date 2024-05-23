from jinja2 import Template
from pathlib import Path
import json

def run(self, percent, templatesFolderPath = 'files/templates'):
    self.log('Автоматическая продажа запущена')
    events = self.getEvents()
    reSellEventsItemID = [event['item_id'] for event in events if event['type']=='reSell']
    buyEvents = [event for event in events if event['type']=='buy' and event.get('status')=='success' and event['item_id'] not in reSellEventsItemID]
    title = ''
    title_en = ''
    price = -1
    templatesFolderPath = Path(templatesFolderPath)
    for buyEvent in buyEvents:
        if buyEvent['marketURL'].get('autoSellOptions', {}) != {}:
            if buyEvent['marketURL']['autoSellOptions']['enabled']:
                percent = buyEvent['marketURL']['autoSellOptions'].get('percent', percent)
                if buyEvent['marketURL']['autoSellOptions'].get('template'):
                    path = templatesFolderPath / buyEvent['marketURL']['autoSellOptions']['template']
                    with open(path, encoding='utf-8') as templateFile:
                        templateData = Template(templateFile.read())
                    item = self.lolzeBotApi.sendRequest(f'{buyEvent["item_id"]}')['item']
                    additionalVars = {}
                    additionalVarsFolderPath = Path(templatesFolderPath) / 'additionalVars'
                    additionalVarsFiles = Path(additionalVarsFolderPath).glob('*')
                    files = [x for x in additionalVarsFiles if x.is_file()]
                    for file in files:
                        with open (file, 'r', encoding='utf-8') as f:
                            additionalVars.update(json.load(f))
                    jsonTemplate = templateData.render(item=item, additionalVars=additionalVars)
                    jsonTemplate = json.loads(jsonTemplate)
                    title = jsonTemplate.get('title')
                    title_en = jsonTemplate.get('title_en')
                    price = jsonTemplate.get('price', -1)
            else:
                continue
        response = self.lolzeBotApi.reSellAccount(item_id=buyEvent['item_id'], percent=percent, price=price, title=title, title_en=title_en)
        if error := response.get('errors'):
            self.addEvent(
                {
                    'type':'reSell',
                    'status': 'error',
                    'item_id': buyEvent["item_id"]
                }
            )
            self.log (f'Не удалось выставить на продажу https://lzt.market/{buyEvent["item_id"]}\n{error}', logLevel='info')
            return 0
        self.log (f'Выставлен на продажу https://lzt.market/{response["item"]["item_id"]}', logLevel='info')
        self.addEvent(
            {
                'type':'reSell',
                'status': 'success',
                'item_id': buyEvent["item_id"]
            }
        )
        #Добавление тега к аккаунту
        if addTags := buyEvent['marketURL']['autoSellOptions'].get('tags', []):
            userTagsID = self.lolzeBotApi.sendRequest("/me")['user']['tags']
            tmp = {}
            [tmp.update({userTagsID[userTagID]['title']:userTagID}) for userTagID in userTagsID]
            userTagsID = tmp
            for addTag in addTags:
                tag_id = userTagsID.get(addTag, None)
                if tag_id:
                    response = self.lolzeBotApi.addTag(item_id=response["item"]["item_id"], tag_id=tag_id)
                    if error := response.get('errors'):
                        self.log (f'Не удалось добавить тэг к аккаунту https://lzt.market/{response["item"]["item_id"]}\n{error}', logLevel='info')
                else:
                    self.log (f'Ну существует тега {addTag}. Данный тэг не будет добавлен к аккаунту', logLevel='info')
    return 0