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


def main(output_csv_path: str) -> None:
    pass
QUOTE_FIELDS = [field.name for field in fields(Quote)]


def parse_single_quote(quote: Tag) -> Quote:
    return Quote(
        text=str(quote.select_one(".text").text),
        author=str(quote.select_one(".author").text),
        tags=[tag.text for tag in quote.select(".tag")]
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


def main() -> None:
    quotes = get_page_quotes()
    write_quotes_to_csv(quotes, "quotes.csv")


if __name__ == "__main__":
    main()
