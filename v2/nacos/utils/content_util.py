SHOW_CONTENT_SIZE = 100


def truncate_content(content: str):
    if content == "":
        return ""
    if len(content) <= SHOW_CONTENT_SIZE:
        return content
    return content[:SHOW_CONTENT_SIZE] + "..."
