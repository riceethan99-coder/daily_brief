import os

import anthropic


def get_focus(events: list[str], todos: list[str], recurring: list[str], emails: list[str]) -> str:
    """
    Use Claude to generate a 1–2 sentence recommendation of the single most
    important focus for today, given the person's tasks, calendar, and emails.

    Returns an empty string if anything fails — the focus section is simply
    omitted from the brief rather than blocking it.
    """
    try:
        return _generate_focus(events, todos, recurring, emails)
    except Exception as e:
        print(f"[focus_generator] Error: {e}")
        return ""


def _generate_focus(events: list[str], todos: list[str], recurring: list[str], emails: list[str]) -> str:
    calendar_str  = "\n".join(f"- {e}" for e in events)   if events   else "Nothing scheduled"
    todos_str     = "\n".join(f"- {t}" for t in todos)    if todos    else "None"
    recurring_str = "\n".join(f"- {r}" for r in recurring) if recurring else "None"
    emails_str    = "\n".join(f"- {e}" for e in emails)   if emails   else "None"

    prompt = f"""You are a personal assistant for the founder of fenflowai, a business.

Today's calendar:
{calendar_str}

Tasks for today (these are the only tasks to consider):
{todos_str}

Daily habits (do NOT use these when choosing a focus task):
{recurring_str}

Emails needing attention:
{emails_str}

Rules for choosing the focus:
1. Only consider tasks from "Tasks for today" — ignore daily habits entirely.
2. Priority order: tasks with a deadline or due date first, then client work or business growth tasks for fenflowai (signing clients, delivering client work, outreach, revenue-generating activities), then everything else.
3. If "Tasks for today" is empty or contains no actionable tasks, output one short motivational quote instead (max 12 words, no attribution).

Output one short sentence only (max 15 words). No preamble, no explanation."""

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=60,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text.strip()
