import openai
from config import OPENAI_KEY, OPENAI_MODEL
from audio.utils import extract_json_block

# Configure API key once here
openai.api_key = OPENAI_KEY


def generate_summary(transcript_text: str):
    """
    Send transcript to GPT and return the parsed JSON summary using extract_json_block.
    (Flow and output schema unchanged.)
    """
    system_prompt = """
You are an expert business analyst. You will be given a raw transcript from a client-agency meeting.

Your task is to extract a comprehensive and structured summary in JSON format using the schema below.

Please follow these guidelines strictly:
- Be concise but informative. Ensure each bullet is standalone and easy to understand.
- Use consistent formatting (no sentence fragments; start with verbs where applicable).
- For To-Do items, include responsible parties and estimated deadlines if mentioned or inferable.
- Include actionable insights and KPIs if discussed.
- Maintain professional tone. Avoid repetition.

Return **only valid JSON** with no extra text, markdown, or explanation.

Schema:
{
  "mom": ["<Key discussion points and agreements>", "..."],
  "todo_list": ["<Actionable task with responsible person and timeframe, if known>", "..."],
  "action_plan": {
    "decision_made": ["<Key decisions taken>", "..."],
    "key_services_to_promote": ["<Service list>", "..."],
    "target_geography": ["<Location list>", "..."],
    "budget_and_timeline": ["<Budget, timeline details>", "..."],
    "lead_management_strategy": ["<Lead handling strategy>", "..."],
    "next_steps_and_ownership": ["<Task and responsible person>", "..."]
  }
}
"""
    chat_response = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcript_text},
        ],
    )

    return extract_json_block(chat_response.choices[0].message.content)
