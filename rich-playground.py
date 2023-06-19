from rich.console import Console
from rich.text import Text
from rich.markdown import Markdown

console = Console()
text = Text("Hello, World!")
text.stylize("bold magenta", 0, 6)
console.print(text)

MARKDOWN_TEXT = """\
| Syntax      | \033[31mDescription\033[0m |
| ----------- | ----------- |
| Header       Title       |
| Paragraph   | Text        |
"""

md = Markdown(MARKDOWN_TEXT)
console.print(md)

