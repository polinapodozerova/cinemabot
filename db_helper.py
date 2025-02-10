import aiosqlite
import sqlite3
from datetime import datetime
import typing as tp
import asyncio

DATABASE_PATH = "movie.db"


async def init_db():
    """
    Инициализация базы данных и создание таблиц.
    """
    async with aiosqlite.connect(DATABASE_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS search_history (
            user_id INTEGER,
            query TEXT,
            movie_name TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
        )
        await cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS movie_stats (
            user_id INTEGER,
            movie_name TEXT,
            count INTEGER DEFAULT 0,
            rating REAL DEFAULT 7.5,
            PRIMARY KEY (user_id, movie_name)
        )
    """
        )
        await cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER,
            user_lang TEXT DEFAULT 'ru'
        )
    """
        )
        await cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS movie_links (
            movie_name TEXT PRIMARY KEY,
            link TEXT,
            title_ru TEXT,
            title_en TEXT,
            description_ru TEXT,
            description_en TEXT,
            genres_ru TEXT,
            genres_en TEXT,
            rating REAL,
            year INTEGER
        )
    """
        )
        await conn.commit()


async def save_request_to_db(
    user_id: int, query: str, movie_name: str
) -> None:
    """
    saves query to db
    """
    async with aiosqlite.connect(DATABASE_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "INSERT INTO search_history (user_id, query, movie_name) VALUES (?, ?, ?)",
            (user_id, query, movie_name),
        )
        await conn.commit()


async def save_rating_to_db(
    user_id: int, rating: int, movie_name: str
) -> None:
    """
    saves rating to db
    """
    async with aiosqlite.connect(DATABASE_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "UPDATE movie_stats SET rating = ? WHERE user_id = ? AND movie_name = ?",
            (rating, user_id, movie_name),
        )
        await conn.commit()


async def increment_movie_count(user_id: int, movie_name: str) -> None:
    """
    для статистики
    """
    async with aiosqlite.connect(DATABASE_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "SELECT count FROM movie_stats WHERE user_id = ? AND movie_name = ?",
            (user_id, movie_name),
        )
        result = await cursor.fetchone()
        if result:
            count = result[0] + 1
            await cursor.execute(
                "UPDATE movie_stats SET count = ? WHERE user_id = ? AND movie_name = ?",
                (count, user_id, movie_name),
            )
        else:
            await cursor.execute(
                "INSERT INTO movie_stats (user_id, movie_name, count) VALUES (?, ?, 1)",
                (user_id, movie_name),
            )
        await conn.commit()


async def get_search_history(
    user_id: int, query_num: int = 10
) -> list[tuple[str, str, datetime]]:
    """
    возвращает историю поиска для пользователя
    """
    async with aiosqlite.connect(DATABASE_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "SELECT query, movie_name, timestamp FROM search_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, query_num),
        )
        history = await cursor.fetchall()
    return history


async def get_movie_stats(user_id: int) -> list[tuple[str, int]]:
    """
    возвращает статистику по фильмам для пользователя
    """
    async with aiosqlite.connect(DATABASE_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "SELECT movie_name, count FROM movie_stats WHERE user_id = ? ORDER BY count DESC",
            (user_id,),
        )
        stats = await cursor.fetchall()
    return stats


def get_users_languages() -> tp.Dict[int, str]:
    """
    для информации о языках
    """
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * from users")
        users = dict(cursor.fetchall())
    return users


async def add_user(user_id: int) -> None:
    """
    добавляет нового пользователя
    """
    async with aiosqlite.connect(DATABASE_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "INSERT INTO users (user_id, user_lang) VALUES (?, ?)",
            (user_id, "ru"),
        )
        await conn.commit()


async def change_language(user_id: int, new_lang: str) -> None:
    """
    меняет язык интерфейса для пользователя
    """
    async with aiosqlite.connect(DATABASE_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "UPDATE users SET user_lang = ? WHERE user_id = ?",
            (new_lang, user_id),
        )
        await conn.commit()


async def save_movie_link(
    movie_name: str,
    link: str,
    title_ru: str,
    title_en: str,
    description_ru: str,
    description_en: str,
    genres_ru: str,
    genres_en: str,
    rating: float,
    year: int,
) -> None:
    """
    Сохраняет ссылку на фильм и дополнительную информацию в базе данных.
    """
    async with aiosqlite.connect(DATABASE_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            """
        INSERT OR REPLACE INTO movie_links (
            movie_name, link, title_ru, title_en, description_ru, description_en, genres_ru, genres_en, rating, year
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                movie_name,
                link,
                title_ru,
                title_en,
                description_ru,
                description_en,
                genres_ru,
                genres_en,
                rating,
                year,
            ),
        )
        await conn.commit()


async def get_movie_link(movie_name: str) -> str:
    """
    Возвращает ссылку на фильм по его названию.
    """
    async with aiosqlite.connect(DATABASE_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "SELECT link FROM movie_links WHERE movie_name = ?", (movie_name,)
        )
        result = await cursor.fetchone()
        return result[0] if result else None


async def get_movie_info_from_db(movie_name: str, lang: str) -> dict:
    """
    Возвращает дополнительную информацию о фильме по его названию.
    """
    title = "title_" + lang
    description = "description_" + lang
    genres = "genres_" + lang
    async with aiosqlite.connect(DATABASE_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            """
        SELECT ?, ?, ?, rating, year
        FROM movie_links
        WHERE movie_name = ?
        """,
            (
                title,
                description,
                genres,
                movie_name,
            ),
        )
        result = await cursor.fetchone()
        if result:
            return {
                "link": result[0],
                "title": result[1],
                "description": result[2],
                "genres": result[3],
                "rating": result[4],
                "year": result[5],
            }
        return None


async def main() -> None:
    await init_db()


if __name__ == "__main__":
    asyncio.run(main())
