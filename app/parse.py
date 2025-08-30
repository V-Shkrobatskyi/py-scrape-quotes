import csv
from dataclasses import dataclass, fields, astuple

import requests
from bs4 import BeautifulSoup, Tag


BASE_URL = "https://quotes.toscrape.com/"


@dataclass
class Quote:
    text: str
    author: str
    tags: list[str]


@dataclass
class Author:
    name: str
    born_date: str
    born_location: str
    description: str


QUOTE_FIELDS = [field.name for field in fields(Quote)]
AUTHOR_FIELDS = [field.name for field in fields(Author)]

# authors cache (dict: link -> Author)
author_cache: dict[str, Author] = {}


def parse_single_author(author_link: str) -> Author:
    if author_link in author_cache:
        return author_cache[author_link]

    text = requests.get(BASE_URL + author_link).content
    author_page = BeautifulSoup(text, "html.parser")

    author = Author(
        name=str(author_page.select_one(".author-title").text),
        born_date=str(author_page.select_one(".author-born-date").text),
        born_location=str(
            author_page.select_one(".author-born-location").text
        ),
        description=str(author_page.select_one(".author-description").text),
    )

    author_cache[author_link] = author
    return author


def parse_single_quote(quote: Tag) -> Quote:
    author_link = quote.select_one("small.author + a")["href"]
    parse_single_author(author_link)

    return Quote(
        text=str(quote.select_one(".text").text),
        author=str(quote.select_one(".author").text),
        tags=[tag.text for tag in quote.select(".tag")],
    )


def get_single_page_quotes(page_soup: Tag) -> list[Quote]:
    quotes = page_soup.select(".quote")
    return [parse_single_quote(quote) for quote in quotes]


def get_page_quotes() -> list[Quote]:
    text = requests.get(BASE_URL).content
    first_page = BeautifulSoup(text, "html.parser")
    all_quotes = get_single_page_quotes(first_page)

    next_page_link = first_page.select_one("li.next a")["href"]
    while next_page_link:
        text = requests.get(BASE_URL + next_page_link).content
        next_page = BeautifulSoup(text, "html.parser")
        all_quotes.extend(get_single_page_quotes(next_page))

        next_page = next_page.select_one("li.next a")
        if next_page:
            next_page_link = next_page["href"]
        else:
            next_page_link = None

    return all_quotes


def write_quotes_to_csv(quotes: list[Quote], output_csv_path: str) -> None:
    with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(QUOTE_FIELDS)
        writer.writerows([astuple(quote) for quote in quotes])


def write_authors_to_csv(
        authors: dict[str, Author],
        output_csv_path: str
) -> None:
    with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(AUTHOR_FIELDS)
        writer.writerows([astuple(author) for author in authors.values()])


def main(output_csv_path: str) -> None:
    quotes = get_page_quotes()
    write_quotes_to_csv(quotes, output_csv_path)
    write_authors_to_csv(author_cache, "authors.csv")


if __name__ == "__main__":
    main("quotes.csv")
