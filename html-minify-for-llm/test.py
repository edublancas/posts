import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from pathlib import Path
from typing import List, Callable, Iterable

import requests
from openai import OpenAI
from pydantic import BaseModel
from bs4 import BeautifulSoup
import tiktoken
import pandas as pd

import lib
from cache import FunctionCache


client = OpenAI()


def answer_question(*, html_content: str, model: str, query: str) -> str:
    SYSTEM_PROMPT = """
You're an expert question-answering system. You're given a snippet of HTML content
and a question. You need to answer the question based on the HTML content. Your
response should be a plain text answer to the question based on the HTML content. Your
answer should be concise and to the point.
    """

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT.strip(),
            },
            {
                "role": "user",
                "content": f"HTML Content: {html_content}\n\nQuestion: {query}",
            },
        ],
    )

    return completion.choices[0].message.content


class ParsedColumn(BaseModel):
    name: str
    values: List[str]


class ParsedTable(BaseModel):
    name: str
    columns: List[ParsedColumn]


def parse_column(*, html_content: str, model: str, query: str) -> dict:
    SYSTEM_PROMPT = """
You're an expert web scraper. You're given the HTML contents of a table, a user
query and you have to extract a column from it that is related to the user query.

The name of the column should be the header of the column. The values should be the
text content of the cells in the column.
    """

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"HTML Content: {html_content}",
            },
            {
                "role": "user",
                "content": f"User Query: {query}",
            },
        ],
        response_format=ParsedColumn,
    )

    event = completion.choices[0].message.parsed
    return event.model_dump()


def parse_table(*, html_content: str, model: str, query: str) -> dict:
    SYSTEM_PROMPT = """
You're an expert web scraper. You're given the HTML contents of a table, a user
query and you have to extract a column from it that is related to the user query.

The name of the table should be the header of the table. The column's names should be
the headers of the columns. The values should be the text content of the cells in
the table.
    """

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"HTML Content: {html_content}",
            },
            {
                "role": "user",
                "content": f"User Query: {query}",
            },
        ],
        response_format=ParsedTable,
    )

    event = completion.choices[0].message.parsed
    return event.model_dump()


url = "https://en.wikipedia.org/wiki/Mercury_Prize"
response = requests.get(url)
html_content = response.text


def extract_table(html_content: str, table_class: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    table = soup.find("table", class_=table_class)
    if table:
        return str(table)
    else:
        raise ValueError(f"Table with class {table_class} not found")


html_content_table = extract_table(html_content, "wikitable")


cleaned_html = lib.minifier.clean(html_content)
cleaned_table = lib.minifier.clean(html_content_table)

unstructured_html = lib.tag_remover.clean(html_content)
unstructured_table = lib.tag_remover.clean(html_content_table)

markdown_html = lib.markdown_converter.clean(html_content)
markdown_table = lib.markdown_converter.clean(html_content_table)


questions_answers = {
    "Is there any artist who have won the Mercury Prize more than once? If so, who?": "PJ Harvey",
    "When did the 5th Mercury Prize ceremony take place?": "1996",
    "When was Silent Alarm nominated for the Mercury Prize?": "2005",
    "Who did Wolf Alice lose to in 2021?": "Arlo Parks",
    "Which artist requested to be withdrawn from the shortlist?": "Gorillaz",
    "Who sponsored the Mercury Prize in 2015?": "BBC",
    "When was the Mercury Prize first awarded?": "1992",
    "How many times has Oasis been nominated for the Mercury Prize? (output the number)": "2",
    "Which artist has been nominated the most times for the Mercury Prize without winning?": "Radiohead",
    "How many times has Franz Ferdinand been nominated for the Mercury Prize?": "1",
}

question_answers_columns = {
    "Extract the winners of the Mercury Prize from 1992 to 1995, in order": [
        "Primal Scream – Screamadelica",
        "Suede – Suede",
        "M People – Elegant Slumming",
        "Portishead – Dummy",
    ],
    "Give me the first artist (as they appear in the table) and corresponding "
    "albums that were shortlisted in 2022 and 2024 (in order)": [
        "Fergus McCreadie – Forest Floor",
        "Barry Can't Swim – When Will We Land?",
    ],
    "Give me the years for the 1st, 4th and 8th editions (in order)": [
        "1992",
        "1995",
        "1999",
    ],
    "Extract the shortlisted nominees (exclude the winner) for 2015, only the "
    "artist names (they appear first, followed by the album)": {
        "Aphex Twin",
        "Gaz Coombes",
        "C Duncan",
        "Eska",
        "Florence and the Machine",
        "Ghostpoet",
        "Róisín Murphy",
        "Slaves",
        "Soak",
        "Wolf Alice",
        "Jamie xx",
    },
    "Extract the shortlisted nominees (include the winner) for the 25th edition, only "
    "the artist names (they appear first, followed by the album)": {
        "Skepta",
        "Anohni",
        "Bat for Lashes",
        "David Bowie",
        "The Comet Is Coming",
        "Kano",
        "Michael Kiwanuka",
        "Laura Mvula",
        "The 1975",
        "Radiohead",
        "Savages",
        "Jamie Woon",
    },
    "Extract the shortlisted nominees (exclude the winner) for 2022, only the "
    "album names (they appear second, after the artist)": {
        "Forest Floor",
        "Tresor",
        "Harry's House",
        "For All Our Days That Tear the Heart",
        "Skin",
        "Reason to Smile",
        "Supernova",
        "Seventeen Going Under",
        "Prioritise Pleasure",
        "Wet Leg",
        "The Overload",
    },
    "Extract the first two artists (as they appear in the table) for the 2012 edition": [
        "Django Django",
        "Field Music",
    ],
    "Extract the last two artists (as they appear in the table) for the 2012 edition, "
    "exclude the album name": [
        "Roller Trio",
        "Jessie Ware",
    ],
    "Extract all the shortlisted information (exclude winner) for the 2004 "
    "edition (artist, then album, and so on), in order": [
        "Basement Jaxx",
        "Kish Kash",
        "Belle & Sebastian",
        "Dear Catastrophe Waitress",
        "Jamelia",
        "Thank You",
        "Keane",
        "Hopes and Fears",
        "Snow Patrol",
        "Final Straw",
        "Joss Stone",
        "The Soul Sessions",
        "The Streets",
        "A Grand Don't Come for Free",
        "Ty",
        "Upwards",
        "Amy Winehouse",
        "Frank",
        "Robert Wyatt",
        "Cuckooland",
        "The Zutons",
        "Who Killed...... The Zutons?",
    ],
    "Extract the shorlisted that have been shorlisted with Franz "
    "Ferdinand, artist only. In order, as they appear. If an artist appears "
    "more than once, include it multiple times": [
        "Basement Jaxx",
        "Belle & Sebastian",
        "Jamelia",
        "Keane",
        "Snow Patrol",
        "Joss Stone",
        "The Streets",
        "Ty",
        "Amy Winehouse",
        "Robert Wyatt",
        "The Zutons",
    ],
}


def contains(ground_truth: str, model_answer: str) -> bool:
    return ground_truth in model_answer


def compare_collection(
    ground_truth: Iterable[str], model_answer: Iterable[str]
) -> bool:
    if isinstance(ground_truth, list):
        return ground_truth == model_answer
    elif isinstance(ground_truth, set):
        return ground_truth == set(model_answer)
    else:
        raise ValueError(f"Unsupported type for ground truth: {type(ground_truth)}")


def interrogate(
    qa: dict,
    html_content: str,
    model_info: lib.ModelInfo,
    model_caller: Callable,
    evaluator: Callable,
    cost_only: bool = False,
) -> float:
    total_questions = len(qa)
    correct_answers = 0
    encoder = tiktoken.encoding_for_model(model_info.name)
    total_cost = 0

    for question, answer in qa.items():
        n_tokens = len(encoder.encode(html_content))
        cost = n_tokens * model_info.price_per_million_tokens / 1_000_000
        # print(f"Cost for {n_tokens:,} tokens: ${cost:.2f}")
        total_cost += cost

        if cost_only:
            continue

        print("Question:", question)

        answer_from_model = model_caller(
            html_content=html_content,
            model=model_info.name,
            query=question,
        )

        if isinstance(answer_from_model, dict):
            answer_from_model = answer_from_model["values"]

        correct = evaluator(answer, answer_from_model)

        if correct:
            correct_answers += 1

        print("Correct?", correct)

        if not correct:
            print("Correct answer:", answer)
            print("Model answer:", answer_from_model)

    print(f"Total cost for {model_info.name}: ${total_cost:.2f}")

    if not cost_only:
        accuracy = correct_answers / total_questions
        print(f"Model accuracy {model_info.name}: {accuracy:.2%}")
        return total_cost, accuracy
    else:
        return total_cost, None


answer_question_cached = FunctionCache(
    answer_question, path_to_db="cache.db", block_execution=True
)
parse_column_cached = FunctionCache(
    parse_column, path_to_db="cache.db", block_execution=True
)
parse_table_cached = FunctionCache(
    parse_table, path_to_db="cache.db", block_execution=True
)


page = {
    "raw": html_content,
    "clean": cleaned_html,
    "unstructured": unstructured_html,
    "markdown": markdown_html,
}

table = {
    "raw": html_content_table,
    "clean": cleaned_table,
    "unstructured": unstructured_table,
    "markdown": markdown_table,
}

name2extension = {
    "raw": "html",
    "clean": "html",
    "unstructured": "html",
    "markdown": "md",
}

# for name, content in page.items():
#     ext = name2extension[name]

#     if name == "markdown":
#         print("Saving markdown page")
#         Path(f"page_{name}.{ext}").write_text(content)

# for name, content in table.items():
#     ext = name2extension[name]

#     if name == "markdown":
#         print("Saving markdown table")
#         Path(f"table_{name}.{ext}").write_text(content)


# the content of the page might change, invalidating the cache.
# let's load the existing files
new_page = {}
new_table = {}

for name in ["raw", "clean", "unstructured", "markdown"]:
    ext = name2extension[name]

    page_file = Path(f"page_{name}.{ext}")
    table_file = Path(f"table_{name}.{ext}")

    if page_file.exists():
        new_page[name] = page_file.read_text()
    else:
        raise ValueError(f"File {page_file} not found")

    if table_file.exists():
        new_table[name] = table_file.read_text()
    else:
        raise ValueError(f"File {table_file} not found")


page = new_page
table = new_table


models = [
    lib.gpt4omini,
    lib.gpt4o_2024_08_06,
]

rows = []

for model_info in models:
    for page_type, page_html in page.items():
        print(f"Interrogating page {page_type}")

        try:
            total_cost, accuracy = interrogate(
                qa=questions_answers,
                html_content=page_html,
                model_info=model_info,
                model_caller=answer_question_cached,
                evaluator=contains,
                cost_only=False,
            )
        except Exception as e:
            print(f"Error (interrogate): {e}. Page type: {page_type}")
            rows.append((model_info.name, page_type, None, None, "string"))
        else:
            rows.append(
                (model_info.name, page_type, total_cost, accuracy, "unstructured")
            )

    for table_type, table_html in table.items():
        print(f"Interrogating table {table_type}")
        total_cost, accuracy = interrogate(
            qa=question_answers_columns,
            html_content=table_html,
            model_info=model_info,
            model_caller=parse_column_cached,
            evaluator=compare_collection,
            cost_only=False,
        )
        rows.append((model_info.name, table_type, total_cost, accuracy, "structured"))

df = pd.DataFrame(rows, columns=["model", "input", "cost", "accuracy", "question_type"])
df.to_parquet("results.parquet", index=False)

print(df)
