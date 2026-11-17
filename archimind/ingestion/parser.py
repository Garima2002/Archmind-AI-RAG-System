"""HTML parser, cleaner, and structured section extractor."""

import logging
import re
from dataclasses import dataclass
from typing import List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class ParsedSection:
    """Represents a discrete semantic section within a document."""

    section_title: Optional[str]
    text: str


@dataclass
class ParsedDocument:
    """Container for parsed and cleaned document content."""

    title: str
    url: str
    source_domain: str
    sections: List[ParsedSection]


class DocumentParser:
    """Extracts, cleans, and structures text from HTML or plain text technical docs."""

    # Tags to strip out completely
    STRIP_TAGS = [
        "script",
        "style",
        "nav",
        "footer",
        "header",
        "aside",
        "form",
        "noscript",
        "svg",
        "button",
        "iframe",
    ]

    def clean_text(self, text: str) -> str:
        """Normalizes whitespace and removes excessive blank lines."""
        if not text:
            return ""
        # Replace multiple whitespace/newlines with clean single spaces/newlines
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        return text.strip()

    def parse(self, raw_content: str, url: str, fallback_title: str, domain: str) -> ParsedDocument:
        """Parses HTML or plaintext into structured sections."""
        # Check if content looks like HTML
        is_html = bool(re.search(r"<(html|head|body|div|p|h1|h2)[^>]*>", raw_content, re.IGNORECASE))

        if not is_html:
            cleaned = self.clean_text(raw_content)
            return ParsedDocument(
                title=fallback_title,
                url=url,
                source_domain=domain,
                sections=[ParsedSection(section_title=None, text=cleaned)],
            )

        soup = BeautifulSoup(raw_content, "html.parser")

        # Remove irrelevant non-content elements
        for tag in self.STRIP_TAGS:
            for el in soup.find_all(tag):
                el.decompose()

        # Extract title
        title = fallback_title
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        elif soup.find("h1"):
            h1 = soup.find("h1")
            if h1 and h1.text:
                title = h1.text.strip()

        sections: List[ParsedSection] = []
        body = soup.body or soup

        # Find heading-delimited sections (h2, h3)
        current_heading: Optional[str] = None
        current_paragraphs: List[str] = []

        # Walk through children
        for element in body.find_all(["h1", "h2", "h3", "h4", "p", "li", "pre", "code", "blockquote"]):
            tag_name = element.name.lower()

            if tag_name in ["h1", "h2", "h3", "h4"]:
                # Flush existing accumulated section
                if current_paragraphs:
                    section_text = self.clean_text("\n".join(current_paragraphs))
                    if len(section_text) > 30:  # Ignore trivial snippets
                        sections.append(
                            ParsedSection(
                                section_title=current_heading,
                                text=section_text,
                            )
                        )
                    current_paragraphs = []

                current_heading = element.get_text(separator=" ", strip=True)
            else:
                p_text = element.get_text(separator=" ", strip=True)
                if p_text:
                    current_paragraphs.append(p_text)

        # Flush final section
        if current_paragraphs:
            section_text = self.clean_text("\n".join(current_paragraphs))
            if len(section_text) > 30:
                sections.append(
                    ParsedSection(
                        section_title=current_heading,
                        text=section_text,
                    )
                )

        # If no sections were identified, fallback to whole body text
        if not sections:
            full_text = self.clean_text(body.get_text(separator="\n", strip=True))
            if full_text:
                sections.append(ParsedSection(section_title=None, text=full_text))

        return ParsedDocument(
            title=title,
            url=url,
            source_domain=domain,
            sections=sections,
        )
