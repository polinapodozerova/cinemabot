import asyncio
import logging
import sys
import os
import random

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.filters.callback_data import CallbackData, CallbackQuery
from aiogram.types import (
    Message,
    BotCommand,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from movie_finder import (
    get_movie_info,
    MovieInfo,
    find_movie_urls,
    get_random_movie_from_top250,
)
from db_helper import (
    get_movie_stats,
    get_search_history,
    save_request_to_db,
    init_db,
    increment_movie_count,
    get_users_languages,
    change_language,
    add_user,
    get_movie_info_from_db,
    save_movie_link,
    save_rating_to_db,
)

from phrasebook import (
    start_message,
    help_message,
    lang_message,
    watch_message,
    no_queries,
    lang_choose_message,
    film_link_not_found_message,
    film_not_found_message,
    film_found_message,
    stats_message,
    history_message,
    history_message_2,
    hello_message,
    choose_genre_message,
    set_rating_message
)

load_dotenv()

STICKERS = {
    "sad_dog": "CAACAgIAAxkBAAENWONnYugUgQ4jth-SnFeC-uVvPrTnfQACHwADXQWCFuGUEHuw6WXbNgQ",
    "happy_rat": "CAACAgIAAxkBAAENWOVnYuhiwXOwqEi5M1_gfjge50mwzwAC4BwAAj06EUhEul5mn-zHqTYE",
    "it_dog": "CAACAgIAAxkBAAENWOdnYuhtTG4qflu5X9sQ4kbrKniF8QACug0AAtTaoEu7BNkHkbaXRTYE",
}
USER_LANG = get_users_languages()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


class StatsCallback(CallbackData, prefix="stats"):
    action: str


async def set_commands() -> None:
    commands = [BotCommand(command="/start"), BotCommand(command="/help")]
    await bot.set_my_commands(commands)


@dp.message(CommandStart())
async def send_welcome(message: Message) -> None:
    user_id = message.from_user.id
    logging.info(user_id)
    if user_id not in USER_LANG:
        logging.info(f"NEW USER!!!!!!!!!!!!{user_id}!!!!!!!!!!!!!")
        USER_LANG[user_id] = "ru"
        user_lang = USER_LANG[user_id]
        await add_user(user_id)
        await message.answer(
            hello_message(message.from_user.first_name)[user_lang]
        )
        await message.answer_sticker(STICKERS["happy_rat"])
    user_lang = USER_LANG[user_id]
    await message.answer(start_message[user_lang])


@dp.message(Command(commands=["help"]))
async def show_help(message: Message) -> None:
    user_id = message.from_user.id
    user_lang = USER_LANG[user_id]
    await message.answer(help_message[user_lang])


@dp.message(Command(commands=["history"]))
async def show_history(message: Message) -> None:
    """Shows the search history for the user."""
    user_id = message.from_user.id
    user_lang = USER_LANG[user_id]
    history = await get_search_history(user_id)

    if history:
        response = history_message[user_lang]
        for query, movie_name, timestamp in history:
            response += history_message_2(timestamp, query, movie_name)[
                user_lang
            ]
        await message.answer(response)
    else:
        await message.answer(no_queries[user_lang])


@dp.message(Command(commands=["stats"]))
async def show_stats(message: Message) -> None:
    """Shows movie stats for the user."""
    user_id = message.from_user.id
    user_lang = USER_LANG[user_id]
    stats = await get_movie_stats(user_id)

    if stats:
        response = stats_message[user_lang]
        for movie_name, count in stats:
            response += f"- '{movie_name}': {count}\n"
        await message.answer(response)
    else:
        await message.answer(no_queries[user_lang])


@dp.message(Command(commands=["language"]))
async def choose_language(message: Message) -> None:
    user_id = message.from_user.id
    user_lang = USER_LANG[user_id]
    keyboard = get_language_keyboard()
    await message.answer(lang_choose_message[user_lang], reply_markup=keyboard)


# Словарь жанров (название жанра -> ID жанра в API Кинопоиска)
GENRES = {
    "комедия": 1,
    "драма": 2,
    "триллер": 3,
    "фантастика": 4,
    "ужасы": 5,
    "мелодрама": 6,
    "боевик": 7,
    "детектив": 8,
    "приключения": 9,
    "аниме": 10,
}


class GenreCallback(CallbackData, prefix="genre_name"):
    genre_name: str


def get_genre_keyboard() -> InlineKeyboardMarkup:
    """
    клавиатура с кнопками для выбора жанра.
    """
    builder = InlineKeyboardBuilder()
    for genre_name in GENRES.keys():
        builder.add(
            InlineKeyboardButton(
                text=genre_name.capitalize(),
                callback_data=GenreCallback(genre_name=genre_name).pack(),
            )
        )
    builder.adjust(2)
    return builder.as_markup()


class RatingCallback(CallbackData, prefix="rating"):
    rating: int
    movie_name: str


def get_rating_keyboard(movie_name) -> InlineKeyboardMarkup:
    """
    клавиатура с кнопками для выcтавления рейтинга
    """
    builder = InlineKeyboardBuilder()
    for rating in range(1, 11):
        builder.add(
            InlineKeyboardButton(
                text=str(rating),
                callback_data=RatingCallback(rating=rating, movie_name=movie_name).pack(),
            )
        )
    builder.adjust(5)
    return builder.as_markup()

@dp.callback_query(lambda callback_query: callback_query.data.startswith("open_rating_keyboard"))
async def open_rating_keyboard(callback_query: CallbackQuery) -> None:
    movie_name = callback_query.data.split(":")[1]
    await callback_query.message.edit_reply_markup(
        reply_markup=get_rating_keyboard(movie_name)
    )
    await callback_query.answer()

@dp.callback_query(RatingCallback.filter())
async def rating_callback_handler(
    callback_query: CallbackQuery, callback_data: RatingCallback
) -> None:
    """Нажатие на кнопку выбора рейтинга"""
    user_id = callback_query.from_user.id
    user_lang = USER_LANG[user_id]
    rating = callback_data.rating
    movie_name = callback_data.movie_name
    print(movie_name, ENCODED_TITLES)

    await save_rating_to_db(user_id=user_id, movie_name=ENCODED_TITLES[int(movie_name)], rating=rating)
    await callback_query.answer(f"Вы поставили оценку {rating}!")

@dp.callback_query(GenreCallback.filter())
async def genre_callback_handler(
    callback_query: CallbackQuery, callback_data: GenreCallback
) -> None:
    """
    нажатие на кнопку жанра
    """
    user_id = callback_query.from_user.id
    user_lang = USER_LANG[user_id]
    try:
        genre_name = callback_data.genre_name
        movie = await get_random_movie_from_top250(
            genre_name=genre_name, lang=user_lang
        )

        movie_info, link, title = await process_finding(user_id=user_id, movie_name=movie.title_ru, user_lang=user_lang)
        if link:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=watch_message[user_lang],
                            url="http" + link.split("http")[1].split("&")[0],
                        ),
                        InlineKeyboardButton(
                            text=set_rating_message[user_lang],
                            callback_data=f"open_rating_keyboard:{title}",
                        ),
                    ]
                ]
            )
            await callback_query.message.answer_photo(
                photo=movie_info.poster_url,
                caption=str(movie_info),
                reply_markup=keyboard,
            )
            await callback_query.answer(film_found_message[user_lang])
        else:
            await callback_query.answer(film_link_not_found_message[user_lang])
            await callback_query.answer_sticker(STICKERS["sad_dog"])

    except Exception as e:
        logging.error(f"Error fetching random movie by genre: {e}")
        await callback_query.answer(film_not_found_message[user_lang])


async def process_finding(user_id, movie_name, user_lang):
    try:
        movie_info_from_db = await get_movie_info_from_db(
            movie_name, user_lang
        )
        logging.info("movie info found")
        if movie_info_from_db:
            logging.info("movie info found in db")
            movie_info = MovieInfo(
                movie_id=None,
                title_ru=movie_info_from_db["title_ru"],
                title_en=movie_info_from_db["title_en"],
                year=movie_info_from_db["year"],
                length=None,
                description=movie_info_from_db["description_ru"],
                description_en=movie_info_from_db["description_en"],
                genres=movie_info_from_db["genres_ru"].split(", "),
                genres_en=movie_info_from_db["genres_en"].split(", "),
                rating=movie_info_from_db["rating"],
                poster_url=None,
                lang=user_lang,
            )
            movie_true_name = movie_info_from_db["title_ru"]
            link = movie_info_from_db["link"]
        else:
            logging.info("movie info not found in db")
            movie_info: MovieInfo = await get_movie_info(movie_name, user_lang)
            movie_true_name = (
                movie_info.title_ru
                if user_lang == "ru"
                else movie_info.title_en
            )
            logging.info("started looking for link")
            link = await find_movie_urls(movie_name=movie_true_name, top=1)
            logging.info("finished looking for link")

        await save_request_to_db(
            user_id=user_id, query=movie_name, movie_name=movie_true_name
        )
        await increment_movie_count(
            user_id=user_id, movie_name=movie_true_name
        )

        if link:
            await save_movie_link(
                movie_name=movie_info.title_ru,
                link=link,
                title_ru=movie_info.title_ru,
                title_en=movie_info.title_en,
                description_ru=movie_info.description,
                description_en=movie_info.description_en,
                genres_ru=", ".join(movie_info.genres),
                genres_en=", ".join(movie_info.genres_en),
                rating=movie_info.rating,
                year=movie_info.year,
            )
        return movie_info, link, movie_info.title_ru if user_lang == "ru" else movie_info.title_en
    except Exception as e:
        return e


@dp.message(Command(commands=["random_movie_genre"]))
async def random_movie_genre_command(message: Message) -> None:
    user_id = message.from_user.id
    user_lang = USER_LANG[user_id]
    await message.answer(
        reply_markup=get_genre_keyboard(), text=choose_genre_message[user_lang]
    )

ENCODED_TITLES = {}
@dp.message()
async def provide_links_and_description(message: Message) -> None:
    """Handles all text messages (movie name requests)"""
    user_id = message.from_user.id
    user_lang = USER_LANG[user_id]
    movie_name = message.text
    logging.info(f"user {user_id} wanted to find {message.text}")

    try:
        movie_info, link, title = await process_finding(user_id=user_id, movie_name=movie_name, user_lang=user_lang)
        title_num = random.randint(1, 1000000000)
        ENCODED_TITLES[title_num] = title
        print(ENCODED_TITLES)
        if link:
            logging.info(f"link found {link}")
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=watch_message[user_lang],
                            url="http" + link.split("http")[1].split("&")[0],
                        ),
                        InlineKeyboardButton(
                            text=set_rating_message[user_lang],
                            callback_data=f"open_rating_keyboard:{title_num}",
                        ),
                    ]
                ]
            )
            await message.answer_photo(
                photo=movie_info.poster_url,
                caption=str(movie_info),
                reply_markup=keyboard,
            )
        else:
            logging.info(f"link not found {title}")
            await message.answer_photo(
                photo=movie_info.poster_url, caption=str(movie_info)
            )
            await message.answer(film_link_not_found_message[user_lang])
            await message.answer_sticker(STICKERS["sad_dog"])
    except Exception as e:
        logging.error(f"Error processing movie request: {e}")
        await message.answer(film_not_found_message[user_lang])
        await message.answer_sticker(STICKERS["sad_dog"])


class LanguageCallback(CallbackData, prefix="lang"):
    language: str


def get_language_keyboard() -> InlineKeyboardMarkup:
    """клавиатура с кнопками для выбора языка."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Русский",
            callback_data=LanguageCallback(language="ru").pack(),
        ),
        InlineKeyboardButton(
            text="English",
            callback_data=LanguageCallback(language="en").pack(),
        ),
    )
    return builder.as_markup()


@dp.callback_query(LanguageCallback.filter())
async def language_callback_handler(
    callback_query: CallbackQuery, callback_data: LanguageCallback
) -> None:
    """нажатие на кнопку выбора языка."""
    user_id = callback_query.from_user.id
    language = callback_data.language
    USER_LANG[user_id] = language
    change_language(user_id, language)
    await callback_query.message.edit_text(
        lang_message[language] + f" {language}"
    )
    await callback_query.answer()


async def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await init_db()
    try:
        await dp.start_polling(bot, skip_updates=True, on_startup=set_commands)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
