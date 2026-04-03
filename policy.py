import json
import os
from pathlib import Path

try:
    import anthropic
except ImportError:
    anthropic = None


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "json files"
RULES_PATH = DATA_DIR / "rules.json"
SEBI_PATH = DATA_DIR / "sebi_rules.json"


def _get_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or anthropic is None:
        return None
    return anthropic.Anthropic(api_key=api_key)


def load_rules():
    with RULES_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_sebi_rules():
    with SEBI_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_rules(data):
    with RULES_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _contains_any(text: str, phrases: list[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def _match_user_rules(action: str, rules: list[str]) -> dict | None:
    action_text = _normalize(action)
    rules_text = _normalize(" ".join(rules))

    crypto_terms = [
        "bitcoin",
        "btc",
        "crypto",
        "cryptocurrency",
        "dogecoin",
        "memecoin",
        "shitcoin",
        "ethereum",
        "eth",
        "solana",
    ]
    all_in_terms = [
        "put everything",
        "all my money",
        "entire portfolio",
        "100%",
        "all-in",
        "go all in",
        "full portfolio",
    ]
    leverage_terms = ["margin", "leveraged", "leverage", "futures", "options", "intraday"]

    if _contains_any(action_text, crypto_terms) and "avoid all cryptocurrency" in rules_text:
        return {
            "violated": True,
            "rule": "Avoid all cryptocurrency and highly speculative assets",
            "reason": "This action involves cryptocurrency, which is explicitly blocked by your personal rules.",
        }

    if _contains_any(action_text, crypto_terms) and _contains_any(action_text, all_in_terms):
        return {
            "violated": True,
            "rule": "Never invest more than 10% of the portfolio in a single stock",
            "reason": "Putting everything into bitcoin is concentrated, speculative, and conflicts with your diversification rules.",
        }

    if _contains_any(action_text, leverage_terms) and "low to medium risk" in _normalize(load_rules().get("goal", "")):
        return {
            "violated": True,
            "rule": "Grow my portfolio steadily over 5 years with low to medium risk",
            "reason": "Leveraged or short-term trading does not fit a low-to-medium-risk long-term portfolio goal.",
        }

    return None


def _match_sebi_rules(action: str, regulations: list[dict]) -> dict | None:
    action_text = _normalize(action)

    mapping = [
        (
            ["pump and dump", "manipulate price", "artificial volume", "wash trade", "circular trade", "spoof"],
            regulations[0]["title"] if len(regulations) > 0 else "SEBI PFUTP Regulations, 2003",
            "This action suggests market manipulation or artificial trading activity, which SEBI prohibits.",
        ),
        (
            ["insider tip", "inside information", "upsi", "unpublished price sensitive", "before earnings"],
            regulations[1]["title"] if len(regulations) > 1 else "SEBI PIT Regulations, 2015",
            "This action indicates use of inside information or UPSI, which is prohibited under SEBI insider trading regulations.",
        ),
        (
            ["guaranteed return", "fixed return", "assured return", "promise 20%", "promise returns"],
            regulations[2]["title"] if len(regulations) > 2 else "SEBI Investment Advisers Regulations, 2013",
            "Promising fixed or assured returns is not suitable compliance language for regulated investment advice.",
        ),
        (
            ["manage my friend's portfolio", "trade for others", "handle client money", "manage money for clients"],
            regulations[4]["title"] if len(regulations) > 4 else "SEBI Portfolio Managers Regulations, 2020",
            "Managing securities portfolios for others requires the appropriate SEBI registration and regulatory framework.",
        ),
    ]

    for phrases, title, reason in mapping:
        if _contains_any(action_text, phrases):
            return {
                "violated": True,
                "regulation": title,
                "reason": reason,
            }

    return None


async def check_intent(user_goal: str, action: str) -> dict:
    action_text = _normalize(action)
    goal_text = _normalize(user_goal)

    if not action_text:
        return {"match": False, "reason": "Please enter an action to test."}

    if _contains_any(action_text, ["put everything", "all my money", "entire portfolio", "all-in", "100%"]):
        return {
            "match": False,
            "reason": "An all-in allocation does not match a steady low-to-medium-risk investment goal.",
        }

    if "low to medium risk" in goal_text and _contains_any(
        action_text,
        ["bitcoin", "crypto", "dogecoin", "memecoin", "leveraged", "futures", "options", "intraday"],
    ):
        return {
            "match": False,
            "reason": "This action is more speculative than the goal of steady five-year growth with low to medium risk.",
        }

    client = _get_client()
    if client is None:
        return {"match": True, "reason": "Action fits the stated goal based on local safety checks."}

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
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()
    return json.loads(raw)


async def check_user_rules(rules: list, action: str) -> dict:
    heuristic_result = _match_user_rules(action, rules)
    if heuristic_result:
        return heuristic_result

    client = _get_client()
    if client is None:
        return {"violated": False, "rule": None, "reason": "No local rule violations found."}

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
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()
    return json.loads(raw)


async def check_sebi_rules(regulations: list, action: str) -> dict:
    heuristic_result = _match_sebi_rules(action, regulations)
    if heuristic_result:
        return heuristic_result

    client = _get_client()
    if client is None:
        return {"violated": False, "regulation": None, "reason": "No SEBI-related concerns found."}

    regs_text = "\n".join(
        f"- {reg.get('title')}: {reg.get('summary')}" if isinstance(reg, dict) else f"- {reg}"
        for reg in regulations
    )
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
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()
    return json.loads(raw)


async def enforce(action: str) -> dict:
    data = load_rules()
    sebi_data = load_sebi_rules()

    user_goal = data.get("goal", "")
    user_rules = data.get("rules", [])
    sebi_regulations = sebi_data.get("regulations", [])

    intent_result = await check_intent(user_goal, action)
    if not intent_result.get("match"):
        return {
            "allowed": False,
            "stage": "intent_match",
            "reason": intent_result.get("reason"),
            "rule": None,
        }

    rules_result = await check_user_rules(user_rules, action)
    if rules_result.get("violated"):
        return {
            "allowed": False,
            "stage": "user_rules",
            "reason": rules_result.get("reason"),
            "rule": rules_result.get("rule"),
        }

    sebi_result = await check_sebi_rules(sebi_regulations, action)
    if sebi_result.get("violated"):
        return {
            "allowed": False,
            "stage": "sebi_rules",
            "reason": sebi_result.get("reason"),
            "rule": sebi_result.get("regulation"),
        }

    return {
        "allowed": True,
        "stage": "all_passed",
        "reason": "Action aligns with the portfolio goal, user rules, and SEBI compliance checks.",
        "rule": None,
    }
