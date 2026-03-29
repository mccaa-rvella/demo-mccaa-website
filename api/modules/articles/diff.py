from difflib import HtmlDiff


def generate_html_diff(old_html: str, new_html: str) -> str:
    """Generate an HTML diff between old and new article content."""
    differ = HtmlDiff()
    old_lines = old_html.splitlines()
    new_lines = new_html.splitlines()
    return differ.make_table(
        old_lines, new_lines,
        fromdesc="Published Version",
        todesc="New Version",
        context=True,
        numlines=3,
    )
