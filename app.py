"""
Optimove Partner One Pager Creator
Streamlit app — run with: streamlit run app.py
Deploy to Streamlit Cloud: connect GitHub repo, set main file to app.py
"""

import streamlit as st
import json
import tempfile
import sys
import re
import os
from pathlib import Path

# ── Path setup ─────────────────────────────────────────────────────────────────
APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR / "scripts"))

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Partner one pager creator",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }

.brand-header {
    display: flex; align-items: center; gap: 10px;
    padding: 0 0 1.5rem 0;
    border-bottom: 0.5px solid #d3d3d3;
    margin-bottom: 2rem;
}
.brand-mark {
    width: 32px; height: 32px; border-radius: 8px;
    background: #302c69; display: flex; align-items: center;
    justify-content: center; flex-shrink: 0;
}
.brand-mark svg { width: 18px; height: 18px; fill: white; }
.brand-title { font-size: 14px; font-weight: 500; color: #555; margin: 0; }

.progress-row {
    display: flex; align-items: center; gap: 0;
    margin-bottom: 2rem;
}
.step-dot {
    width: 28px; height: 28px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; font-weight: 600; flex-shrink: 0;
    border: 1.5px solid #d3d3d3; background: white; color: #999;
}
.step-dot.active  { background: #f0effb; border-color: #302c69; color: #302c69; }
.step-dot.done    { background: #302c69; border-color: #302c69; color: white; }
.step-line        { flex: 1; height: 1px; background: #d3d3d3; }
.step-line.done   { background: #302c69; }

.step-label { font-size: 11px; font-weight: 600; color: #9e97cb;
              text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.step-title { font-size: 20px; font-weight: 600; color: #111; margin-bottom: 1.5rem; }

.home-card {
    border: 0.5px solid #e0e0e0; border-radius: 12px;
    padding: 1.5rem; cursor: pointer; transition: border-color 0.15s;
    background: white; margin-bottom: 0.75rem;
}
.home-card:hover { border-color: #302c69; }
.home-card-icon { font-size: 24px; margin-bottom: 8px; }
.home-card-title { font-size: 16px; font-weight: 600; margin-bottom: 4px; }
.home-card-sub { font-size: 13px; color: #666; }

.review-box {
    background: #f8f8fc; border-radius: 10px;
    padding: 1.25rem; margin-bottom: 1.25rem;
}
.review-row {
    display: flex; justify-content: space-between; align-items: baseline;
    padding: 6px 0; border-bottom: 0.5px solid #e8e8e8; font-size: 14px;
}
.review-row:last-child { border-bottom: none; }
.review-row .lbl { color: #888; font-size: 13px; }
.review-row .val { font-weight: 500; text-align: right; max-width: 60%; }

.result-box {
    background: #f0fdf4; border: 1px solid #86efac;
    border-radius: 10px; padding: 1.5rem; margin-top: 1.5rem;
}
.notfound-box {
    background: #fafafa; border: 0.5px solid #e0e0e0;
    border-radius: 10px; padding: 1.5rem; margin-top: 1.5rem;
    text-align: center;
}

div[data-testid="stForm"] { border: none; padding: 0; }
</style>
""", unsafe_allow_html=True)

# ── Session state defaults ─────────────────────────────────────────────────────
DEFAULTS = {
    "screen":       "home",    # home | create | search | generating | done
    "step":         1,
    "partner":      "",
    "extra_urls":   "",
    "industry":     "iGaming",
    "format":       "PDF",
    "aspect":       "16:9",
    "pages":        2,
    "sections":     ["Overview & headline", "Key capabilities", "Use cases",
                     "KPIs & statistics", "Social proof logos"],
    "logos_raw":    "",
    "generated_path": None,
    "generated_ext":  "pdf",
    "search_query": "",
    "partner_data": None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


def reset():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v


# ── Brand header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="brand-header">
  <div class="brand-mark">
    <svg viewBox="0 0 24 24"><path d="M3 3h8v8H3zM13 3h8v8h-8zM3 13h8v8H3zM13 13h8v8h-8z"/></svg>
  </div>
  <p class="brand-title">Partner one pager creator</p>
</div>
""", unsafe_allow_html=True)


# ── Progress bar ───────────────────────────────────────────────────────────────
def progress_bar(current_step: int, total: int = 4):
    dots = []
    for i in range(1, total + 1):
        if i < current_step:
            cls = "done"
            label = "✓"
        elif i == current_step:
            cls = "active"
            label = str(i)
        else:
            cls = ""
            label = str(i)
        dots.append(f'<div class="step-dot {cls}">{label}</div>')
        if i < total:
            line_cls = "done" if i < current_step else ""
            dots.append(f'<div class="step-line {line_cls}"></div>')

    st.markdown(f'<div class="progress-row">{"".join(dots)}</div>',
                unsafe_allow_html=True)


# ── Auto-research ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def auto_research(partner_name: str) -> dict:
    """Fetch partner website and extract basic info."""
    try:
        import requests
        from urllib.parse import urlparse

        # Infer domain
        clean = re.sub(r'[^a-z0-9]', '', partner_name.lower())
        domain = f"{clean}.co.uk" if "amelco" in clean else f"{clean}.com"
        url = f"https://www.{domain}"

        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
        text = resp.text[:8000]

        # Extract meta description
        desc_match = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
                               text, re.I)
        description = desc_match.group(1) if desc_match else ""

        # Extract title
        title_match = re.search(r'<title>(.*?)</title>', text, re.I)
        site_title = title_match.group(1) if title_match else partner_name

        return {
            "domain": domain,
            "description": description[:300],
            "site_title": site_title[:120],
        }
    except Exception:
        return {}


# ── Generate document ──────────────────────────────────────────────────────────
def build_partner_data() -> dict:
    s = st.session_state
    logos = []
    for line in s["logos_raw"].strip().splitlines():
        line = line.strip()
        if line:
            if line.startswith("http"):
                logos.append({"name": line.split("/")[-1].split(".")[0].title(),
                              "logo_url": line})
            else:
                logos.append(line)

    return {
        "partner_name":    s["partner"],
        "partner_domain":  s.get("partner_domain", ""),
        "headline":        s.get("headline", ""),
        "intro":           s.get("intro", ""),
        "capabilities":    s.get("capabilities", []),
        "use_cases":       s.get("use_cases", []),
        "kpis":            s.get("kpis", []),
        "client_logos":    logos,
        "trusted_by":      "1,200+" if s["industry"] not in ("iGaming", "Sports betting") else "50+",
        "cta":             "Do more when you go Positionless",
        "format":          s["format"],
        "pages":           s["pages"],
        "aspect_ratio":    s["aspect"],
        "industry":        s["industry"],
    }


def run_generation(data: dict) -> tuple[bytes, str, str]:
    """Run the generation script and return (bytes, extension, mime_type)."""
    fmt = data.get("format", "PDF")

    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = Path(tmpdir) / "partner_data.json"
        data_path.write_text(json.dumps(data, indent=2))

        if fmt == "PDF":
            from generate_pdf import generate
            out = generate(str(data_path), tmpdir)
            mime = "application/pdf"
            ext  = "pdf"
        elif fmt == "Word":
            from generate_docx import generate
            out = generate(str(data_path), tmpdir)
            mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ext  = "docx"
        else:
            from generate_pptx import generate
            aspect = data.get("aspect_ratio", "16:9")
            out = generate(str(data_path), tmpdir, aspect)
            mime = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            ext  = "pptx"

        return Path(out).read_bytes(), ext, mime


# ──────────────────────────────────────────────────────────────────────────────
# SCREEN: HOME
# ──────────────────────────────────────────────────────────────────────────────
if st.session_state["screen"] == "home":
    st.markdown("### What would you like to do?")
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄  Create a one pager",
                     use_container_width=True, key="btn_create",
                     help="Generate a new partner one pager from scratch"):
            st.session_state["screen"] = "create"
            st.session_state["step"] = 1
            st.rerun()

    with col2:
        if st.button("🔍  Find a one pager",
                     use_container_width=True, key="btn_search",
                     help="Search existing one pagers by partner name"):
            st.session_state["screen"] = "search"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("Optimove Partnerships team · internal tool")


# ──────────────────────────────────────────────────────────────────────────────
# SCREEN: SEARCH
# ──────────────────────────────────────────────────────────────────────────────
elif st.session_state["screen"] == "search":
    st.markdown('<p class="step-title">Find a one pager</p>', unsafe_allow_html=True)

    query = st.text_input("Partner name", placeholder="e.g. Mixpanel, Klaviyo, The Trade Desk…",
                          key="search_input_box")

    st.markdown("**Recent partners**")
    recent = ["Amelco", "The Trade Desk", "Mixpanel", "Klaviyo", "Braze"]
    cols = st.columns(len(recent))
    for i, name in enumerate(recent):
        if cols[i].button(name, key=f"recent_{i}", use_container_width=True):
            st.session_state["search_query"] = name
            st.rerun()

    if st.session_state.get("search_query"):
        query = st.session_state["search_query"]

    col_search, col_back = st.columns([3, 1])
    with col_search:
        search_clicked = st.button("Search ↗", type="primary", use_container_width=True)
    with col_back:
        if st.button("← Back", use_container_width=True):
            reset()
            st.rerun()

    if search_clicked and query:
        # Simple lookup — in production connect to Notion or a database
        known = {
            "amelco":        "Optimove x Amelco - One Pager.pdf",
            "the trade desk":"Optimove x The Trade Desk - One Pager.pdf",
            "mixpanel":      None,
            "klaviyo":       None,
        }
        key = query.lower().strip()
        match = next((v for k, v in known.items() if k in key or key in k), "NOT_FOUND")

        if match and match != "NOT_FOUND":
            st.success(f"✅ Found a one pager for **{query}**")
            st.markdown(f"""
<div class="result-box">
  <strong>Optimove x {query.title()}</strong><br>
  <span style="color:#666;font-size:13px">Partner one pager · PDF</span>
</div>
""", unsafe_allow_html=True)
            col_dl, col_regen = st.columns(2)
            with col_dl:
                st.button("⬇️  Download", use_container_width=True)
            with col_regen:
                if st.button("🔄  Regenerate", use_container_width=True):
                    st.session_state["partner"] = query
                    st.session_state["screen"] = "create"
                    st.session_state["step"] = 1
                    st.rerun()
        else:
            st.markdown(f"""
<div class="notfound-box">
  <p style="font-size:15px;font-weight:600;margin-bottom:8px">
    No one pager found for "{query}"
  </p>
  <p style="font-size:13px;color:#666;margin-bottom:0">
    Want to create one?
  </p>
</div>
""", unsafe_allow_html=True)
            if st.button(f"Create a one pager for {query} ↗",
                         type="primary", use_container_width=True):
                st.session_state["partner"] = query
                st.session_state["screen"] = "create"
                st.session_state["step"] = 1
                st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# SCREEN: CREATE (steps 1–4)
# ──────────────────────────────────────────────────────────────────────────────
elif st.session_state["screen"] == "create":
    step = st.session_state["step"]
    progress_bar(step)

    # ── Step 1: Partner details ──────────────────────────────────────────────
    if step == 1:
        st.markdown('<p class="step-label">Step 1 of 4</p>', unsafe_allow_html=True)
        st.markdown('<p class="step-title">Partner details</p>', unsafe_allow_html=True)

        partner = st.text_input(
            "Partner name or directory link",
            value=st.session_state["partner"],
            placeholder="e.g. Amelco, Klaviyo — or paste a Notion URL",
        )

        extra = st.text_area(
            "Additional content (optional)",
            value=st.session_state["extra_urls"],
            placeholder="Paste URLs to academy articles, PRs, or blogs — one per line",
            height=90,
        )

        industry = st.radio(
            "Industry",
            ["Retail", "iGaming", "Sports betting", "Trading", "Other"],
            horizontal=True,
            index=["Retail", "iGaming", "Sports betting", "Trading", "Other"].index(
                st.session_state["industry"]
            ),
        )

        col_back, col_next = st.columns([1, 3])
        with col_back:
            if st.button("← Back"):
                reset()
                st.rerun()
        with col_next:
            if st.button("Next →", type="primary", use_container_width=True):
                if not partner.strip():
                    st.error("Please enter a partner name.")
                else:
                    st.session_state["partner"]    = partner.strip()
                    st.session_state["extra_urls"] = extra.strip()
                    st.session_state["industry"]   = industry

                    # Auto-research the partner
                    with st.spinner(f"Looking up {partner}…"):
                        info = auto_research(partner)
                        if info.get("domain"):
                            st.session_state["partner_domain"] = info["domain"]

                    st.session_state["step"] = 2
                    st.rerun()

    # ── Step 2: Format & length ──────────────────────────────────────────────
    elif step == 2:
        st.markdown('<p class="step-label">Step 2 of 4</p>', unsafe_allow_html=True)
        st.markdown('<p class="step-title">Format & length</p>', unsafe_allow_html=True)

        fmt = st.radio(
            "Output format",
            ["PDF", "Word (.docx)", "PowerPoint"],
            horizontal=True,
            index=["PDF", "Word (.docx)", "PowerPoint"].index(
                st.session_state["format"] if st.session_state["format"] in
                ["PDF", "Word (.docx)", "PowerPoint"] else "PDF"
            ),
        )

        aspect = st.session_state["aspect"]
        if fmt == "PowerPoint":
            aspect = st.radio("Aspect ratio", ["16:9 widescreen", "4:3 classic"],
                              horizontal=True)
            aspect = "16:9" if "16:9" in aspect else "4:3"

        pages = st.radio("Number of pages", [1, 2], horizontal=True,
                         index=st.session_state["pages"] - 1,
                         format_func=lambda x: f"{x} page{'s' if x > 1 else ''}")

        col_back, col_next = st.columns([1, 3])
        with col_back:
            if st.button("← Back"):
                st.session_state["step"] = 1
                st.rerun()
        with col_next:
            if st.button("Next →", type="primary", use_container_width=True):
                # Normalise format label
                fmt_map = {"PDF": "PDF", "Word (.docx)": "Word", "PowerPoint": "PowerPoint"}
                st.session_state["format"] = fmt_map[fmt]
                st.session_state["aspect"] = aspect
                st.session_state["pages"]  = pages
                st.session_state["step"]   = 3
                st.rerun()

    # ── Step 3: Content ──────────────────────────────────────────────────────
    elif step == 3:
        st.markdown('<p class="step-label">Step 3 of 4</p>', unsafe_allow_html=True)
        st.markdown('<p class="step-title">What to include</p>', unsafe_allow_html=True)

        all_sections = [
            "Overview & headline",
            "Key capabilities",
            "Use cases",
            "KPIs & statistics",
            "Social proof logos",
            "Client quote",
        ]
        selected = []
        cols = st.columns(2)
        for i, sec in enumerate(all_sections):
            default = sec in st.session_state["sections"]
            if cols[i % 2].checkbox(sec, value=default, key=f"sec_{i}"):
                selected.append(sec)

        st.markdown("<br>", unsafe_allow_html=True)
        logos_raw = st.text_area(
            "Client logos",
            value=st.session_state["logos_raw"],
            placeholder="Brand names or direct image URLs — one per line\n"
                        "e.g. Sephora\nFanDuel\nhttps://img.logo.dev/staples.com?token=...",
            height=100,
        )

        col_back, col_next = st.columns([1, 3])
        with col_back:
            if st.button("← Back"):
                st.session_state["step"] = 2
                st.rerun()
        with col_next:
            if st.button("Review →", type="primary", use_container_width=True):
                st.session_state["sections"] = selected
                st.session_state["logos_raw"] = logos_raw
                st.session_state["step"] = 4
                st.rerun()

    # ── Step 4: Review & generate ────────────────────────────────────────────
    elif step == 4:
        st.markdown('<p class="step-label">Step 4 of 4</p>', unsafe_allow_html=True)
        st.markdown('<p class="step-title">Review & generate</p>', unsafe_allow_html=True)

        s = st.session_state
        fmt_display = s["format"]
        if fmt_display == "PowerPoint":
            fmt_display += f" · {s['aspect']}"

        rows = [
            ("Partner",       s["partner"]),
            ("Industry",      s["industry"]),
            ("Format",        fmt_display),
            ("Pages",         str(s["pages"])),
            ("Sections",      ", ".join(s["sections"]) or "—"),
            ("Client logos",  f"{len([l for l in s['logos_raw'].splitlines() if l.strip()])} added"
                              if s["logos_raw"].strip() else "Auto-fetch"),
        ]

        rows_html = "".join(
            f'<div class="review-row"><span class="lbl">{l}</span>'
            f'<span class="val">{v}</span></div>'
            for l, v in rows
        )
        st.markdown(f'<div class="review-box">{rows_html}</div>', unsafe_allow_html=True)

        col_back, col_edit = st.columns([3, 1])
        with col_edit:
            if st.button("Edit", use_container_width=True):
                st.session_state["step"] = 1
                st.rerun()

        if st.button("✨  Generate one pager", type="primary", use_container_width=True):
            st.session_state["screen"] = "generating"
            st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# SCREEN: GENERATING
# ──────────────────────────────────────────────────────────────────────────────
elif st.session_state["screen"] == "generating":
    partner = st.session_state["partner"]
    fmt     = st.session_state["format"]

    st.markdown(f"### Generating one pager for {partner}…")

    steps_msg = [
        f"Researching {partner}…",
        "Fetching logos…",
        f"Building {fmt} document…",
        "Finalizing…",
    ]

    progress = st.progress(0)
    status   = st.empty()

    try:
        data = build_partner_data()

        for i, msg in enumerate(steps_msg[:-1]):
            status.markdown(f"_{msg}_")
            progress.progress((i + 1) * 25)

        file_bytes, ext, mime = run_generation(data)

        progress.progress(100)
        status.empty()

        filename = f"Optimove x {partner} - One Pager.{ext}"

        st.success(f"✅ Done! Your one pager is ready.")
        st.markdown("<br>", unsafe_allow_html=True)

        st.download_button(
            label=f"⬇️  Download {filename}",
            data=file_bytes,
            file_name=filename,
            mime=mime,
            use_container_width=True,
            type="primary",
        )

        col_new, col_home = st.columns(2)
        with col_new:
            if st.button("Create another", use_container_width=True):
                for k in ["step", "partner", "extra_urls", "industry",
                          "format", "aspect", "pages", "sections", "logos_raw"]:
                    st.session_state[k] = DEFAULTS[k]
                st.session_state["screen"] = "create"
                st.rerun()
        with col_home:
            if st.button("← Home", use_container_width=True):
                reset()
                st.rerun()

    except Exception as e:
        progress.empty()
        status.empty()
        st.error(f"Generation failed: {e}")
        if st.button("← Back to review"):
            st.session_state["screen"] = "create"
            st.session_state["step"]   = 4
            st.rerun()
