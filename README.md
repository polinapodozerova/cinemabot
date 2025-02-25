# Movie Finder Bot

Этот телеграм бот, написанный с помощью `asyncio`, помогает пользователям искать информацию о фильмах, предоставляя описание, постер и ссылки на просмотр. Бот также сохраняет историю поиска и статистику по фильмам для каждого пользователя.

---

## Основные функции
Бот поддерживает выбор языка - русский или английский. По умолчанию для новых пользователей выставляется русский. При выборе английского языка ссылки будут выдаваться на сайты, где можно посмотреть фильм на английском с субтитрами.\
Пока что бот размещен на сервере от yandex cloud, бесперебойная работа обеспечена с помощью `tmux`\
Все сетевые взаимодействия выполняются асинхронно с использованием `aiohttp`

Для того чтобы найти фильм, с помощью api кинопоиска определяется его настоящее название и затем парсятся первые 7 страниц гугла по соответствующему запросу. Из найденных ссылок выбирается наиболее подходящая (есть список приоритетных сайтов и сайтов которые выдавать не надо) и выдается пользователю бота. 
Использование api кинопоиска позволяет находить фильм по запросу в свободной форме - даже по описанию фильма или перечислению основных персонажей.

Для просмотра некоторых фильмов необходимо подключение к vpn!

Также реализована команда для поиска случайного фильма с заданным жанром из топ-250 кинопоиска.

Доступные команды:
1. **Поиск фильмов**:
   - Пользователь отправляет название фильма, и бот возвращает описание, постер и ссылку на просмотр.

2. **Случайный фильм из топ-250 с заданным жанром**:
   - Пользователь выбирает жанр из 10 вариантов, и бот возвращает описание, постер и ссылку на просмотр на случайный фильм этого жанра из топ-250 кинопоиска.

3. **История поиска**:
   - Команда `/history` показывает историю поиска пользователя.

4. **Статистика по фильмам**:
   - Команда `/stats` показывает, сколько раз пользователь искал каждый фильм.

5. **Помощь**:
   - Команда `/help` выводит список доступных команд и основную информацию.

6. **Изменение языка**:
   - Команда `/language` позволяет поменять язык интерфейса и получать ссылки на фильмы в оригинале.

Для хранения информации о поисках и запросах создана небольшая база данных из четырех табличек\
Запросы к базе данных выполняются асинхронно через `aiosqlite`

**Схема базы данных**:
1. Таблица: `search_history`
- Хранит историю поиска пользователей\
user_id (INTEGER): ID пользователя\
query (TEXT): Запрос пользователя\
movie_name (TEXT): Найденное название фильма\
timestamp (DATETIME): Время поиска

2. Таблица: `movie_stats`
- Хранит статистику поиска фильмов\
user_id (INTEGER): ID пользователя\
movie_name (TEXT): Название фильма\
count (INTEGER): Количество поисков фильма\

3. Таблица: `users`
- Хранит информацию о пользователях\
user_id (INTEGER): ID пользователя\
user_lang (TEXT): Язык пользователя (по умолчанию "ru")

4. Таблица `movie_links`
- Хранит информацию и ссылки на фильмы
---


**requirements**

```aiogram==3.15.0
aiohttp==3.10.5
aiosqlite==0.20.0
beautifulsoup4==4.12.3
requests==2.32.3
translators
