import os

from notion_client import Client

# The three toggle heading names expected on the Notion page (case-sensitive)
SECTION_RECURRING = "Recurring Tasks"
SECTION_TODAY = "Today"
SECTION_TOMORROW = "Tomorrow"


def get_tasks() -> tuple[list[str], list[str]]:
    """
    Perform the daily task reset on the Notion page, then return today's tasks.

    Daily reset logic:
      - Recurring Tasks: all checkboxes reset to unchecked
      - Today: checked items deleted, unchecked items kept (carry-over)
      - Tomorrow: all items moved into Today, Tomorrow cleared

    Returns (recurring, todos) — both are empty lists if anything fails,
    so the rest of the brief still sends.
    """
    try:
        return _run_daily_reset()
    except Exception as e:
        print(f"[notion_manager] Error: {e}")
        return [], []


def _run_daily_reset() -> tuple[list[str], list[str]]:
    notion = Client(auth=os.environ["NOTION_TOKEN"])
    page_id = os.environ["NOTION_DATABASE_ID"]

    # --- Step 1: Find the three toggle heading blocks ---
    page_blocks = notion.blocks.children.list(block_id=page_id)["results"]
    heading_ids = _find_section_headings(page_blocks)

    for name in (SECTION_RECURRING, SECTION_TODAY, SECTION_TOMORROW):
        if name not in heading_ids:
            raise ValueError(
                f"Could not find a toggle heading named '{name}' on the Notion page. "
                "Make sure all three toggle headings exist with exact spelling."
            )

    # --- Step 2: Fetch children of each section ---
    recurring_blocks = notion.blocks.children.list(block_id=heading_ids[SECTION_RECURRING])["results"]
    today_blocks     = notion.blocks.children.list(block_id=heading_ids[SECTION_TODAY])["results"]
    tomorrow_blocks  = notion.blocks.children.list(block_id=heading_ids[SECTION_TOMORROW])["results"]

    # --- Step 3: Reset Recurring Tasks (uncheck all) ---
    for block in recurring_blocks:
        if block["type"] == "to_do":
            notion.blocks.update(block["id"], **{"to_do": {"checked": False}})

    # --- Step 4: Today — delete completed, keep carry-overs ---
    for block in today_blocks:
        if block["type"] == "to_do" and block["to_do"]["checked"]:
            notion.blocks.delete(block["id"])

    # --- Step 5: Move Tomorrow → Today ---
    tomorrow_texts = []
    for block in tomorrow_blocks:
        if block["type"] == "to_do":
            text = "".join(chunk["plain_text"] for chunk in block["to_do"]["rich_text"])
            if text:
                tomorrow_texts.append(text)

    if tomorrow_texts:
        new_blocks = [
            {"object": "block", "type": "to_do", "to_do": {"rich_text": [{"type": "text", "text": {"content": t}}], "checked": False}}
            for t in tomorrow_texts
        ]
        notion.blocks.children.append(block_id=heading_ids[SECTION_TODAY], children=new_blocks)

    for block in tomorrow_blocks:
        if block["type"] == "to_do":
            notion.blocks.delete(block["id"])

    # --- Step 6: Read final state for the brief ---
    # Re-fetch Today after the changes above
    final_today = notion.blocks.children.list(block_id=heading_ids[SECTION_TODAY])["results"]
    todos = [
        "".join(chunk["plain_text"] for chunk in block["to_do"]["rich_text"])
        for block in final_today
        if block["type"] == "to_do" and not block["to_do"]["checked"]
    ]
    todos = [t for t in todos if t]  # drop empty strings

    # Re-fetch Recurring after unchecking (text is the same, just refresh for consistency)
    final_recurring = notion.blocks.children.list(block_id=heading_ids[SECTION_RECURRING])["results"]
    recurring = [
        "".join(chunk["plain_text"] for chunk in block["to_do"]["rich_text"])
        for block in final_recurring
        if block["type"] == "to_do"
    ]
    recurring = [r for r in recurring if r]

    return recurring, todos


def _find_section_headings(blocks: list[dict]) -> dict[str, str]:
    """Scan page-level blocks for headings by name and return {name: block_id}."""
    heading_ids = {}
    for block in blocks:
        for h_type in ("heading_1", "heading_2", "heading_3"):
            if block["type"] == h_type:
                text = "".join(chunk["plain_text"] for chunk in block[h_type]["rich_text"])
                if text in (SECTION_RECURRING, SECTION_TODAY, SECTION_TOMORROW):
                    heading_ids[text] = block["id"]
    return heading_ids
