#!/usr/bin/env python3
"""Build an anonymized MZtech talent profile deck from JSON and local portraits."""

from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = ROOT / "templates" / "proposal" / "fonts"
LOGO = ROOT / "media" / "mztechlogo.png"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".svg"}


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def find_chrome() -> str | None:
    candidates = [
        os.environ.get("CHROME_PATH"),
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    return next((candidate for candidate in candidates if candidate and Path(candidate).is_file()), None)


def image_path(base: Path, raw: str) -> Path:
    path = (base / raw).resolve()
    if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
        raise ValueError(f"Portrait is missing or unsupported: {raw}")
    return path


def render_list(values: list[str], class_name: str) -> str:
    return "".join(f'<span class="{class_name}">{esc(item)}</span>' for item in values if item)


def build(data: dict, input_path: Path, output_dir: Path) -> tuple[Path, Path]:
    title = esc(data.get("title") or "Talent profiles")
    slogan = esc(data.get("slogan") or "Simple, reliable technology")
    profiles = data.get("profiles") or []
    if not profiles:
        raise ValueError("profiles must contain at least one profile")

    assets_dir = output_dir / "assets"
    fonts_out = output_dir / "fonts"
    assets_dir.mkdir(parents=True, exist_ok=True)
    fonts_out.mkdir(parents=True, exist_ok=True)
    logo_out = assets_dir / "mztechlogo.png"
    shutil.copy2(LOGO, logo_out)
    neutral_badge = assets_dir / "cert-neutral.svg"
    neutral_badge.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96">
        <path fill="#e0f3fa" stroke="#178dc2" stroke-width="4"
          d="M48 5 59 11 72 10 78 22 89 30 85 44 91 56 81 67 79 81 65 84 56 92 43 86 29 90 22 78 10 72 13 58 5 47 12 35 10 22 24 17 32 6Z"/>
        <path fill="none" stroke="#282769" stroke-width="4" stroke-linecap="round"
          stroke-linejoin="round" d="M31 35h34M31 47h34M31 59h22"/>
        </svg>""",
        encoding="utf-8",
    )
    for font in FONT_DIR.glob("*.woff2"):
        shutil.copy2(font, fonts_out / font.name)

    cover = f"""
    <section class="slide cover">
      <div class="cover-content">
        <img class="brand-logo" src="assets/mztechlogo.png" alt="MZtech">
        <p class="slogan">{slogan}</p>
        <div class="cover-rule"></div>
        <h1>{title}</h1>
        <p class="cover-sub">Selected talent profiles</p>
        <div class="site">mztech.dev</div>
      </div>
    </section>
    """

    slides: list[str] = [cover]
    for index, profile in enumerate(profiles, start=1):
        role = esc(profile.get("role"))
        summary = esc(profile.get("summary"))
        positioning = esc(profile.get("positioning"))
        daily_rate = profile.get("daily_rate")
        rate_html = (
            f'<div class="rate-card"><span>DAILY RATE</span><strong>€{esc(daily_rate)}</strong><small>/ day</small></div>'
            if daily_rate not in (None, "")
            else ""
        )
        photo = image_path(input_path.parent, str(profile.get("photo") or ""))
        photo_out = assets_dir / f"profile-{index:02d}{photo.suffix.lower()}"
        if photo.resolve() != photo_out.resolve():
            shutil.copy2(photo, photo_out)
        jobs = profile.get("experience") or []
        education = profile.get("education") or []
        skills = profile.get("skills") or []
        certifications = profile.get("certifications") or []
        badges = profile.get("certification_badges") or []

        job_html = []
        for job in jobs:
            bullets = "".join(
                f'<li><span class="bullet"></span><span>{esc(item)}</span></li>'
                for item in job.get("highlights", [])
            )
            job_html.append(f"""
              <article class="job">
                <div class="job-heading">
                  <h3>{esc(job.get("company"))}</h3>
                  <span class="period">{esc(job.get("period"))}</span>
                </div>
                <p class="job-title">{esc(job.get("title"))}</p>
                <ul>{bullets}</ul>
              </article>
            """)

        education_html = "".join(
            f'<div class="education-item"><h3>{esc(item.get("degree"))}</h3>'
            f'<p>{esc(item.get("school"))}'
            f'{" · " + esc(item.get("period")) if item.get("period") else ""}</p></div>'
            for item in education
        )
        badge_labels = {
            str(badge.get("label", "")).strip().casefold() for badge in badges
        }
        certification_html = "".join(
            f'<div class="cert-badge"><img src="assets/cert-neutral.svg" '
            f'alt="Certification emblem"><span>{esc(certification)}</span></div>'
            for certification in certifications
            if str(certification).strip().casefold() not in badge_labels
        )
        badge_html = []
        for badge_index, badge in enumerate(badges, start=1):
            badge_image = image_path(input_path.parent, str(badge.get("image") or ""))
            badge_out = assets_dir / f"cert-{index:02d}-{badge_index:02d}{badge_image.suffix.lower()}"
            if badge_image.resolve() != badge_out.resolve():
                shutil.copy2(badge_image, badge_out)
            badge_html.append(
                f'<div class="cert-badge{" cert-badge-wide" if badge.get("wide") else ""}">'
                f'<img src="{esc(badge_out.relative_to(output_dir).as_posix())}" '
                f'alt="{esc(badge.get("label"))}"><span>{esc(badge.get("label"))}</span></div>'
            )

        slides.append(f"""
        <section class="slide profile">
          <div class="profile-top">
            <span class="eyebrow">TALENT PROFILE <b>{index:02d}</b></span>
            <span class="wordmark">MZ<span>tech</span></span>
          </div>
          <div class="profile-grid">
            <div class="left-column">
              <div class="portrait-wrap">
                <img class="portrait" src="{esc(photo_out.relative_to(output_dir).as_posix())}" alt="Candidate portrait">
              </div>
              <section class="left-section summary-section">
                <h2>Summary</h2><p>{summary}</p>
              </section>
              <section class="left-section">
                <h2>Technical toolkit</h2>
                <div class="chips">{render_list(skills, "chip")}</div>
              </section>
              <section class="left-section cert-section">
                <h2>Certifications</h2>
                <div class="certifications">{''.join(badge_html)}{certification_html}</div>
              </section>
            </div>
            <div class="right-column">
              <div class="profile-heading">
                <div>
                  <div class="accent-line"></div>
                  <h1>{role}</h1>
                  <p class="positioning">{positioning}</p>
                </div>
                {rate_html}
              </div>
              <section class="right-section experience-section">
                <h2>Experience</h2>
                {''.join(job_html)}
              </section>
              <section class="right-section education-section">
                <h2>Education</h2>
                <div class="education-list">{education_html}</div>
              </section>
            </div>
          </div>
          <div class="profile-footer"><span>mztech.dev · {slogan}</span><span>{index + 1:02d} / {len(profiles) + 1:02d}</span></div>
        </section>
        """)

    html_doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{title}</title>
<style>
@font-face{{font-family:BeVietnam;src:url('fonts/BeVietnamPro-400.woff2') format('woff2');font-weight:400}}
@font-face{{font-family:BeVietnam;src:url('fonts/BeVietnamPro-500.woff2') format('woff2');font-weight:500}}
@font-face{{font-family:BeVietnam;src:url('fonts/BeVietnamPro-600.woff2') format('woff2');font-weight:600}}
@font-face{{font-family:Poppins;src:url('fonts/Poppins-500.woff2') format('woff2');font-weight:500}}
@font-face{{font-family:Poppins;src:url('fonts/Poppins-600.woff2') format('woff2');font-weight:600}}
:root{{--navy:#282769;--blue:#1a407e;--cyan:#178dc2;--sky:#16add8;--ink:#101038;--muted:#596580;--pale:#eef3fa;--line:#d7e0ef}}
*{{box-sizing:border-box;margin:0;padding:0}}
@page{{size:1920px 1080px;margin:0}}
html,body{{font-family:BeVietnam,Arial,sans-serif;color:var(--ink);background:var(--pale)}}
.slide{{width:1920px;height:1080px;position:relative;overflow:hidden;page-break-after:always;break-after:page;background:linear-gradient(135deg,#f8fbff 0%,#eaf1fa 100%)}}
.slide:last-child{{page-break-after:auto;break-after:auto}}
.cover{{background:linear-gradient(135deg,#f8fbff 0%,#eaf1fa 100%)}}
.cover-content{{position:absolute;inset:150px 0 0;text-align:center;display:flex;align-items:center;flex-direction:column}}
.brand-logo{{width:210px;height:210px;object-fit:contain}}
.slogan{{font:500 28px Poppins,sans-serif;letter-spacing:.02em;color:var(--blue);margin-top:20px}}
.cover-rule{{width:84px;height:4px;border-radius:4px;background:var(--cyan);margin:70px 0 30px}}
.cover h1{{font:600 60px Poppins,sans-serif;letter-spacing:-.03em;color:var(--navy)}}
.cover-sub{{font-size:25px;color:var(--muted);margin-top:14px}}
.site{{font:500 18px Poppins,sans-serif;letter-spacing:.13em;color:var(--cyan);margin-top:34px}}
.profile{{padding:48px 78px 78px}}
.profile-top{{height:44px;display:flex;align-items:center;justify-content:space-between}}
.eyebrow{{font:600 18px Poppins,sans-serif;letter-spacing:.12em;color:var(--muted)}}
.eyebrow b{{color:var(--cyan);margin-left:9px}}
.wordmark{{font:600 27px Poppins,sans-serif;color:var(--navy)}}
.wordmark span{{color:var(--cyan)}}
.profile-grid{{height:850px;display:grid;grid-template-columns:620px 1fr;gap:72px;margin-top:18px;align-items:start}}
.left-column{{display:flex;flex-direction:column;gap:16px;min-width:0}}
.portrait-wrap{{width:330px;height:250px;margin:0 auto;border-radius:20px;overflow:hidden;background:#e2eaf5;box-shadow:0 15px 35px rgba(16,16,56,.13)}}
.portrait{{width:100%;height:100%;object-fit:contain;object-position:center;display:block}}
.left-section h2,.right-section>h2{{font:600 16px Poppins,sans-serif;letter-spacing:.09em;text-transform:uppercase;color:var(--navy);margin-bottom:8px}}
.summary-section p{{font-size:17px;line-height:1.45;color:#38425a}}
.chips{{display:flex;flex-wrap:wrap;gap:7px}}
.chip,.credential{{font-size:14px;line-height:1.1;padding:7px 10px;border-radius:7px}}
.chip{{background:#fff;border:1px solid var(--line);color:#27335a}}
.credential{{background:#e0f3fa;color:#124d72;font-weight:600}}
.certifications{{display:flex;flex-wrap:wrap;align-items:flex-start;gap:8px}}
.cert-badge{{width:184px;min-height:92px;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;text-align:center}}
.cert-badge img{{height:68px;width:76px;object-fit:contain}}
.cert-badge-wide img{{height:52px;width:132px}}
.cert-badge span{{font-size:12px;line-height:1.15;color:#33415e;margin-top:3px}}
.right-column{{min-width:0;padding-top:2px}}
.profile-heading{{display:flex;justify-content:space-between;align-items:center;gap:24px;border-bottom:1px solid var(--line);padding-bottom:18px;margin-bottom:19px}}
.accent-line{{width:58px;height:4px;border-radius:3px;background:linear-gradient(90deg,var(--cyan),var(--sky));margin-bottom:13px}}
.profile h1{{font:600 43px/1.12 Poppins,sans-serif;letter-spacing:-.025em;color:var(--navy)}}
.positioning{{font:500 18px/1.4 BeVietnam,sans-serif;color:var(--cyan);margin-top:8px}}
.rate-card{{min-width:185px;border-radius:14px;padding:16px 20px;background:#fff;border:1px solid var(--line);text-align:center;box-shadow:0 8px 20px rgba(16,16,56,.06)}}
.rate-card span{{display:block;font:600 11px Poppins,sans-serif;letter-spacing:.12em;color:var(--muted)}}
.rate-card strong{{font:600 32px Poppins,sans-serif;color:var(--navy);margin-top:3px}}
.rate-card small{{font-size:14px;color:var(--muted);margin-left:6px}}
.right-section{{margin-top:17px}}
.job{{padding:12px 15px 11px;border-left:3px solid var(--cyan);background:rgba(255,255,255,.55);margin-top:9px;border-radius:0 10px 10px 0}}
.job-heading{{display:flex;justify-content:space-between;align-items:baseline;gap:16px}}
.job-heading h3,.education-item h3{{font:600 19px Poppins,sans-serif;color:var(--navy)}}
.period{{white-space:nowrap;font-size:14px;color:var(--muted)}}
.job-title{{font-size:16px;font-weight:600;color:#3c4a65;margin-top:3px}}
.job ul{{list-style:none;display:grid;gap:4px;margin-top:6px}}
.job li{{font-size:17px;line-height:1.35;color:#2a344d;display:grid;grid-template-columns:11px 1fr;gap:7px}}
.bullet{{width:8px;height:8px;border-radius:50%;background:var(--cyan);margin-top:6px}}
.education-list{{display:grid;grid-template-columns:1fr 1fr;gap:10px 18px}}
.education-item{{padding:10px 13px;background:rgba(255,255,255,.65);border-radius:9px}}
.education-item h3{{font-size:16px}}
.education-item p{{font-size:14px;line-height:1.35;color:var(--muted);margin-top:3px}}
.profile-footer{{position:absolute;left:78px;right:78px;bottom:33px;border-top:1px solid #d4deec;padding-top:13px;display:flex;justify-content:space-between;color:var(--muted);font-size:14px}}
strong{{font-weight:600}}
</style></head><body>{''.join(slides)}</body></html>"""
    html_out = output_dir / "profile-deck.html"
    pdf_out = output_dir / "profile-deck.pdf"
    html_out.write_text(html_doc, encoding="utf-8")
    chrome = find_chrome()
    if not chrome:
        raise RuntimeError("Chrome/Chromium not found. Install it or set CHROME_PATH.")
    result = subprocess.run(
        [
            chrome,
            "--headless",
            "--disable-gpu",
            "--no-first-run",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_out}",
            html_out.resolve().as_uri(),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0 or not pdf_out.exists():
        raise RuntimeError(f"PDF rendering failed: {result.stderr.strip() or result.stdout.strip()}")
    return html_out, pdf_out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Profiles JSON file")
    args = parser.parse_args()
    source = args.input.resolve()
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
        html_path, pdf_path = build(data, source, source.parent)
    except (OSError, json.JSONDecodeError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"HTML deck: {html_path}")
    print(f"PDF: {pdf_path}")
    print(f"Slides: {len(data.get('profiles', [])) + 1} (cover + profiles)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
