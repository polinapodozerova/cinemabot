import translators as ts


def translate_text(
    text: str, inp_language: str = "ru", target_language: str = "en"
) -> str:
    new_text = ts.translate_text(
        text,
        translator="yandex",
        from_language=inp_language,
        to_language=target_language,
    )
    return new_text
