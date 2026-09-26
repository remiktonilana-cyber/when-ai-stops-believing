"""Self-contained, escaped HTML output; no external assets or scripts."""

from html import escape


LABEL = "Synthetic Decision Gate demonstration — no live traffic control."


def render_report(results):
    cards, rows = [], []
    for result in results:
        request, decision = result["request"], result["decision"]
        before, after = result["before"], result["after"]
        permission = decision["permission"]
        color = {"GREEN": "green", "YELLOW": "yellow", "RED": "red"}.get(permission, "")
        values = {
            "Traffic situation": result["situation"],
            "Traffic state": f"NS queue: {before['ns_queue']}; EW queue: {before['ew_queue']}",
            "Controller health": before["controller_health"],
            "Context shift": before["context_shift"],
            "Scripted AI proposal": request["proposed_action"],
            "Belief status": request["belief_status"],
            "Confidence (in belief status)": request["confidence"],
            "Permission": permission,
            "Reason codes": ", ".join(decision["reason_codes"]),
            "Human review required": decision["requires_human_review"],
            "Missing fields": ", ".join(decision["assessment"]["missing_fields"]) or "None",
            "Execution result": result["execution_result"],
            "Timing before → after": f"NS {before['ns_green']} → {after['ns_green']}; "
                                      f"EW {before['ew_green']} → {after['ew_green']}",
        }
        details = "".join(f"<dt>{escape(key)}</dt><dd>{escape(str(value))}</dd>"
                          for key, value in values.items())
        cards.append(f'<section class="{color}"><h2>{escape(result["scenario"])}</h2>'
                     f"<dl>{details}</dl></section>")
        rows.append("<tr>" + "".join(f"<td>{escape(str(value))}</td>" for value in (
            result["scenario"], request["belief_status"], request["confidence"],
            permission, result["execution_result"])) + "</tr>")
    return ("<!doctype html><html lang='en'><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>Urban Traffic Decision Gate Demo</title><style>"
            "body{font:16px system-ui;max-width:1100px;margin:2rem auto;padding:1rem;background:#f6f7fa;color:#182130}"
            "section{background:white;padding:1rem;margin:1rem 0;border-left:8px solid #555}"
            ".green{border-color:#167044}.yellow{border-color:#ad7600}.red{border-color:#bc3030}"
            "dt{font-weight:bold;margin-top:.7rem}dd{margin:.2rem 0}"
            "table{border-collapse:collapse;width:100%}td,th{border:1px solid #aaa;padding:.6rem;text-align:left}"
            "</style><body><h1>Urban Traffic Decision Gate Demo</h1>"
            f"<p><strong>{escape(LABEL)}</strong></p>"
            "<p>Scripted proposals and beliefs. Confidence is not probability of correctness. "
            "This demonstration measures no traffic improvement.</p>"
            "<table><caption>Scenario comparison</caption><thead><tr>"
            "<th>Scenario</th><th>Belief status</th><th>Confidence</th><th>Permission</th>"
            "<th>Execution result</th></tr></thead><tbody>" + "".join(rows)
            + "</tbody></table>" + "".join(cards) + "</body></html>")
