import aiohttp
import asyncio
from bs4 import BeautifulSoup
import itertools
import typing as tp
import os
from copy import deepcopy
from dotenv import load_dotenv
import random

from phrasebook import description
from translate import translate_text

load_dotenv()

good_sites = [
    "inoriginal" "rutube",
    "mydeaf",
    "inoriginal",
    "lordfilm",
    "gidonline.fun",
    "baksino",
    "hdfilmsurge",
    "madagaskar-mult",
    "shrek-mults",
    "shrek-lordfilms.ru",
    "rezka.men",
]
eng_good_sites = [
    "mydeaf",
    "inoriginal",
]
banned_sites = [
    "netflix",
    "ivi",
    "google",
    "yandex",
    "kinopoisk",
    "prime",
    "wink",
    "okko",
    "kion",
    "amazon",
    "kinogo",
    "ok.ru",
    "jut.su",
]
good_sites_with_priorities = {
    good_sites[i]: (i + 1) for i in range(len(good_sites))
}

NUM_LINKS_ON_PAGE = 10
NUM_PAGES_TO_SCRAPE = 7
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5)\
            AppleWebKit/537.36 (KHTML, like Gecko) Cafari/537.36"
}
KINOPOISK_API = os.environ["KINOPOISK_API"]


class MovieInfo:
    """
    Класс для хранения информации о фильме.

    :param movie_id: Идентификатор фильма.
    :param title_ru: Название фильма на русском языке.
    :param title_en: Название фильма на английском языке.
    :param year: Год выпуска фильма.
    :param length: Продолжительность фильма.
    :param description: Описание или сюжет фильма.
    :param genres: Список жанров фильма.
    :param rating: Рейтинг фильма.
    :param poster_url: URL постера фильма.
    """

    def __init__(
        self,
        movie_id,
        title_ru,
        title_en,
        year,
        length,
        description,
        description_en,
        genres,
        genres_en,
        rating,
        poster_url,
        lang="ru",
    ):
        self.movie_id = movie_id
        self.title_ru = title_ru
        self.title_en = title_en
        self.year = year
        self.length = length
        self.description = description
        self.description_en = description_en
        self.genres = genres
        self.genres_en = genres_en
        self.rating = rating
        self.poster_url = poster_url
        self.lang = lang

    def __str__(self):
        """
        Возвращает строковое представление объекта MovieInfo.
        """
        return description(
            self.title_ru,
            self.title_en,
            self.year,
            self.rating,
            self.genres,
            self.genres_en,
            self.description,
            self.description_en,
        )[self.lang]


def good_link(link: str) -> bool:
    if "http" in link:
        for bad_site in banned_sites:
            if bad_site in link:
                return False
        return True
    return False


def what_lang(text: str) -> str:
    eng = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    eng_count = 0
    for i in text:
        if i in eng:
            eng_count += 1
    eng_rate = eng_count / len(text)
    if eng_rate > 0.8:
        return "en"
    return "ru"


def create_search_url(movie_name: str, page_num=0, lang='ru') -> str:
    query = movie_name.replace(" ", "+")
    if lang == 'ru' and what_lang(movie_name) == "ru":
        return f"https://www.google.com/search?q={query}+смотреть+онлайн&start={page_num * NUM_LINKS_ON_PAGE}"
    else:
        return f"https://www.google.com/search?q={query}+watch+online+с+субтитрами+в+оригинале&start=\
            {page_num * NUM_LINKS_ON_PAGE}"


async def find_all_links_on_page(
    session: aiohttp.ClientSession, search_url: str
) -> tp.List[str]:

    good_links: tp.List[str] = []
    try:
        async with session.get(search_url, headers=HEADERS) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    if good_link(href):
                        good_links.append(href)
            else:
                print(f"Error: Received status {response.status} from Google.")
    except aiohttp.ClientError as e:
        print(f"Error connecting to Google: {e}")
    return good_links


def get_priority(url: str) -> int:
    for site_name in banned_sites:
        if site_name in url:
            return 0
    for site_name in good_sites:
        if site_name in url:
            return good_sites_with_priorities[site_name]
    return 1000


def select_most_relevant_link(links: tp.List[str], top) -> str:
    """
    Выбирает наиболее релевантные ссылки на основе приоритета.

    :param links: Список ссылок.
    :param top: Количество ссылок для выбора.
    :return: Список наиболее релевантных ссылок.
    """
    links_with_priority = set((link, get_priority(link)) for link in links)
    for link, priority in deepcopy(links_with_priority):
        if priority == 0:
            links_with_priority.remove((link, priority))
    sorted_links = sorted(links_with_priority, key=lambda x: x[1])
    return [movie[0] for movie in sorted_links[:top]]


async def find_movie_urls(movie_name: str, top=3, lang='ru') -> str:
    """
    Находит ссылки на фильм на основе его названия.

    :param movie_name: Название фильма.
    :param top: Количество ссылок для выбора.
    :return: Список наиболее релевантных ссылок.
    """
    all_search_urls: tp.List[str] = []

    for page_num in range(NUM_PAGES_TO_SCRAPE):
        search_url = create_search_url(movie_name, page_num, lang)
        all_search_urls.append(search_url)

    async with aiohttp.ClientSession() as session:
        responses = [
            find_all_links_on_page(session, url) for url in all_search_urls
        ]
        links = await asyncio.gather(*responses)
        links = list(itertools.chain(*links))[:top]
        return select_most_relevant_link(links, top)[0]


async def get_movie_info(movie_name: str, lang="ru") -> MovieInfo:
    """
    Получает информацию о фильме с помощью Kinopoisk API.

    :param movie_name: Название фильма.
    :return: Объект MovieInfo с информацией о фильме.
    """
    kinopoisk_search_id_url = (
        "https://kinopoiskapiunofficial.tech/api/v2.1/films/search-by-keyword"
    )
    kinopoisk_headers = {
        "X-API-KEY": KINOPOISK_API,
        "Content-Type": "application/json",
        "User-Agent": HEADERS["User-Agent"],
    }
    kinopoisk_params = {
        "keyword": movie_name,
        "page": 1,
        "searchFilmsCountResult": 1,
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                kinopoisk_search_id_url,
                headers=kinopoisk_headers,
                params=kinopoisk_params,
            ) as response:
                if response.status == 200:
                    movie_data = await response.json()
                    movie_data = movie_data.get("films")[0]
                    return give_movie_info(movie_data, lang)
                print(
                    f"Error: Received status {response.status, response} from kinopoisk."
                )
        except aiohttp.ClientError as e:
            print(f"Error connecting to kinopoisk: {e}")


async def get_random_movie_from_top250(
    genre_name: str = "драма", lang="ru"
) -> MovieInfo:
    """
    выдает случайный фильм из топ-250 Кинопоиска с возможностью фильтрации по жанру
    :param genre_id: ID жанра для фильтрации.
    :return: Объект MovieInfo.
    """
    kinopoisk_top250_url = (
        "https://kinopoiskapiunofficial.tech/api/v2.2/films/top"
    )
    kinopoisk_headers = {
        "X-API-KEY": KINOPOISK_API,
        "Content-Type": "application/json",
        "User-Agent": HEADERS["User-Agent"],
    }

    films_by_genre = []
    async with aiohttp.ClientSession() as session:
        try:
            for page in range(1, 11):
                async with session.get(
                    kinopoisk_top250_url,
                    headers=kinopoisk_headers,
                    params={"type": "TOP_250_BEST_FILMS", "page": page},
                ) as response:
                    if response.status == 200:
                        top250_data = await response.json()
                        films = top250_data.get("films", [])
                        new_films_by_genre = [
                            film
                            for film in films
                            if any(
                                (genre.get("genre") == genre_name)
                                for genre in film.get("genres", [])
                            )
                        ]
                        for film in new_films_by_genre:
                            films_by_genre.append(film)
                    else:
                        raise Exception(
                            f"Error: Received status {response.status} from Kinopoisk."
                        )
            if films_by_genre:
                movie_data = random.choice(films_by_genre)
                return give_movie_info(movie_data, lang)
            else:
                raise Exception(
                    "No films found in the top 250 with the specified genre."
                )
        except aiohttp.ClientError as e:
            raise Exception(f"Error connecting to Kinopoisk: {e}")


def give_movie_info(movie_data, lang="ru"):
    genres_dict = (movie_data.get("genres", "неизвестный жанр")[0],)
    return MovieInfo(
        movie_id=movie_data.get("filmId", "неизвестный id"),
        title_ru=movie_data.get("nameRu", "неизвестное название"),
        title_en=movie_data.get("nameEn", "неизвестное название"),
        year=movie_data.get("year", "неизвестный год"),
        length=movie_data.get("filmLength", "неизвестная длина"),
        description=movie_data.get("description", "описания нет"),
        description_en=translate_text(
            movie_data.get("description", "описания нет")
        ),
        genres=[genre["genre"] for genre in genres_dict],
        genres_en=[translate_text(genre["genre"]) for genre in genres_dict],
        rating=movie_data.get("rating", "неизвестный рейтинг"),
        poster_url=movie_data.get("posterUrl", "постера нет"),
        lang=lang,
    )
