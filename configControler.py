import json
from pprint import pprint
import requests

class telegramCFGA:
    def __init__(self, token, adminIDs, configFile):
        self.urlAPI = f'https://api.telegram.org/bot{token}/' 
        self.adminIDs = adminIDs
        self.configFile = configFile
        self.offset = 0
    
    def __sendRequest (self, url, params={}):
        response = requests.get (f'{self.urlAPI}{url}', params=params)
        if response.status_code == 200:
            return json.loads(response.content.decode())
        else:
            body = json.loads(response.content.decode())
            raise Exception (f"Запрос к методу {url} выдал не 200 код. Код {response.status_code}. body {body}")
        
    def __sendMessage (self, id, text, keyboard=[[]]):
        if keyboard == [[]]:
            keyboard = [[
                {'text': 'Вывести конфиг'},
                {'text': 'Задать конфиг'}
            ]]
        reply_markup = {
            'keyboard': keyboard,
            'resize_keyboard': True
        }
        reply_markup = json.dumps(reply_markup)
        params = {
            'chat_id': id,
            'text': text,
            'reply_markup': reply_markup
        }
        return self.__sendRequest('sendMessage', params=params)
    
    def __getConfiguration (self):
        with open(self.configFile) as configFile:
            configJson = json.load(configFile)
        return configJson
        
    def __loadConfiguration (self, jsonData):
        with open(self.configFile, 'r+') as configFile:
            configJson = json.load(configFile)
            configFile.seek(0)
            json.dump(jsonData, configFile, indent=4)
            configFile.truncate()
    
    def __getLastMessages (self):
        messages = self.__sendRequest('getUpdates', {'offset': self.offset+1})
        if messages['result']:
            for message in messages['result'][::-1]:
                if message['message']['from']['id'] in self.adminIDs:
                    message = messages['result'][-1]
                    self.offset = message['update_id']
                    return message 
        return []
    
    def commands (self, command):
        if command['message']['text'] == 'Вывести конфиг':
            keyboard = [
                [
                    {'text': 'Назад'},
                    {'text': 'Лицензионный ключ'}
                ],
                [
                    {'text': 'Основные настройки lolze'},
                    {'text': 'MarketURLs'}
                ]
            ]
            self.__sendMessage (id=command['message']['chat']['id'], text='Что именно вывести?', keyboard=keyboard)
            while True:
                if message:=self.__getLastMessages():
                    if message['message']['text'] == "Назад":
                        return 0
                    elif message['message']['text'] == "Лицензионный ключ":
                        config = self.__getConfiguration()
                        liceKey = config['lolzeAutoUP']['licenseKey']
                        self.__sendMessage (id=command['message']['chat']['id'], text=f'Лицензионный ключ: {liceKey}', keyboard=keyboard)
                    elif message['message']['text'] == "Основные настройки lolze":
                        config = self.__getConfiguration()
                        for param in config['lolze']:
                            if param == 'marketURLs':
                                continue
                            self.__sendMessage (id=command['message']['chat']['id'], text=f'{param}={config["lolze"][param]}', keyboard=keyboard)
                    elif message['message']['text'] == 'MarketURLs':
                        config = self.__getConfiguration()
                        for url in config["lolze"]['marketURLs']:
                            self.__sendMessage (id=command['message']['chat']['id'], text=f'{url}', keyboard=keyboard)
        elif command['message']['text'] == 'Задать конфиг':
            keyboard = [
                [
                    {'text': 'Назад'},
                    {'text': 'Лицензионный ключ'}
                ],
                [
                    {'text': 'Основные настройки lolze'},
                    {'text': 'MarketURLs'}
                ]
            ]
            self.__sendMessage (id=command['message']['chat']['id'], text='Что хотите задать?', keyboard=keyboard)
            while True:
                if message:=self.__getLastMessages():
                    if message['message']['text'] == "Назад":
                        return 0
                    elif message['message']['text'] == "Лицензионный ключ":
                        keyboard = [[{'text': 'Назад'}]]
                        self.__sendMessage (id=command['message']['chat']['id'], text='Введите лицензионный ключ:', keyboard=keyboard)
                        while True:
                            if res := self.__getLastMessages():
                                if res['message']['text'] == "Назад":
                                    return 0
                                else:
                                    config = self.__getConfiguration()
                                    config['lolzeAutoUP']['licenseKey'] = res['message']['text']
                                    self.__loadConfiguration (config)
                                    return 0
                    elif message['message']['text'] == "Основные настройки lolze":
                        keyboard = [[{'text': 'Назад'}]]
                        config = self.__getConfiguration()
                        row = 0
                        for con in config['lolze']:
                            if con == 'marketURLs':
                                continue
                            row += 1
                            keyboard.append ([])
                            keyboard[row].append(con)
                        self.__sendMessage (id=command['message']['chat']['id'], text='Что хотите задать:', keyboard=keyboard)
                        while True:
                            if res := self.__getLastMessages():
                                if res['message']['text'] == "Назад":
                                    return 0
                                elif res['message']['text'] in config['lolze']:
                                    keyboard = [[{'text': 'Назад'}]]
                                    param = res["message"]["text"]
                                    self.__sendMessage (id=command['message']['chat']['id'], text=f'Укажите значение для {param}', keyboard=keyboard)
                                    while True:
                                        if res := self.__getLastMessages():
                                            if res['message']['text'] == "Назад":
                                                return 0
                                            else:
                                                config = self.__getConfiguration()
                                                config['lolze'][param] = res['message']['text']
                                                self.__loadConfiguration (config)
                                                return 0
                    elif message['message']['text'] == "MarketURLs":
                        keyboard = [[{'text': 'Назад'}],[{'text':'Добавить'},{'text':'Удалить'}]]
                        self.__sendMessage (id=command['message']['chat']['id'], text=f'Что хотети?', keyboard=keyboard)
                        while True:
                            if res := self.__getLastMessages():
                                if res['message']['text'] == "Назад":
                                    return 0
                                elif res['message']['text'] == "Добавить":
                                    keyboard = [[{'text': 'Назад'}]]
                                    self.__sendMessage (id=command['message']['chat']['id'], text=f'Укажите ссылку для добавления', keyboard=keyboard)
                                    while True:
                                        if res := self.__getLastMessages():
                                            if res['message']['text'] == "Назад":
                                                return 0
                                            else:
                                                config = self.__getConfiguration()
                                                config['lolze']['marketURLs'].append ({'url': res['message']['text']})
                                                self.__loadConfiguration(config)
                                                return 0
                                elif res['message']['text'] == "Удалить":
                                    config = self.__getConfiguration()
                                    num = 1
                                    keyboard = [[{'text': 'Назад'}]]
                                    for url in config['lolze']['marketURLs']:
                                        self.__sendMessage (id=command['message']['chat']['id'], text=f'{num}_URL: {url}', keyboard=keyboard)
                                        num += 1
                                    self.__sendMessage (id=command['message']['chat']['id'], text=f'Укажите номер url которую хотите удалить', keyboard=keyboard)
                                    while True:
                                        if res := self.__getLastMessages():
                                            if res['message']['text'] == "Назад":
                                                return 0
                                            else:
                                                config['lolze']['marketURLs'].pop(num-2)
                                                self.__loadConfiguration(config)
                                                return 0
                                                
                    
    def run (self):
        for id in self.adminIDs:
            self.__sendMessage(id, 'Бот конфигурирования запущен')
        while True:
            try:
                if message := self.__getLastMessages():
                    self.commands (message)
                    self.__sendMessage (id=message['message']['chat']['id'], text='Гланове меню')
            except Exception as err:
                print(f'err')
                

test = telegramCFGA('', [], 'config.json')
res = test.run()
pprint (res)
