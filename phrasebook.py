start_message = {
    "ru": "отправь мне название фильма и я найду его\n\n\
        чтобы просмотреть список доступных команд, нажми /help",
    "en": "send me a film name and I'll find it",
}
help_message = {
    "ru": """
        Ты можешь ввести название фильма, его краткое описание или перечислить основных персонажей
        и я постараюсь его найти.
        Если хочешь посмотреть фильм на английском с субтитрами, переключись на английскую версию бота

        Если не знаешь, что посмотреть, нажми /random_movie_genre"

        Доступные команды:
        /start - Запустить бота
        /help - Показать это сообщение с помощью
        /random_movie_genre - Выдать случайный фильм заданного жанра из топ-250 кинопоиска
        /history - Показать историю ваших поисков
        /stats - Показать статистику по фильмам
        /language - Поменять язык""",
    "en": """
        Type film name, its brief desccripttion or main characters and I'll try to find it.
        Available commands:
        /start - Start the bot
        /help - Show this help message
        /history - Show your search history
        /stats - Show movie stats
        /language - change language""",
}
lang_message = {"ru": "Выбран язык", "en": "Chosen language"}
watch_message = {"ru": "Смотреть", "en": "Watch"}
no_queries = {
    "ru": "пока не было ни одного запроса, попробуй ввести название какого-нибудь фильма",
    "en": "no queries found, try to find some movie",
}
lang_choose_message = {"ru": "Выбери язык", "en": "Chose language"}
film_link_not_found_message = {
    "ru": "ссылка на фильм не найдена",
    "en": "film link was not found",
}
film_not_found_message = {
    "ru": "не могу найти такой фильм",
    "en": "film was not found",
}
film_found_message = {"ru": "фильм найден!", "en": "film was found!"}
stats_message = {
    "ru": "статистика по твоим запросам\n",
    "en": "movie request stats\n",
}
history_message = {"ru": "твои последние запросы", "en": "your last requests"}


def history_message_2(timestamp, query, movie_name):
    return {
        "ru": f"{timestamp} по запросу '{query}', был найден фильм '{movie_name}'\n",
        "en": f"{timestamp} by query '{query}', was found movie '{movie_name}'\n",
    }


def hello_message(user_name):
    return {"ru": f"привет, {user_name}!", "en": f"hi {user_name}!"}


def description(
    title_ru,
    title_en,
    year,
    rating,
    genres,
    genres_en,
    description,
    description_en,
):
    return {
        "ru": (
            f"🟡 Название: {title_ru}\n"
            f"🔴 Год: {year}\n"
            f"🟡 Рейтинг: {rating}\n"
            f"🔴 Жанры: {', '.join([genre for genre in genres])}\n"
            f"Краткое описание: {description}\n"
        ),
        "en": (
            f"🟡 Title: {title_en}\n"
            f"🔴 Year: {year}\n"
            f"🟡 Rating: {rating}\n"
            f"🔴 Genres: {', '.join([genre for genre in genres_en])}\n"
            f"Description: {description_en}\n"
        ),
    }


choose_genre_message = {
    "ru": "выбери жанр",
    "en": "choose genre"
    }

set_rating_message = {
    "ru": "Поставить оценку фильму",
    "en": "Rate this film"
    }
