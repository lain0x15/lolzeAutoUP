```
---
debug: false        | Запуск бота в режиме тестирования | возможные параметры true/false
lolze:
  token: eyAAAAAAAAAAAASSSSSSSSSSSSSSSSSSSSS.eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeasdasdasdas.saaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaASDASD   | Токен от lzt.market
  proxy: {}         | Прокси | Пример заполнения {'https': 'proxy.example:3128', 'http': 'proxy.example:3128'}
  baseURLmarket: https://api.lzt.market/    | URL для api lzt.market
  rateLimit:
    request: 0.5        | Задержка между запросами в секундах
    searchRequest: 3    | Задержка между запросами поиска аккаунтов для покупки в секундах
logs:
  terminalLevels: | Уровни логирования для вывода в командную строку | Возможные значения info, debug, error
  - info
  - debug
  - error  
  telegramLevels: | Уровни логирования для отправки в telegram | Возможные значения info, debug, error
  - info
  - error
modules:
  bump:           | Модуль поднятия аккаунтов в поиске
    enabled: true | Включить/выключить модуль | Возможные значения true/false
    params:
      methodBump: pdate_to_up | Определяет каким способом поднимать аккаунты | доступные значения "price_to_up" - сначало дешёвые, "price_to_down" - сначало дорогие, "pdate_to_up" - Старые (по заливу)
  stick:          | Модуль закрепления аккаунтов
    enabled: true | Включить/выключить модуль | Возможные значения true/false
    params:
      methodSticky: price_to_down | Определяет каким способом закреплять аккаунты | доступные значения "price_to_up" - сначало дешёвые, "price_to_down" - сначало дорогие, "pdate_to_up" - Старые (по заливу)
  autoUpdateInfo:  | Модуль обновления информации об аккаунтах
    enabled: false | Включить/выключить модуль | Возможные значения true/false
    params:
      tag: autoUpdateInfo | Тэг фильтр. Поднимает аккаунты только с данных тэгом
      periodInSeconds: 3600 | Задержка между поднятиями в секундах
  autoBuy: | 
    enabled: false | Включить/выключить модуль | Возможные значения true/false
    params:
      limitSumOfBalace: 0      | Лимит по балансу. Не покупает аккаунты если ваш баланс ниже заданного
      attemptsBuyAccount: 3    | Кол-во попыток купить аккаунт в случае неудач
      marketURLs:
      - url: https://lzt.market/valorant/?pmax=5  | ссылка для покупки | минимальный набор для работы модуля
      - url: https://lzt.market/valorant/?pmax=10 | ссылка для покупки
        buyWithoutValidation: false | Покупать без валидации | Доступные значения true/false | true - покупка без валидации, false - перед покупкой проверять валидность аккаунта (по умолчанию)
        autoSellOptions:            | Параметры модуля продажи
          enabled: true             | Включить продажу | Доступные значения true/false
          title: valorant           | Загаловок который будет при выставлении на продажу
          title_en: valorant        | Загаловок на англ. который будет при выставлении на продажу
          price: 5                  | Цена за которую выставить
          percent: 20               | Проценты которые прибавить к конечной цене
          attemptsSell: 4           | Кол-во попыток продать аккаунт
          tags:                     | Теги которые добавить к выставленному на продажу аккаунту (теги должны быть созданы заранее)
          - autoUpdateInfo
```