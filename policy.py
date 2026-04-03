import json
import os
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def load_rules():
    with open("rules.json", "r") as f:
        return json.load(f)

def load_sebi_rules():
    with open("sebi_rules.json", "r") as f:
        return json.load(f)

def save_rules(data):
    with open("rules.json", "w") as f:
        json.dump(data, f, indent=2)

async def check_intent(user_goal: str, action: str) -> dict:
    prompt = f"""
You are a financial safety enforcer called Fence.

The user's stated goal is: "{user_goal}"
The agent wants to perform this action: "{action}"

Does this action align with the user's stated goal?
Reply only in this exact JSON format:
{{
  "match": true or false,
  "reason": "your reason here"
}}
"""
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )
    
    raw = message.content[0].text.strip()
    return json.loads(raw)

async def check_user_rules(rules: list, action: str) -> dict:
    rules_text = "\n".join(f"- {r}" for r in rules)
    prompt = f"""
You are a financial safety enforcer called Fence.

The user has defined these personal investment rules:
{rules_text}

The agent wants to perform this action: "{action}"

Does this action violate any of the user's rules?
Reply only in this exact JSON format:
{{
  "violated": true or false,
  "rule": "the rule that was violated or null",
  "reason": "your reason here"
}}
"""
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )
    
    raw = message.content[0].text.strip()
    return json.loads(raw)

async def check_sebi_rules(regulations: list, action: str) -> dict:
    regs_text = "\n".join(f"- {r}" for r in regulations)
    prompt = f"""
You are a financial safety enforcer called Fence.

These are SEBI regulations that must never be violated:
{regs_text}

The agent wants to perform this action: "{action}"

Does this action violate any SEBI regulation?
Reply only in this exact JSON format:
{{
  "violated": true or false,
  "regulation": "the regulation that was violated or null",
  "reason": "your reason here"
}}
"""
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )
    
    raw = message.content[0].text.strip()
    return json.loads(raw)

async def enforce(action: str) -> dict:
    data = load_rules()
    sebi_data = load_sebi_rules()

    user_goal = data.get("goal", "")
    user_rules = data.get("rules", [])
    sebi_regulations = sebi_data.get("regulations", [])

    # Step 1: intent match
    intent_result = await check_intent(user_goal, action)
    if not intent_result.get("match"):
        return {
            "allowed": False,
            "stage": "intent_match",
            "reason": intent_result.get("reason"),
            "rule": None
        }

    # Step 2: user rules
    rules_result = await check_user_rules(user_rules, action)
    if rules_result.get("violated"):
        return {
            "allowed": False,
            "stage": "user_rules",
            "reason": rules_result.get("reason"),
            "rule": rules_result.get("rule")
        }

    # Step 3: SEBI rules
    sebi_result = await check_sebi_rules(sebi_regulations, action)
    if sebi_result.get("violated"):
        return {
            "allowed": False,
            "stage": "sebi_rules",
            "reason": sebi_result.get("reason"),
            "rule": sebi_result.get("regulation")
        }

    return {
        "allowed": True,
        "stage": "all_passed",
        "reason": "Action aligns with user intent and all rules",
        "rule": None
    }