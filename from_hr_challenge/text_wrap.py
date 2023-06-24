import textwrap


def wrap(string, max_width):
    text = textwrap.wrap(string, width=max_width)
    return "\n".join(text)
