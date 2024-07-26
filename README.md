﻿lolzeAutoUp - бот для маркета lzt.market имеющий функционал:
-------------------------------------------
1) Автоматического поднятия аккаунтов
2) Автоматического закрепления аккаунтов
3) Автоматической покупке/продажи
4) Обновлении информации об аккаунте
-------------------------------------------
Требования:
1) python 3.12+
2) Библиотеки requests, schema, pyyaml, Jinja2
-------------------------------------------
Быстрый старт:
1) Устанавливаем python с офф сайта https://www.python.org/downloads/
2) Выполните команду  
```python -m pip install requests schema pyyaml Jinja2```
3) Копируем пример файла конфигурации по пути documentation/config.yaml.example в корень папки бота и удаляем приписку .example
4) Добавляем токен в файл конфигурации
5) Запускаем cmd в папке с ботом  выполняем команду ```python main.py ```
Запустится бот с модулями для поднятия и закрепления аккаунтов
-------------------------------------------
[Пример конфигурационного файла](documentation/config.yaml.example)

[Описание параметров config.yaml](documentation/descriptionConfig.md)