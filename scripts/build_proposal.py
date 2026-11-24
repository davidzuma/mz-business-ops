#!/usr/bin/env python3
"""Build an MZtech proposal deck (HTML -> PDF) from a JSON content file.

Deterministic helper for the `proposal` skill. Stdlib only; renders the
16:9 slide deck with headless Chrome, matching the design system in
templates/proposal/deck.html (reference: examples/Ebro Fleet Control
Proposal.pdf).

Usage:
    python3 scripts/build_proposal.py --input data/proposals/<slug>/proposal.json --budget 3000
    python3 scripts/build_proposal.py --input <file.json> --outdir <dir> --no-pdf

The JSON content model is documented in templates/proposal/example.json.
Rich-text fields accept inline HTML (<strong>, <a>, arrows); plain fields
are escaped. Pricing totals are computed here, never by hand.

Language: meta.language = "es" (default) or "en". All fixed deck labels
follow it; content fields are authored in the chosen language.
Company defaults (confirmed by the owner): MZ Asesoría y Consultoría SL,
represented by David Zumaquero Mairena. The CIF/NIF is shown only when set;
when unknown it is omitted from the signature block (and flagged).
"""

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEMPLATE = REPO / "templates" / "proposal" / "deck.html"

COMPANY_DEFAULTS = {
    "brand": "MZtech",
    "legal_name": "MZ Asesoría y Consultoría SL",
    "signatory": "David Zumaquero Mairena",
}

STRINGS = {
    "es": {
        "proposal": "Propuesta", "contents": "Contenido", "design_demo": "Diseño y demo",
        "scope": "Alcance del servicio", "intro": "Introducción", "scope_project": "Alcance del proyecto",
        "scope_detail": "Alcance del proyecto (detalle)", "exclusions": "Exclusiones",
        "functional_detail": "Alcance funcional (detalle)", "architecture": "Arquitectura y despliegue",
        "security": "Usuarios y seguridad", "assumptions": "Supuestos y aclaraciones",
        "roles_flows": "Roles, flujos y datos", "planning": "Planificación y fases",
        "team": "Equipo y modelo operativo", "rhythm": "Ritmo y entregas", "collab": "Cómo colaboramos",
        "role": "Rol", "scope_col": "Ámbito", "pricing": "Estimación económica",
        "phase": "Fase", "concept": "Concepto", "duration": "Duración<br>estimada",
        "price": "Precio<br>(sin IVA)", "total": "Total", "payment": "Forma de pago",
        "validity_label": "Plazo de validez de la propuesta", "validity_suffix": "días naturales",
        "maintenance": "Mantenimiento post go-live", "maint_block": "Bolsa de mantenimiento y pequeñas mejoras",
        "maint_includes": "Qué incluye", "maint_amount": "Importe", "hours": "Horas",
        "amount": "Importe (sin IVA)", "costs": "Costes recurrentes y de terceros",
        "kind": "Tipo", "note": "Nota", "cases": "Proyectos y casos de éxito",
        "metrics_title": "Algunas métricas de nuestros sistemas",
        "sector": "Sector", "solution": "Solución", "duration_label": "Duración",
        "challenge": "RETO", "solution_k": "SOLUCIÓN", "impact": "IMPACTO",
        "legal": "Bases de la prestación del servicio", "acceptance": "Aceptación de la propuesta",
        "acceptance_text": "{client} confirma su aceptación de los términos expuestos en esta propuesta y autoriza a {company} a iniciar el servicio descrito.",
        "represented": "Representado por:", "sign_line": "Nombre, cargo y firma",
        "pending": "[PENDIENTE DE CONFIRMAR]",
        "tagline": ["Ingeniería de Software", "que convierte ideas en sistemas"],
    },
    "en": {
        "proposal": "Proposal", "contents": "Contents", "design_demo": "Design & demo",
        "scope": "Service scope", "intro": "Introduction", "scope_project": "Project scope",
        "scope_detail": "Project scope (detail)", "exclusions": "Exclusions",
        "functional_detail": "Functional scope (detail)", "architecture": "Architecture & deployment",
        "security": "Users & security", "assumptions": "Assumptions & clarifications",
        "roles_flows": "Roles, flows & data", "planning": "Planning & phases",
        "team": "Team & operating model", "rhythm": "Rhythm & deliverables", "collab": "How we collaborate",
        "role": "Role", "scope_col": "Scope", "pricing": "Pricing",
        "phase": "Phase", "concept": "Item", "duration": "Estimated<br>duration",
        "price": "Price<br>(excl. VAT)", "total": "Total", "payment": "Payment terms",
        "validity_label": "Proposal validity", "validity_suffix": "calendar days",
        "maintenance": "Post go-live maintenance", "maint_block": "Maintenance & small improvements retainer",
        "maint_includes": "What's included", "maint_amount": "Amount", "hours": "Hours",
        "amount": "Amount (excl. VAT)", "costs": "Recurring & third-party costs",
        "kind": "Type", "note": "Note", "cases": "Projects & success stories",
        "metrics_title": "Some metrics from our systems",
        "sector": "Sector", "solution": "Solution", "duration_label": "Duration",
        "challenge": "CHALLENGE", "solution_k": "SOLUTION", "impact": "IMPACT",
        "legal": "Terms of service", "acceptance": "Proposal acceptance",
        "acceptance_text": "{client} confirms acceptance of the terms set out in this proposal and authorises {company} to begin the service described.",
        "represented": "Represented by:", "sign_line": "Name, title & signature",
        "pending": "[TO BE CONFIRMED]",
        "tagline": ["Software Engineering", "that turns ideas into systems"],
    },
}

CHROME_CANDIDATES = [
    os.environ.get("CHROME_PATH", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    shutil.which("chromium") or "",
    shutil.which("google-chrome") or "",
    shutil.which("google-chrome-stable") or "",
]


def esc(value):
    return html.escape(str(value), quote=True)


def eur(value):
    """Format a number as Spanish-style euros: 14580 -> '14.580€'."""
    value = float(value)
    s = f"{value:,.0f}" if value.is_integer() else f"{value:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".") + "€"


def slugify(text):
    text = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")
    return text or "proposal"


class Builder:
    def __init__(self, data, outdir):
        self.data = data
        self.meta = data.get("meta", {})
        self.lang = self.meta.get("language", "es")
        if self.lang not in STRINGS:
            self.lang = "es"
        self.S = STRINGS[self.lang]
        self.company = dict(COMPANY_DEFAULTS)
        for k, v in (self.meta.get("company") or {}).items():
            if v:
                self.company[k] = v
        self.outdir = Path(outdir)
        self.assets = self.outdir / "assets"
        self.slides = []
        self.toc = []
        self.warnings = []
        self.section_no = 0
        self.sub_no = 0

    # ---------- helpers ----------
    def warn(self, msg):
        self.warnings.append(msg)

    def asset(self, src):
        if not src:
            return None
        if str(src).startswith(("http://", "https://")):
            self.warn(f"Remote image used (needs network at render time): {src}")
            return src
        path = Path(src)
        if not path.is_absolute():
            path = REPO / path
        if not path.exists():
            self.warn(f"Image not found, skipped: {src}")
            return None
        dest = self.assets / path.name
        shutil.copyfile(path, dest)
        return f"assets/{path.name}"

    def footer(self, page):
        year = self.meta.get("year", date.today().year)
        brand = self.company.get("brand", "MZtech")
        title = self.proposal_title()
        return (
            f'<div class="footer"><span>{esc(year)} · {esc(brand)}</span>'
            f'<span>{self.S["proposal"]}: {esc(title)} · {page} / {len(self.slides)}</span></div>'
        )

    def proposal_title(self):
        return self.meta.get("title") or (
            f"{self.meta.get('client_short', 'Cliente')} - {self.meta.get('project', 'Proyecto')}"
        )

    def add_slide(self, inner, cls=""):
        self.slides.append(f'<section class="slide {cls}">{inner}</section>')

    def sec_head(self, number, title):
        return (
            f'<div class="sec-head"><span class="sec-num">{esc(number)}.</span>'
            f'<span class="sec-title">{esc(title)}</span></div><div class="sec-rule"></div>'
        )

    def new_section(self, key, title):
        self.section_no += 1
        self.sub_no = 0
        return self.section_no

    def sub_number(self):
        self.sub_no += 1
        return f"{self.section_no}.{self.sub_no}"

    def bullets(self, items):
        if not items:
            return ""
        return '<ul class="bullets">' + "".join(f"<li>{i}</li>" for i in items) + "</ul>"

    def blocks(self, groups):
        out = []
        for g in groups or []:
            out.append(f'<h3 class="block">{esc(g["heading"])}</h3>')
            out.append(self.bullets(g.get("items", [])))
            if g.get("note"):
                out.append(f'<p class="note">{g["note"]}</p>')
        return "".join(out)

    # ---------- slides ----------
    def build_cover(self):
        # No logo by default (brand rule): typographic brand name only.
        brand = self.company.get("brand", "MZtech")
        logo = self.asset(self.meta["logo"]) if self.meta.get("logo") else None
        tagline = self.meta.get("tagline") or self.S["tagline"]
        mark = (
            f'<img class="cover-logo" src="{logo}" alt="{esc(brand)}">'
            if logo
            else f'<div class="cover-brand">{esc(brand)}</div>'
        )
        inner = (
            f'<div class="cover-center">{mark}'
            f'<div class="cover-tagline">{esc(tagline[0])} <span class="t2">{esc(tagline[1])}</span></div></div>'
            f'<div class="cover-title">{self.S["proposal"]}: {esc(self.proposal_title())}</div>'
        )
        self.add_slide(inner, cls="cover")

    def build_toc_placeholder(self):
        self.toc_index = len(self.slides)
        self.add_slide("")

    def build_demo(self):
        demo = self.data.get("demo") or {}
        slides = demo.get("slides") or []
        if not slides:
            return
        project = self.meta.get("project", "")
        section_title = demo.get("section_title") or f'{self.S["design_demo"]} — {project}'
        num = self.new_section("demo", section_title)
        self.toc.append((0, str(num), section_title, len(self.slides) + 1))
        for i, s in enumerate(slides):
            if i == 0:
                head = self.sec_head(num, section_title)
            else:
                n = self.sub_number()
                head = self.sec_head(n, s.get("title", f"Demo {i + 1}"))
                self.toc.append((1, n, s.get("title", f"Demo {i + 1}"), len(self.slides) + 1))
            img = self.asset(s.get("image"))
            visual = f'<div class="visual"><img src="{img}" alt="{esc(s.get("title", "Demo"))}"></div>' if img else ""
            copy = [f'<h3>{esc(s.get("heading") or s.get("title", ""))}</h3>']
            if s.get("note"):
                copy.append(f'<p><strong>{esc(s["note"])}</strong></p>')
            if s.get("caption"):
                copy.append(f'<p>{s["caption"]}</p>')
            if s.get("url"):
                label = s.get("url_label") or ("this link" if self.lang == "en" else "este enlace")
                copy.append(f'<p>{"The interactive demo is at" if self.lang == "en" else "La demo interactiva está en"} <a href="{esc(s["url"])}">{esc(label)}</a>.</p>')
            solo = "" if img else " solo"
            self.add_slide(head + f'<div class="split">{visual}<div class="copy{solo}">{"".join(copy)}</div></div>')

    def build_scope(self):
        scope = self.data.get("scope") or {}
        if not scope:
            return
        S = self.S
        num = self.new_section("scope", S["scope"])
        self.toc.append((0, str(num), S["scope"], len(self.slides) + 1))
        intro = "".join(f"<p>{p}</p>" for p in scope.get("intro", []))
        inner = self.sec_head(num, S["scope"])
        if intro:
            inner += f'<h3 class="block">{S["intro"]}</h3>' + intro
        if scope.get("items"):
            inner += f'<h3 class="block">{S["scope_project"]}</h3>' + self.bullets(scope["items"])
        self.add_slide(inner)

        if scope.get("exclusions"):
            n = self.sub_number()
            self.toc.append((1, n, S["scope_detail"], len(self.slides) + 1))
            self.add_slide(self.sec_head(n, S["scope_detail"]) + f'<h3 class="block">{S["exclusions"]}</h3>' + self.bullets(scope["exclusions"]))

        for key, sub_title in [
            ("functional", S["functional_detail"]),
            ("architecture", S["architecture"]),
            ("security", S["security"]),
        ]:
            groups = self.data.get(key) or scope.get(key)
            if groups:
                n = self.sub_number()
                self.toc.append((1, n, sub_title, len(self.slides) + 1))
                self.add_slide(self.sec_head(n, sub_title) + self.blocks(groups))

        if self.data.get("assumptions") or scope.get("assumptions"):
            items = self.data.get("assumptions") or scope.get("assumptions")
            n = self.sub_number()
            self.toc.append((1, n, S["assumptions"], len(self.slides) + 1))
            rows = [f'<strong>{esc(a["id"])}</strong> — {a["html"]}' for a in items]
            self.add_slide(self.sec_head(n, S["assumptions"]) + f'<h3 class="block">{S["roles_flows"]}</h3>' + self.bullets(rows))

    def build_planning(self):
        plan = self.data.get("planning")
        if not plan:
            return
        S = self.S
        num = self.new_section("planning", S["planning"])
        self.toc.append((0, str(num), S["planning"], len(self.slides) + 1))
        inner = self.sec_head(num, S["planning"])
        if plan.get("summary"):
            inner += f'<p>{plan["summary"]}</p>'
        if plan.get("phases"):
            inner += '<ul class="bullets" style="margin-top:22px">' + "".join(
                f'<li><strong>{esc(p["label"])}:</strong> {p["html"]}</li>' for p in plan["phases"]
            ) + "</ul>"
        g = plan.get("gantt")
        if g:
            inner += self.gantt(g)
        self.add_slide(inner)

    def gantt(self, g):
        weeks = int(g.get("weeks", 15))
        months = g.get("months") or [{"label": f"Mes {i + 1}", "span": 4} for i in range((weeks + 3) // 4)]
        cols = f"grid-template-columns: 330px repeat({weeks}, 1fr);"
        out = ['<div class="gantt">']
        row = f'<div class="gantt-grid" style="{cols}"><div style="grid-column:1;grid-row:1"></div>'
        col = 2
        for m in months:
            span = int(m["span"])
            row += f'<div class="month" style="grid-column:{col}/{col + span};grid-row:1">{esc(m["label"])}</div>'
            col += span
        out.append(row + "</div>")
        row = f'<div class="gantt-grid" style="{cols}"><div></div>'
        for w in range(1, weeks + 1):
            row += f'<div class="week" style="grid-column:{w + 1};grid-row:1">S{w}</div>'
        out.append(row + "</div>")
        for bar in g.get("bars", []):
            start, end = int(bar["start"]), int(bar["end"])
            if not (1 <= start <= end <= weeks):
                self.warn(f"Gantt bar out of range (weeks={weeks}): {bar.get('label')} {start}-{end}")
                continue
            row = f'<div class="gantt-grid" style="{cols}">'
            row += f'<div class="row-label" style="grid-column:1;grid-row:1">{esc(bar["label"])}</div>'
            for w in range(1, weeks + 1):
                row += f'<div class="cell" style="grid-column:{w + 1};grid-row:1"></div>'
            color = bar.get("color", "cyan")
            row += f'<div class="bar {esc(color)}" style="grid-column:{start + 1}/{end + 2};grid-row:1"></div>'
            out.append(row + "</div>")
        out.append("</div>")
        return "".join(out)

    def build_team(self):
        team = self.data.get("team")
        if not team:
            return
        S = self.S
        num = self.new_section("team", S["team"])
        self.toc.append((0, str(num), S["team"], len(self.slides) + 1))
        inner = self.sec_head(num, S["team"])
        if team.get("rows"):
            inner += f'<table class="tbl"><tr><th style="width:420px">{S["role"]}</th><th>{S["scope_col"]}</th></tr>'
            for r in team["rows"]:
                inner += f'<tr><td><strong>{esc(r["role"])}</strong></td><td>{esc(r["scope"])}</td></tr>'
            inner += "</table>"
        if team.get("rhythm"):
            inner += f'<h3 class="block">{S["rhythm"]}</h3><p>' + team["rhythm"] + "</p>"
        if team.get("collab"):
            inner += f'<h3 class="block">{S["collab"]}</h3>' + self.bullets(team["collab"])
        self.add_slide(inner)

    def build_pricing(self):
        pricing = self.data.get("pricing")
        if not pricing or not pricing.get("items"):
            return
        S = self.S
        num = self.new_section("pricing", S["pricing"])
        self.toc.append((0, str(num), S["pricing"], len(self.slides) + 1))
        total = 0.0
        rows = []
        for it in pricing["items"]:
            amount = float(it["amount"])
            total += amount
            concept = f'<span class="concept">{esc(it["concept"])}</span>'
            if it.get("detail"):
                concept += f' — {esc(it["detail"])}'
            rows.append(
                f'<tr><td>{esc(it.get("phase", ""))}</td><td>{concept}</td>'
                f'<td class="num">{esc(it.get("duration", ""))}</td><td class="num">{eur(amount)}</td></tr>'
            )
        inner = self.sec_head(num, S["pricing"])
        inner += (
            f'<table class="tbl"><tr><th style="width:150px">{S["phase"]}</th><th>{S["concept"]}</th>'
            f'<th class="num" style="width:190px">{S["duration"]}</th>'
            f'<th class="num" style="width:180px">{S["price"]}</th></tr>'
            + "".join(rows)
            + f'<tr class="total"><td>{S["total"]}</td><td></td><td></td><td class="num">{eur(total)}</td></tr></table>'
        )
        terms = ['<div class="terms">']
        if self.meta.get("payment_terms"):
            terms.append(f'<p><strong>{S["payment"]}:</strong> {esc(self.meta["payment_terms"])}</p>')
        validity = self.meta.get("validity_days", 30)
        terms.append(f'<p><strong>{S["validity_label"]}:</strong> {esc(validity)} {S["validity_suffix"]}.</p>')
        if self.meta.get("overrun_clause"):
            terms.append(f'<p class="fine">{esc(self.meta["overrun_clause"])}</p>')
        terms.append("</div>")
        self.add_slide(inner + "".join(terms))
        self.pricing_total = total

        maint = self.data.get("maintenance")
        if maint:
            n = self.sub_number()
            self.toc.append((1, n, S["maintenance"], len(self.slides) + 1))
            m = self.sec_head(n, S["maintenance"])
            m += f'<h3 class="block">{S["maint_block"]}</h3>'
            if maint.get("intro"):
                m += f'<p>{maint["intro"]}</p>'
            if maint.get("includes"):
                m += f'<h3 class="block">{S["maint_includes"]}</h3>' + self.bullets(maint["includes"])
            if maint.get("items"):
                m += f'<h3 class="block">{S["maint_amount"]}</h3><table class="tbl"><tr><th>{S["concept"]}</th><th>{S["hours"]}</th><th class="num">{S["amount"]}</th></tr>'
                for it in maint["items"]:
                    amount = it["amount"]
                    amount_s = eur(amount) if isinstance(amount, (int, float)) else esc(amount)
                    m += f'<tr><td>{esc(it["concept"])}</td><td>{esc(it.get("hours", ""))}</td><td class="num">{amount_s}</td></tr>'
                m += "</table>"
            self.add_slide(m)

        costs = self.data.get("costs")
        if costs and costs.get("items"):
            n = self.sub_number()
            self.toc.append((1, n, S["costs"], len(self.slides) + 1))
            c = self.sec_head(n, S["costs"])
            if costs.get("intro"):
                c += f'<p>{costs["intro"]}</p>'
            c += (f'<table class="tbl" style="margin-top:24px"><tr><th>{S["concept"]}</th><th style="width:220px">{S["kind"]}</th>'
                  f'<th class="num" style="width:240px">{S["amount"]}</th><th style="width:380px">{S["note"]}</th></tr>')
            for it in costs["items"]:
                amount = it["amount"]
                amount_s = eur(amount) if isinstance(amount, (int, float)) else esc(amount)
                c += (f'<tr><td><span class="concept">{esc(it["concept"])}</span></td>'
                      f'<td>{esc(it.get("kind", ""))}</td><td class="num">{amount_s}</td>'
                      f'<td class="note">{esc(it.get("note", ""))}</td></tr>')
            c += "</table>"
            if costs.get("note"):
                c += f'<p class="note" style="margin-top:20px">{costs["note"]}</p>'
            self.add_slide(c)

    def build_cases(self):
        metrics = self.data.get("metrics") or []
        cases = self.data.get("cases") or []
        if not metrics and not cases:
            return
        S = self.S
        num = self.new_section("cases", S["cases"])
        self.toc.append((0, str(num), S["cases"], len(self.slides) + 1))
        if metrics:
            inner = self.sec_head(num, S["cases"])
            inner += f'<h2 class="slide-sub">{S["metrics_title"]}</h2>'
            inner += '<div class="metrics">' + "".join(
                f'<div class="metric"><div class="cap">{m["caption"]}</div><div class="big">{m["big"]}</div></div>'
                for m in metrics
            ) + "</div>"
            self.add_slide(inner)
        for case in cases:
            inner = self.sec_head(num, S["cases"])
            inner += f'<h2 class="slide-sub">{esc(case["name"])}</h2>'
            left = ['<div class="copy">']
            logo = self.asset(case.get("logo"))
            if logo:
                left.append(f'<img class="client-logo" src="{logo}" alt="">')
            left.append(f'<p class="meta"><strong>{S["sector"]}:</strong> {esc(case.get("sector", ""))}</p>')
            left.append(f'<p class="meta"><strong>{S["solution"]}:</strong> {esc(case.get("solution", ""))}</p>')
            left.append(f'<p class="meta"><strong>{S["duration_label"]}:</strong> {esc(case.get("duration", ""))}</p>')
            for key, label in [("challenge", S["challenge"]), ("solution_detail", S["solution_k"]), ("impact", S["impact"])]:
                if case.get(key):
                    left.append(f'<div class="case-block"><div class="k">{label}</div><p>{esc(case[key])}</p></div>')
            left.append("</div>")
            img = self.asset(case.get("image"))
            visual = f'<div class="visual"><img src="{img}" alt=""></div>' if img else ""
            inner += f'<div class="split case">{"".join(left)}{visual}</div>'
            self.add_slide(inner)

    def build_legal(self):
        legal = self.data.get("legal")
        if not legal:
            return
        S = self.S
        num = self.new_section("legal", S["legal"])
        self.toc.append((0, str(num), S["legal"], len(self.slides) + 1))
        legal_name = self.company.get("legal_name") or S["pending"]
        tax_id = self.company.get("tax_id") or ""
        signatory = self.company.get("signatory") or S["pending"]
        if not tax_id:
            self.warn("Company CIF/NIF not provided; omitted from the signature block.")
        entity = esc(legal_name) + (f" — {esc(tax_id)}" if tax_id else "")
        items = [f'<strong>{esc(i["title"])}</strong>: {i["html"]}' for i in legal.get("items", [])]
        inner = self.sec_head(num, S["legal"]) + self.bullets(items)
        client_legal = self.meta.get("client_legal") or self.meta.get("client_short") or S["pending"]
        acceptance = legal.get("acceptance") or S["acceptance_text"].format(client=esc(client_legal), company=esc(legal_name))
        inner += (
            f'<div class="accept"><h2>{S["acceptance"]}</h2><p>{acceptance}</p>'
            f'<div class="sign-cols">'
            f'<div class="sign-col"><div class="entity">{esc(client_legal)}</div>'
            f'<div class="rep">{S["represented"]}</div><div class="name">&nbsp;</div><div class="line">{S["sign_line"]}</div></div>'
            f'<div class="sign-col"><div class="entity">{entity}</div>'
            f'<div class="rep">{S["represented"]}</div><div class="name">{esc(signatory)}</div><div class="line">{S["sign_line"]}</div></div>'
            f"</div></div>"
        )
        self.add_slide(inner)

    def finalize_toc(self):
        rows = []
        for level, number, title, page in self.toc:
            cls = "toc-row sub" if level else "toc-row"
            rows.append(f'<div class="{cls}"><span class="n">{esc(number)}</span><span class="t">{esc(title)}</span><span class="pg">{page}</span></div>')
        inner = self.sec_head(0, self.S["contents"]) + f'<div class="toc">{"".join(rows)}</div>'
        self.slides[self.toc_index] = f'<section class="slide">{inner}</section>'

    def render_html(self):
        self.build_cover()
        self.build_toc_placeholder()
        self.build_demo()
        self.build_scope()
        self.build_planning()
        self.build_team()
        self.build_pricing()
        self.build_cases()
        self.build_legal()
        self.finalize_toc()
        for i in range(1, len(self.slides)):
            self.slides[i] = self.slides[i].replace("</section>", self.footer(i + 1) + "</section>")
        fonts_css = (TEMPLATE.parent / "fonts" / "fonts.css").read_text()
        fonts_dest = self.outdir / "fonts"
        fonts_dest.mkdir(exist_ok=True)
        for f in (TEMPLATE.parent / "fonts").glob("*.woff2"):
            shutil.copyfile(f, fonts_dest / f.name)
        template = TEMPLATE.read_text()
        return (
            template.replace("{{TITLE}}", esc(self.proposal_title()))
            .replace("{{FONTS}}", fonts_css)
            .replace("{{SLIDES}}", "\n".join(self.slides))
        )

    def check_placeholders(self, html_text):
        for match in re.finditer(r"(TODO|PENDIENTE|TO BE CONFIRMED)[^<]*", html_text):
            self.warn(f"Unresolved placeholder in deck: {match.group(0)[:80]}")


def find_chrome():
    for candidate in CHROME_CANDIDATES:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def render_pdf(html_path, pdf_path):
    chrome = find_chrome()
    if not chrome:
        print("WARNING: Chrome/Chromium not found; PDF not rendered. Set CHROME_PATH.", file=sys.stderr)
        return False
    cmd = [
        chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--no-pdf-header-footer", "--virtual-time-budget=15000",
        "--run-all-compositor-stages-before-draw",
        f"--print-to-pdf={pdf_path}", html_path.as_uri(),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if not pdf_path.exists():
        print(result.stderr[-2000:], file=sys.stderr)
        raise RuntimeError("Headless Chrome did not produce a PDF")
    return True


def verify_pages(pdf_path, expected):
    info = shutil.which("pdfinfo")
    if not info:
        return None
    out = subprocess.run([info, str(pdf_path)], capture_output=True, text=True).stdout
    m = re.search(r"Pages:\s+(\d+)", out)
    return int(m.group(1)) if m else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Proposal content JSON")
    parser.add_argument("--outdir", help="Output directory (default data/proposals/<slug>)")
    parser.add_argument("--no-pdf", action="store_true", help="Only write the HTML deck")
    parser.add_argument("--budget", type=float, help="Expected total (excl. VAT); flags a mismatch with the pricing table")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text())
    meta = data.get("meta", {})
    if not meta.get("project"):
        print("WARNING: meta.project is empty; set a project name.", file=sys.stderr)
    if not meta.get("client_short") and not meta.get("title"):
        print("WARNING: meta.client_short and meta.title are empty; the cover needs a proposal title.", file=sys.stderr)
    title = meta.get("title") or f"{meta.get('client_short', 'Cliente')} - {meta.get('project', 'Proyecto')}"
    outdir = Path(args.outdir) if args.outdir else REPO / "data" / "proposals" / slugify(title)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "assets").mkdir(exist_ok=True)

    builder = Builder(data, outdir)
    html_text = builder.render_html()
    builder.check_placeholders(html_text)
    if not (data.get("demo") or {}).get("slides"):
        builder.warn(
            "NO DESIGN/DEMO SLIDES: every proposal must include project-specific designs. "
            "Run the `poc` skill first and add its screenshots + URL to demo.slides."
        )
    if args.budget is not None and getattr(builder, "pricing_total", None) is not None:
        if abs(builder.pricing_total - args.budget) > 0.005:
            builder.warn(
                f"Pricing total {eur(builder.pricing_total)} != budget {eur(args.budget)}. "
                "Adjust pricing.items amounts so they sum exactly to the budget."
            )
    html_path = outdir / "proposal.html"
    html_path.write_text(html_text)
    print(f"HTML deck: {html_path} ({len(builder.slides)} slides)")

    if not args.no_pdf:
        pdf_path = outdir / "proposal.pdf"
        if render_pdf(html_path, pdf_path):
            pages = verify_pages(pdf_path, len(builder.slides))
            print(f"PDF: {pdf_path} ({pages} pages)")
            if pages is not None and pages != len(builder.slides):
                builder.warn(
                    f"Page count {pages} != {len(builder.slides)} slides: a slide overflowed. "
                    "Trim content or split the slide, then rebuild."
                )

    if getattr(builder, "pricing_total", None) is not None:
        print(f"Pricing total (excl. VAT): {eur(builder.pricing_total)}")
    if builder.warnings:
        print("\nFLAGS FOR HUMAN REVIEW:")
        for w in sorted(set(builder.warnings)):
            print(f"  - {w}")
    else:
        print("No flags.")


if __name__ == "__main__":
    main()
