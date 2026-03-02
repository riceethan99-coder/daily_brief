import os
from notion_client import Client


def get_todos() -> list[str]:
    """
    Read to-do checkbox blocks from a Notion page and return the text of
    any that are not yet checked off.
    """
    notion = Client(auth=os.environ["NOTION_TOKEN"])
    page_id = os.environ["NOTION_DATABASE_ID"]  # ID of your to-do page

    response = notion.blocks.children.list(block_id=page_id)

    tasks = []
    for block in response["results"]:
        if block["type"] == "to_do":
            checked = block["to_do"]["checked"]
            if not checked:
                text = "".join(
                    chunk["plain_text"]
                    for chunk in block["to_do"]["rich_text"]
                )
                if text:
                    tasks.append(text)

    return tasks
