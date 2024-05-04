lolzeAutoUp - бот для маркета lolze имеющий функционал:
-------------------------------------------
1) Автоматического поднятия аккаунтов
2) Автоматического закрепления аккаунтов
3) Автоматической покупке
4) Автоматической продажи (в разработке, на данной момент поддерживается valorant)

-------------------------------------------
Требования:

1) pyhton 3.10+
2) Библиотека requests

-------------------------------------------
Настройка:

1) Установите python с официального сайта или из microsoft store
2) Выполните команду python -m pip install requests Jinja2
3) Удалите .example у файла config.json.example
4) Заполните необходимые параметры (ниже расписано)
5) Откройте cmd в папке с ботом и выполните команду python main.py


-------------------------------------------
Файл config.json
```
{
    "lolze": {
        "clients": [
            {
                "enabled": true,
                "token":"", - токен lolze (Обязательный параметр)
                "proxy": {} - Пустое значит без прокси. Добавить прокси пример "proxy": {"https":"https://127.0.0.1:3128"} (в разработке)
            }
        ]
    },
    "telegram": {
        "enabled": false, - false не отправлять данные в телеграм, true отправлять
        "logLevel": ["info", "error"] - уровени логирования который будет отправляться в телеграм. Доступно "info", "debug"
        "token": "", - токен от бота телеграм
        "userIDs": [] - ид пользователей которым будут отправляться логи. пример [1231231231, 33333333333]
    },
    "modules": {
        "bump": {
            "enabled": false, - включить поднятие аккаунтов. false - выключено, true - включено
            "params":{
                "methodBump": "price_to_up" - доступные значения "price_to_up" - сначало дешёвые, "price_to_down" - сначало дорогие, "pdate_to_up" - Старые (по заливу)
            }
        },
        "stick": {
            "enabled": false, - включить закрепление аккаунтов. false - выключено, true - включено
            "params":{
                "methodSticky": "price_to_up" - доступные значения "price_to_up" - сначало дешёвые, "price_to_down" - сначало дорогие, "pdate_to_up" - Старые (по заливу)
            } 
        },
        "sendReports":
        {
            "enabled": true, - включить отправку репортов (информация о количесте купленных, проданных аккаунтов за 24 часа)
            "params":{} 
        },
        "autoSell":
        {
            "enabled": false, - включить автоматическую продажу
            "params": {
                "percent": 20 - процент наценки. Например цена покупки 100 при percent в 20, он выставит акк за 120
            }
        },
        "autoBuy": {
            "enabled": false, включить автоматическую покупку
            "params":{
                "limitSumOfBalace": 0, - лимит. Если ваш баланс ниже, покупать не будет
                "marketURLs": [ - ссылки для покупки
                    {
                        "url": "https://lzt.market/mihoyo/?pmax=5", - URI с фильтрами для поиска аккаунтов
                        "autoSellOptions": { - опционально
                            "enabled": true, - true/false включить/выключить автопродажу для данной ссылки (при выключенном модуле автопродажи ни на что не влияет)
                            "percent": 10, - процент за каторый будет продажа (по умолчанию берется из модуля autoSell)
                            "template": "valorant.template" - файл шаблона для формирования title/title_en
                        },
                        "autoScaleDown": { - опционально. в разработке ни на что не влияет
                            "enabled": false,
                            "percent": 1,
                            "periodInSecond": 3600
                        }
                    },
                    {
                        "url": "https://lzt.market/mihoyo/?pmax=6"
                    }
                ]
            }
        }
    }
}
```