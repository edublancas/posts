import re
import uuid
from abc import ABC, abstractmethod
from collections import namedtuple


import tiktoken
from markdownify import markdownify as md


from bs4 import BeautifulSoup


ModelInfo = namedtuple("ModelInfo", ["name", "price_per_million_tokens"])

gpt4omini = ModelInfo("gpt-4o-mini", 0.150)
gpt4o = ModelInfo("gpt-4o", 5.0)
gpt4o_2024_08_06 = ModelInfo("gpt-4o-2024-08-06", 2.5)
MODEL_INFO = gpt4omini


class HTMLCleaner(ABC):

    @abstractmethod
    def clean(self, html_content: str) -> str:
        pass


class BodyExtractor(HTMLCleaner):
    def clean(self, html_content: str) -> str:
        soup = BeautifulSoup(html_content, "html.parser")
        body = soup.find("body")

        if body:
            return str(body)
        else:
            return html_content


class AttributeRemover(HTMLCleaner):
    def clean(self, html_content: str) -> str:
        # Parse the HTML
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # List of attributes to keep
        attrs_to_keep = ["class", "id", "data-testid"]

        # Remove all attributes except those in attrs_to_keep
        for tag in soup.find_all():
            for attr in list(tag.attrs.keys()):
                if attr not in attrs_to_keep:
                    del tag[attr]

        # Get the cleaned HTML as a string
        cleaned_html = str(soup)

        return cleaned_html


class ClassReplacer(HTMLCleaner):
    def __init__(self, random: bool = True):
        self.random = random
        self.counter = 0

    @staticmethod
    def extract_classes(html_content: str) -> list:
        soup = BeautifulSoup(html_content, "html.parser")
        classes = set()

        for tag in soup.find_all(class_=True):
            classes.update(tag.get("class", []))

        return sorted(list(classes))

    def generate_class_mapping(self, class_list: list) -> dict:
        mapping = {}
        for class_name in class_list:
            if self.random:
                # Generate a random 4-character string using uuid4
                new_value = str(uuid.uuid4())[:4]
            else:
                self.counter += 1
                new_value = str(self.counter)
            mapping[class_name] = new_value
        return mapping

    @staticmethod
    def replace_classes(html_content: str, class_mapping: dict) -> str:
        soup = BeautifulSoup(html_content, "html.parser")

        for tag in soup.find_all(class_=True):
            original_classes = tag.get("class", [])
            new_classes = [class_mapping.get(cls, cls) for cls in original_classes]
            tag["class"] = new_classes

        return str(soup)

    def clean(self, html_content: str) -> str:
        self.counter = 0
        classes = self.extract_classes(html_content)
        mapping = self.generate_class_mapping(classes)
        return self.replace_classes(html_content, mapping)


class IDReplacer(HTMLCleaner):
    def __init__(self, random: bool = True):
        self.random = random
        self.counter = 0

    @staticmethod
    def extract_ids(html_content: str) -> list:
        soup = BeautifulSoup(html_content, "html.parser")
        ids = set()

        for tag in soup.find_all(id=True):
            ids.add(tag.get("id"))

        return sorted(list(ids))

    def generate_id_mapping(self, id_list: list) -> dict:
        mapping = {}
        for id_name in id_list:
            if self.random:
                # Generate a random 4-character string using uuid4
                new_value = str(uuid.uuid4())[:4]
            else:
                self.counter += 1
                new_value = str(self.counter)
            mapping[id_name] = new_value
        return mapping

    @staticmethod
    def replace_ids(html_content: str, id_mapping: dict) -> str:
        soup = BeautifulSoup(html_content, "html.parser")

        for tag in soup.find_all(id=True):
            original_id = tag.get("id")
            new_id = id_mapping.get(original_id, original_id)
            tag["id"] = new_id

        return str(soup)

    def clean(self, html_content: str) -> str:
        self.counter = 0
        ids = self.extract_ids(html_content)
        mapping = self.generate_id_mapping(ids)
        return self.replace_ids(html_content, mapping)


class HTMLMinifier(HTMLCleaner):
    @staticmethod
    def minify_html(html_content: str) -> str:
        # Remove comments
        html_content = re.sub(r"<!--.*?-->", "", html_content, flags=re.DOTALL)

        # Remove whitespace between tags
        html_content = re.sub(r">\s+<", "><", html_content)

        # Remove leading and trailing whitespace
        html_content = html_content.strip()

        # Collapse multiple spaces into a single space within tags
        html_content = re.sub(r"\s+", " ", html_content)

        return html_content

    def clean(self, html_content: str) -> str:
        return self.minify_html(html_content)


class ATagTrimmer(HTMLCleaner):
    def clean(self, html_content: str) -> str:
        soup = BeautifulSoup(html_content, "html.parser")

        for a_tag in soup.find_all("a"):
            if not a_tag.attrs:
                a_tag.unwrap()

        return str(soup)


class HTMLCleanerPipeline:
    def __init__(
        self,
        *,
        cleaners: list[HTMLCleaner],
        model: str,
        price_per_million_tokens: float,
    ):
        self.cleaners = cleaners
        self.model = model
        self.price_per_million_tokens = price_per_million_tokens

    def count_tokens(self, text: str) -> int:
        encoding = tiktoken.encoding_for_model(self.model)
        return len(encoding.encode(text))

    def compute_cost(self, token_count: int) -> float:
        return (token_count / 1_000_000) * self.price_per_million_tokens

    def clean(self, html_content: str) -> str:
        initial_token_count = self.count_tokens(html_content)
        initial_cost = self.compute_cost(initial_token_count)

        print(
            f"Initial HTML content length: {len(html_content):,} ({initial_token_count:,} tokens, ${initial_cost:,.2f})"
        )

        for cleaner in self.cleaners:
            html_content = cleaner.clean(html_content)
            token_count = self.count_tokens(html_content)
            cost = self.compute_cost(token_count)
            print(
                f"HTML content length after {cleaner.__class__.__name__}: {len(html_content):,}"
                f" ({token_count:,} tokens, ${cost:,.2f})"
            )

        return html_content

    def set_model_info(self, model_info: ModelInfo):
        self.model = model_info.name
        self.price_per_million_tokens = model_info.price_per_million_tokens


class TagRemover(HTMLCleaner):
    def clean(self, html_content: str) -> str:
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract all text from the HTML, replacing tags with a single space
        text = " ".join(soup.stripped_strings)

        # Remove extra whitespace
        text = " ".join(text.split())

        return text


class MarkdownConverter(HTMLCleaner):
    def clean(self, html_content: str) -> str:
        return md(html_content)


class EmptyCleaner(HTMLCleaner):
    def clean(self, html_content: str) -> str:
        return html_content


minifier = HTMLCleanerPipeline(
    cleaners=[
        BodyExtractor(),
        AttributeRemover(),
        ClassReplacer(random=False),
        IDReplacer(random=False),
        HTMLMinifier(),
        ATagTrimmer(),
    ],
    model=MODEL_INFO.name,
    price_per_million_tokens=MODEL_INFO.price_per_million_tokens,
)


tag_remover = HTMLCleanerPipeline(
    cleaners=[
        TagRemover(),
    ],
    model=MODEL_INFO.name,
    price_per_million_tokens=MODEL_INFO.price_per_million_tokens,
)

markdown_converter = HTMLCleanerPipeline(
    cleaners=[
        MarkdownConverter(),
    ],
    model=MODEL_INFO.name,
    price_per_million_tokens=MODEL_INFO.price_per_million_tokens,
)


no_cleaner = HTMLCleanerPipeline(
    cleaners=[
        EmptyCleaner(),
    ],
    model=MODEL_INFO.name,
    price_per_million_tokens=MODEL_INFO.price_per_million_tokens,
)
