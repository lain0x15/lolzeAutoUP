import json, asyncio
from src.lolzeAutoUP import lolzeAutoUP

class config:
    def __init__(self, configFilePath='config.json'):
        self.configJson = json.loads('{}')
        self.configFilePath = configFilePath
        
    def loadConfig(self):
        with open(self.configFilePath) as configFile:
            configJsonTemp = json.load(configFile)
        if sorted(configJsonTemp.items()) != sorted(self.configJson.items()):
            self.configJson = configJsonTemp
            return {'status': 'changed'}
        return {'status': 'ok'}

    async def watchLoadConfig (self, func=None, **kwargs):
        while True:
            if self.loadConfig()['status'] == 'changed':
                if func != None:
                    func(**kwargs)
            await asyncio.sleep(20)
    
    def getJson (self):
        return self.configJson

async def run():
    while True:
        lolzeAutoUpConfig = config()
        lolzeAutoUpConfig.loadConfig()
        lolzeAutoUpConfigJson = lolzeAutoUpConfig.getJson()
        token = lolzeAutoUpConfigJson['lolze']['token']
        bot = lolzeAutoUP (token = lolzeAutoUpConfigJson['lolze']['token'],
            methodBump = int(lolzeAutoUpConfigJson['lolze']['METHODBUMP']), 
            methodSticky = int(lolzeAutoUpConfigJson['lolze']['METHODSTICKY']),
            telegramToken = lolzeAutoUpConfigJson['telegram']['token'],
            telegramUserIDs = lolzeAutoUpConfigJson['telegram']['userIDs'],
            urls = lolzeAutoUpConfigJson['lolze']['marketURLs'],
            limitSumOfBalace = int(lolzeAutoUpConfigJson['lolze']['limitSumOfBalace']),
            botName = lolzeAutoUpConfigJson['lolzeAutoUP']['botName'],
            sendReports = True if int(lolzeAutoUpConfigJson['lolze']['sendReports']) == 1 else False
        )
        tasks = [lolzeAutoUpConfig.watchLoadConfig(func=bot.setStatus, status='stop'), bot.run()]
        tasks = list(map(asyncio.ensure_future, tasks))
        groupTask = asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        try:
            finished, unfinished = await groupTask
            for result in finished:
                if res := result.result() != 0:
                    return res
        finally:
            for task in tasks:
                task.cancel()
    
if __name__ == "__main__":
    asyncio.run(run())
