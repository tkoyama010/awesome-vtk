"""Build a static GitHub Pages gallery from the entries listed in README.md."""

from __future__ import annotations

import argparse
import html
import logging
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)

HEADING = re.compile(r"^##\s+(?P<title>.+?)\s*$")
ENTRY = re.compile(
    r"^-\s+\[(?P<name>[^\]]+)\]\((?P<url>[^)\s]+)\)"
    r"(?:\s+-\s+(?P<description>.+?))?\s*$",
)
GITHUB_REPO = re.compile(
    r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/#?]+)/?$",
)
NON_ALNUM = re.compile(r"[^a-z0-9]+")

# The table of contents is generated from the headings below it, so its list
# items are not gallery entries.
IGNORED_SECTIONS = frozenset({"contents"})

TEMPLATE_DIR = Path("site")
ASSETS = ("style.css", "app.js")
HUES = 360


@dataclass(frozen=True)
class Entry:
    """A single link taken from the awesome list."""

    name: str
    url: str
    description: str
    category: str

    @property
    def host(self) -> str:
        """Returns the host name of the link, without a ``www.`` prefix."""
        return urlsplit(self.url).netloc.removeprefix("www.")

    @property
    def thumbnail(self) -> str:
        """Returns a preview image URL, or an empty string when there is none."""
        match = GITHUB_REPO.match(self.url)
        if match is None:
            return ""
        return (
            f"https://opengraph.githubassets.com/awesome-vtk/"
            f"{match['owner']}/{match['repo']}"
        )

    @property
    def initials(self) -> str:
        """Returns the placeholder monogram shown when no preview image loads."""
        return self.name[0].upper()

    @property
    def hue(self) -> int:
        """Returns a stable hue used to tint the placeholder monogram."""
        return sum(ord(character) for character in self.name) % HUES


@dataclass(frozen=True)
class Category:
    """A README section together with the entries it contains."""

    title: str
    entries: tuple[Entry, ...]

    @property
    def slug(self) -> str:
        """Returns an identifier usable in HTML attributes."""
        return NON_ALNUM.sub("-", self.title.lower()).strip("-")


def parse_readme(readme: Path) -> list[Category]:
    """Collect the entries of every README section, keeping the file order."""
    categories: list[Category] = []
    title = ""
    entries: list[Entry] = []

    def flush() -> None:
        if title and entries:
            categories.append(Category(title=title, entries=tuple(entries)))

    for line in readme.read_text(encoding="utf-8").splitlines():
        heading = HEADING.match(line)
        if heading is not None:
            flush()
            title = heading["title"]
            entries = []
            continue
        if title.lower() in IGNORED_SECTIONS:
            continue
        entry = ENTRY.match(line)
        if entry is not None:
            entries.append(
                Entry(
                    name=entry["name"],
                    url=entry["url"],
                    description=entry["description"] or "",
                    category=title,
                ),
            )
    flush()
    return categories


def render_card(entry: Entry) -> str:
    """Render a single gallery card."""
    name = html.escape(entry.name)
    description = html.escape(entry.description)
    haystack = html.escape(f"{entry.name} {entry.description} {entry.category}".lower())
    thumbnail = (
        f'<img class="card__image" src="{html.escape(entry.thumbnail)}" alt="" '
        f'loading="lazy" decoding="async" />'
        if entry.thumbnail
        else ""
    )
    return f"""      <article class="card" data-category="{html.escape(entry.category)}" data-search="{haystack}">
        <a class="card__link" href="{html.escape(entry.url)}" target="_blank" rel="noopener noreferrer">
          <div class="card__thumb" style="--hue: {entry.hue}">
            <span class="card__monogram" aria-hidden="true">{html.escape(entry.initials)}</span>
            {thumbnail}
          </div>
          <div class="card__body">
            <h3 class="card__title">{name}</h3>
            <p class="card__description">{description}</p>
            <p class="card__meta">{html.escape(entry.host)}</p>
          </div>
        </a>
      </article>"""  # noqa: E501


def render_section(category: Category) -> str:
    """Render one README section as a titled grid of cards."""
    cards = "\n".join(render_card(entry) for entry in category.entries)
    return f"""    <section class="section" id="{category.slug}" data-category="{html.escape(category.title)}">
      <h2 class="section__title">
        {html.escape(category.title)}
        <span class="section__count">{len(category.entries)}</span>
      </h2>
      <div class="grid">
{cards}
      </div>
    </section>"""  # noqa: E501


def render_filters(categories: list[Category]) -> str:
    """Render the category filter buttons."""
    titles = ["all", *(category.title for category in categories)]
    return "\n".join(
        f'        <button class="chip{" chip--active" if index == 0 else ""}" '
        f'type="button" data-filter="{html.escape(title)}">'
        f"{html.escape('All' if index == 0 else title)}</button>"
        for index, title in enumerate(titles)
    )


def render_page(template: str, categories: list[Category]) -> str:
    """Fill the page template with the parsed list."""
    total = sum(len(category.entries) for category in categories)
    replacements = {
        "{{FILTERS}}": render_filters(categories),
        "{{SECTIONS}}": "\n".join(render_section(c) for c in categories),
        "{{ENTRY_COUNT}}": str(total),
        "{{CATEGORY_COUNT}}": str(len(categories)),
    }
    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)
    return template


def build(readme: Path, template_dir: Path, output: Path) -> int:
    """Write the site into ``output`` and return the number of entries."""
    categories = parse_readme(readme)
    page = render_page(
        (template_dir / "index.html").read_text(encoding="utf-8"),
        categories,
    )
    output.mkdir(parents=True, exist_ok=True)
    (output / "index.html").write_text(page, encoding="utf-8")
    for asset in ASSETS:
        shutil.copyfile(template_dir / asset, output / asset)
    # The site is already built, so tell GitHub Pages not to run it through
    # Jekyll on the way out.
    (output / ".nojekyll").touch()
    return sum(len(category.entries) for category in categories)


def main() -> None:
    """Parse the command line arguments and build the site."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readme", type=Path, default=Path("README.md"))
    parser.add_argument("--template-dir", type=Path, default=TEMPLATE_DIR)
    parser.add_argument("--output", type=Path, default=Path("_site"))
    arguments = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    total = build(arguments.readme, arguments.template_dir, arguments.output)
    logger.info("Wrote %s with %d entries", arguments.output / "index.html", total)


if __name__ == "__main__":
    main()
