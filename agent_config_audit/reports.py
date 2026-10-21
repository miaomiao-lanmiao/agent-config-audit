"""Deterministic reports that never embed raw launch or credential values."""

from __future__ import annotations

import html
import json
from collections import Counter
from typing import Any

from . import __version__
from .compare import compare
from .config import Config
from .rules import RULES, SEVERITY, audit


def make_report(config: Config, before: Config | None = None) -> dict[str, Any]:
    findings = audit(config)
    counts = Counter(item.severity for item in findings)
    report: dict[str, Any] = {
        "schema_version": "1.0",
        "tool": {"name": "agent-config-audit", "version": __version__},
        "mode": "diff" if before else "scan",
        "input_sha256": config.digest,
        "summary": {
            "servers": len(config.servers),
            "disabled": sum(bool(server.get("disabled")) for server in config.servers.values()),
            "findings": len(findings),
            "high": counts["high"],
            "medium": counts["medium"],
            "low": counts["low"],
        },
        "findings": [item.to_dict() for item in findings],
        "limitations": "Static heuristics only. No server was started or contacted. No findings does not establish safety. Server names and JSON pointers are included; raw configuration values are omitted.",
    }
    if before is not None:
        report["before_sha256"] = before.digest
        report["before_findings"] = [item.to_dict() for item in audit(before)]
        report["changes"] = [item.to_dict() for item in compare(before, config)]
    return report


def fails(report: dict[str, Any], threshold: str) -> bool:
    return threshold != "none" and any(SEVERITY[item["severity"]] >= SEVERITY[threshold] for item in report["findings"])


def _terminal(value: str) -> str:
    return "".join(char if char.isprintable() else "?" for char in value)


def render_text(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        f"AGENT CONFIG AUDIT  v{__version__}",
        f"{summary['servers']} servers / {summary['disabled']} disabled / {summary['findings']} findings",
        f"HIGH {summary['high']}   MEDIUM {summary['medium']}   LOW {summary['low']}",
        "",
    ]
    for item in report["findings"]:
        lines.append(f"[{item['severity'].upper()}] {item['rule_id']} {_terminal(item['server'])}: {item['title']}")
        lines.append(f"  {item['recommendation']}")
    if not report["findings"]:
        lines.append("No findings from the current static rules.")
    if "changes" in report:
        lines.extend(["", f"CONFIGURATION DRIFT: {len(report['changes'])} change(s)"])
        for item in report["changes"]:
            lines.append(
                f"  {item['kind'].upper()} {_terminal(item['server'])} ({', '.join(item['fields']) or 'server'})"
            )
    lines.extend(["", report["limitations"], f"Input SHA-256: {report['input_sha256']}"])
    return "\n".join(lines) + "\n"


def render_sarif(report: dict[str, Any]) -> str:
    rules = [
        {
            "id": rule_id,
            "shortDescription": {"text": title},
            "help": {"text": fix},
            "defaultConfiguration": {"level": "error" if severity == "high" else "warning"},
        }
        for rule_id, (severity, title, fix) in sorted(RULES.items())
    ]
    result = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"name": "agent-config-audit", "version": __version__, "rules": rules}},
                "results": [
                    {
                        "ruleId": item["rule_id"],
                        "level": "error" if item["severity"] == "high" else "warning",
                        "message": {"text": f"{item['title']}. {item['recommendation']}"},
                        "locations": [
                            {"logicalLocations": [{"fullyQualifiedName": item["pointer"], "kind": "member"}]}
                        ],
                        "properties": {"server": item["server"], "jsonPointer": item["pointer"]},
                    }
                    for item in report["findings"]
                ],
                "properties": {
                    "input_sha256": report["input_sha256"],
                    "mode": report["mode"],
                    "changes": report.get("changes", []),
                    "limitations": report["limitations"],
                },
            }
        ],
    }
    return json.dumps(result, indent=2, ensure_ascii=True) + "\n"


def render_html(report: dict[str, Any]) -> str:
    escape = html.escape
    summary = report["summary"]
    cards = []
    for item in report["findings"]:
        cards.append(
            f'<article class="finding" data-severity="{item["severity"]}">'
            f'<div class="finding-top"><span class="severity {item["severity"]}">{item["severity"].upper()}</span>'
            f'<span class="rule">{item["rule_id"]}</span><span class="server">{escape(item["server"])}</span></div>'
            f"<h3>{escape(item['title'])}</h3><p>{escape(item['recommendation'])}</p>"
            f"<code>{escape(item['pointer'])}</code></article>"
        )
    if not cards:
        cards.append(
            '<div class="empty"><span class="empty-mark">&#10003;</span><h3>No findings from the current rules</h3><p>Review package provenance and runtime permissions before launch.</p></div>'
        )
    drift = ""
    if "changes" in report:
        rows = "".join(
            f'<tr><td><span class="change-kind">{escape(item["kind"].upper())}</span></td>'
            f"<td>{escape(item['server'])}</td><td>{escape(', '.join(item['fields']) or 'server')}</td></tr>"
            for item in report["changes"]
        )
        drift = (
            f'<section class="drift" aria-labelledby="drift-title"><h2 id="drift-title">Configuration drift <span>{len(report["changes"]):02d}</span></h2>'
            f'<div class="table-scroll"><table><thead><tr><th>Change</th><th>Server</th><th>Fields</th></tr></thead><tbody>{rows}</tbody></table></div>'
            '<p class="muted">Field names only. Before and after values stay in your configuration files.</p></section>'
        )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>Agent Config Audit — Configuration review</title>
<style>
:root{{--ink:#18252b;--muted:#5d6b70;--paper:#f5f5ef;--line:#d9dfd8;--green:#17634e;--red:#ad3437;--amber:#936310}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.65 system-ui,-apple-system,'Segoe UI',sans-serif}}
a{{color:inherit}}.top{{border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;padding:20px 5%;gap:14px}}
.brand{{font-weight:760;letter-spacing:-.5px;font-size:18px}}.brand b{{display:inline-grid;place-items:center;background:var(--ink);color:#d3edb0;width:32px;height:32px;margin-right:10px;border-radius:7px;font:700 17px monospace}}
.offline{{color:var(--green);font:12px ui-monospace,monospace;letter-spacing:.06em}}.offline::before{{content:'●';margin-right:8px}}
main{{max-width:1160px;margin:auto;padding:54px 32px 30px}}.eyebrow{{font:12px ui-monospace,monospace;letter-spacing:.14em;color:var(--green);text-transform:uppercase}}
.hero{{display:flex;justify-content:space-between;align-items:flex-end;gap:32px;margin-bottom:36px}}h1{{font-size:clamp(34px,5vw,54px);line-height:1.13;letter-spacing:-2px;font-weight:650;margin:12px 0 17px}}
.intro{{color:var(--muted);max-width:590px;margin:0}}.edition{{font:12px/1.8 ui-monospace,monospace;text-align:right;color:var(--muted);white-space:nowrap}}
.stats{{display:grid;grid-template-columns:1.25fr repeat(3,1fr);border:1px solid var(--line);border-radius:12px;overflow:hidden;background:#fff;margin-bottom:37px}}
.stat{{padding:20px 25px;border-right:1px solid var(--line)}}.stat:last-child{{border:0}}.stat-label{{color:var(--muted);font:11px ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase}}
.stat-value{{display:block;font-size:39px;line-height:1.4;letter-spacing:-1.5px}}.stat small{{color:var(--muted);font-size:12px}}.stat.high .stat-value{{color:var(--red)}}.stat.medium .stat-value{{color:var(--amber)}}
.content{{display:grid;grid-template-columns:225px minmax(0,1fr);gap:38px}}aside{{font-size:13px}}aside h2{{font:11px ui-monospace,monospace;letter-spacing:.1em;color:var(--muted);text-transform:uppercase;margin:0 0 17px}}
.nav-item{{display:block;padding:12px 14px;background:#e5eadf;border-radius:6px;font-weight:600;text-decoration:none;margin-bottom:25px}}.notes{{border-top:1px solid var(--line);padding-top:17px}}.notes p{{margin:0 0 14px;color:var(--muted)}}
.section-heading{{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:16px}}h2{{font-size:21px;letter-spacing:-.5px;margin:0}}h2 span{{font:12px ui-monospace,monospace;color:var(--muted);margin-left:8px}}
.review-label{{font:11px ui-monospace,monospace;color:var(--muted)}}.finding{{border:1px solid var(--line);background:#fff;border-radius:9px;padding:22px 24px;margin-bottom:12px;break-inside:avoid}}
.finding-top{{display:flex;align-items:center;gap:10px;flex-wrap:wrap}}.severity{{font:700 10px ui-monospace,monospace;padding:4px 7px;border-radius:4px;letter-spacing:.04em}}.severity.high{{background:#f9e5e4;color:var(--red)}}.severity.medium{{background:#faf0d8;color:var(--amber)}}.severity.low{{background:#e8eee4;color:var(--green)}}
.rule{{font:11px ui-monospace,monospace;color:var(--muted)}}.server{{margin-left:auto;max-width:65%;overflow-wrap:anywhere;font:12px ui-monospace,monospace;color:var(--muted)}}
h3{{font-size:17px;letter-spacing:-.25px;margin:13px 0 7px}}.finding p{{margin:0 0 13px;color:var(--muted);font-size:14px}}code{{font:11px/1.6 ui-monospace,monospace;color:var(--muted);overflow-wrap:anywhere}}
.drift{{margin:0 0 28px}}.drift h2{{margin-bottom:15px}}.table-scroll{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;font-size:13px;text-align:left}}th,td{{padding:12px;border-bottom:1px solid var(--line);overflow-wrap:anywhere}}th{{font:11px ui-monospace,monospace;color:var(--muted)}}.change-kind{{font:11px ui-monospace,monospace;color:var(--green)}}
.muted{{font-size:12px;color:var(--muted)}}.empty{{background:white;border:1px solid var(--line);border-radius:10px;text-align:center;padding:40px 24px}}.empty-mark{{font-size:30px;color:var(--green)}}.empty p{{color:var(--muted)}}
footer{{border-top:1px solid var(--line);margin-top:34px;padding-top:18px;color:var(--muted);font-size:11px}}.digest{{font:10px ui-monospace,monospace;overflow-wrap:anywhere;margin-top:10px}}
@media(max-width:720px){{.top{{padding:16px 20px;flex-wrap:wrap}}main{{padding:30px 20px}}.hero{{display:block}}.edition{{text-align:left;margin-top:20px}}.stats{{grid-template-columns:repeat(2,1fr)}}.stat{{padding:17px 19px}}.stat:nth-child(2){{border-right:0}}.stat:nth-child(-n+2){{border-bottom:1px solid var(--line)}}.content{{grid-template-columns:1fr;gap:24px}}aside{{display:none}}.finding{{padding:19px}}.review-label{{display:none}}.server{{max-width:100%}}}}
@media print{{aside{{display:none}}.content{{display:block}}main{{padding:20px}}.top{{padding:12px}}}}
</style></head><body>
<header class="top"><div class="brand"><b>A/</b>Agent Config Audit</div><div class="offline">OFFLINE ANALYSIS · NO SERVER EXECUTION</div></header>
<main><section class="hero"><div><div class="eyebrow">MCP configuration review</div><h1>Know what you’re<br>about to run.</h1><p class="intro">A focused review of your agent’s server configuration. Inspect the findings, understand the scope, and decide what to trust.</p></div><div class="edition">REPORT / {report["mode"].upper()}<br>RULESET {__version__}<br>VALUES OMITTED</div></section>
<section class="stats" aria-label="Audit summary"><div class="stat"><span class="stat-label">Servers reviewed</span><span class="stat-value">{summary["servers"]:02d}</span><small>{summary["disabled"]} disabled · skipped</small></div><div class="stat high"><span class="stat-label">High priority</span><span class="stat-value">{summary["high"]:02d}</span><small>Review before launch</small></div><div class="stat medium"><span class="stat-label">Medium priority</span><span class="stat-value">{summary["medium"]:02d}</span><small>Check configuration</small></div><div class="stat"><span class="stat-label">Total findings</span><span class="stat-value">{summary["findings"]:02d}</span><small>Across enabled servers</small></div></section>
<div class="content"><aside><h2>Review workspace</h2><a class="nav-item" href="#findings">Findings <span aria-hidden="true">↗</span></a><div class="notes"><h2>Analysis scope</h2><p>Explicit configuration only.<br>No network requests.<br>No child processes.</p><p>Raw commands, arguments and credentials stay out of this report.</p><p>Static findings need human review. A clean report does not establish safety.</p></div></aside><div>{drift}<section id="findings" aria-labelledby="findings-title"><div class="section-heading"><h2 id="findings-title">Findings <span>{summary["findings"]:02d}</span></h2><span class="review-label">SORTED BY PRIORITY</span></div>{"".join(cards)}</section></div></div>
<footer>{escape(report["limitations"])}<div class="digest">INPUT SHA-256 / {report["input_sha256"]}</div></footer></main></body></html>"""


def render(report: dict[str, Any], format_name: str) -> str:
    if format_name == "html":
        return render_html(report)
    if format_name == "sarif":
        return render_sarif(report)
    if format_name == "json":
        return json.dumps(report, indent=2, ensure_ascii=True) + "\n"
    return render_text(report)
