"""Self-contained, escaped HTML presentation of recorded demo results."""

from enum import Enum
from html import escape


LABEL = "Synthetic Decision Gate demonstration — no live traffic control."
REASONS = {
    "POLICY_REQUIREMENTS_MET": "Complete favorable inputs satisfy the demo policy.",
    "CONTEXT_SHIFT": "Operating conditions changed, so automatic execution is held.",
    "HUMAN_REVIEW_REQUIRED": "Human review is required; this demo does not release held actions.",
    "SYSTEM_UNHEALTHY": "The controller is unhealthy, so execution is blocked.",
    "EVIDENCE_CONFLICT": "Conflicting evidence requires review.",
    "BELIEF_UNCERTAIN": "The supplied belief is uncertain and requires review.",
    "BELIEF_INVALID": "The supplied belief is invalid, so execution is blocked.",
    "MISSING_REQUIRED_INFORMATION": "Required information is unavailable; execution is blocked.",
    "STALE_REQUIRED_DATA": "Required data is stale; execution is blocked.",
    "UNUSABLE_REQUIRED_DATA": "Required data is unusable; execution is blocked.",
    "DEGRADED_REQUIRED_DATA": "Degraded data requires review.",
    "HIGH_CONSEQUENCE": "The action's high consequence requires review.",
    "LOW_REVERSIBILITY": "Limited reversibility requires review.",
    "UNSUPPORTED_POLICY": "The requested policy is unsupported; execution is blocked.",
}


def display(value):
    if isinstance(value, Enum):
        value = value.value
    if isinstance(value, bool):
        value = "Yes" if value else "No"
    if value is None:
        value = "Unavailable"
    return escape(str(value))


def description_list(values):
    return "<dl>" + "".join(
        f"<div><dt>{escape(key)}</dt><dd>{display(value)}</dd></div>"
        for key, value in values.items()) + "</dl>"


def render_report(results):
    cards, rows = [], []
    names = {"A Normal": "Normal", "B Environment shift": "Environment Shift",
             "C Operational failure": "Operational Failure"}
    for result in results:
        request, decision = result["request"], result["decision"]
        before, after = result["before"], result["after"]
        permission = decision["permission"]
        color = {"GREEN": "green", "YELLOW": "yellow", "RED": "red"}.get(permission, "")
        badge = f'<strong class="badge {color}">{display(permission)}</strong>'
        explanations = [REASONS.get(code, "See the recorded policy reason.")
                        for code in decision["reason_codes"]]
        timing = f"NS {before['ns_green']} → {after['ns_green']}; EW {before['ew_green']} → {after['ew_green']}"
        rows.append("<tr>" + "".join(f"<td>{display(value)}</td>" for value in (
            names.get(result["scenario"], result["scenario"]), request["proposed_action"],
            request["belief_status"], request["confidence"], result["situation"]))
            + f"<td>{badge}<small>{display(explanations[0] if explanations else 'No reason recorded.')}</small></td>"
            + f"<td><strong>{display(result['execution_result'])}</strong><small>{display(timing)}</small></td></tr>")
        context = {
            "Belief status": request["belief_status"],
            "Confidence (in belief status)": request["confidence"],
            "Data quality": request["data_quality"], "Freshness": request["data_freshness"],
            "Evidence conflict": request["evidence_conflict"], "Context shift": request["context_shift"],
            "Consequence": request["consequence_level"], "Reversibility": request["reversibility"],
            "Belief persistence (observations)": request["belief_persistence"],
            "Controller health": before["controller_health"],
        }
        detail = {
            "Traffic situation": result["situation"],
            "Traffic state": f"NS queue: {before['ns_queue']}; EW queue: {before['ew_queue']}",
            "Scripted AI proposal": request["proposed_action"],
            "Human review required": decision["requires_human_review"],
            "Missing fields": ", ".join(decision["assessment"]["missing_fields"]) or "None",
            "Execution result": result["execution_result"], "Timing before → after": timing,
            "Policy": f"{decision['policy_id']} / version {decision['policy_version']}",
        }
        reason_list = "".join(f"<li><code>{display(code)}</code> — {display(explanation)}</li>"
                              for code, explanation in zip(decision["reason_codes"], explanations))
        blocked_note = ("<p>Blocked: ordinary human confirmation cannot release this action.</p>"
                        if permission == "RED" else "")
        cards.append(f'<section><h2>{display(result["scenario"])} {badge}</h2>'
                     + description_list(detail) + "<h3>Evaluated context</h3>"
                     + description_list(context) + f"<h3>Reason codes</h3><ul>{reason_list}</ul>"
                     + blocked_note + "</section>")
    return ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>Urban Traffic Decision Gate Demo</title><style>"
            "*{box-sizing:border-box}body{font:15px/1.45 system-ui;max-width:1280px;margin:auto;padding:24px;background:#f4f6fa;color:#182130}"
            "h1{font-size:30px;line-height:1.2;margin:8px 0 16px;max-width:850px}h2{font-size:21px}h3{font-size:17px}"
            "section,.summary,.architecture{background:white;border:1px solid #dce2eb;border-radius:10px;padding:20px;margin-bottom:20px}"
            ".eyebrow{font-weight:700;color:#465770;margin:0}small{display:block;margin-top:6px;font-size:12px}"
            ".badge{display:inline-block;border:1px solid;padding:3px 8px;border-radius:5px;font-size:13px}"
            ".green{color:#125b36;background:#e6f5eb}.yellow{color:#714d00;background:#fff3cd}.red{color:#942424;background:#ffe9e9}"
            ".table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px}"
            "th,td{border-bottom:1px solid #dce2eb;padding:10px 8px;text-align:left;vertical-align:top}th{background:#f0f3f8}"
            "td:nth-child(2){max-width:210px}td:nth-child(5),td:nth-child(6){max-width:200px}"
            "caption{text-align:left;font-weight:bold;margin-bottom:8px}dl{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}"
            "dt{font-size:12px;color:#465770;font-weight:bold}dd{margin:3px 0;overflow-wrap:anywhere}"
            ".flow{display:flex;align-items:center;justify-content:space-between;gap:10px;font-weight:bold}.flow span{padding:8px}"
            "code{overflow-wrap:anywhere}@media(max-width:700px){body{padding:12px}h1{font-size:24px}dl{grid-template-columns:1fr}.flow{flex-direction:column}}"
            "</style></head><body><header><p class='eyebrow'>Urban Traffic Decision Gate Demo</p>"
            "<h1>Same AI proposal. Same belief. Different reality. Different permission.</h1>"
            f"<p><strong>{escape(LABEL)}</strong></p></header><main><section class='summary'>"
            "<p>Scripted AI proposal: increase north–south (NS) green timing from 30 to 35 synthetic seconds "
            "for the next cycle. East–west (EW) timing remains 30. The supplied belief stays VALID at confidence 0.8.</p>"
            "<div class='table-wrap'><table><caption>Scenario comparison</caption><thead><tr>"
            "<th>Scenario</th><th>AI proposal</th><th>Belief status</th><th>Confidence</th><th>Changed condition</th>"
            "<th>Permission / why</th><th>Execution result</th></tr></thead><tbody>" + "".join(rows)
            + "</tbody></table></div></section><section class='architecture'><h2>How the decision reaches execution</h2>"
            "<div class='flow' aria-label='Decision flow'><span>AI Proposal</span><span aria-hidden='true'>↓</span>"
            "<span>Reliability Information</span><span aria-hidden='true'>↓</span><span>Decision Gate</span>"
            "<span aria-hidden='true'>↓</span><span>Permission</span><span aria-hidden='true'>↓</span><span>Execution</span></div>"
            "<p>Reliability information is supplied by scripted fixtures, not newly inferred by this demo. "
            "The gate evaluates that information alongside operational context and action impact.</p></section>"
            + "".join(cards) + "</main><footer><p>Confidence is not probability of correctness. "
            "This demonstration measures no traffic improvement. YELLOW remains held; no approval workflow is implemented."
            "</p></footer></body></html>")
