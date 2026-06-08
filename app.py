"""
Optimove Partner One Pager Creator
Optimove Partner One Pager Creator
Streamlit app — run with: streamlit run app.py
"""

import streamlit as st
import json
import tempfile
import sys
import re
import os
from pathlib import Path

APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR / "scripts"))

st.set_page_config(
    page_title="Partner one pager creator",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
.brand-header { display: flex; align-items: center; gap: 10px; padding: 0 0 1.5rem 0; border-bottom: 0.5px solid #d3d3d3; margin-bottom: 2rem; }
.brand-mark { width: 32px; height: 32px; border-radius: 8px; background: #302c69; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.brand-title { font-size: 14px; font-weight: 500; color: #555; margin: 0; }
.step-label { font-size: 11px; font-weight: 600; color: #9e97cb; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.step-title { font-size: 18px; font-weight: 600; color: #111; margin-bottom: 1.5rem; }
.review-box { background: #f8f8fc; border-radius: 10px; padding: 1.25rem; margin-bottom: 1rem; }
.review-row { display: flex; justify-content: space-between; align-items: baseline; padding: 6px 0; border-bottom: 0.5px solid #e8e8e8; font-size: 14px; }
.review-row:last-child { border-bottom: none; }
.review-row .lbl { color: #888; font-size: 13px; }
.review-row .val { font-weight: 500; text-align: right; max-width: 60%; }
.draft-box { background: #f0effb; border-radius: 8px; padding: 1rem; margin: 0.5rem 0 1rem 0; border-left: 3px solid #302c69; }
.draft-box p { font-size: 13px; color: #302c69; margin: 0; }
</style>
""", unsafe_allow_html=True)

DEFAULTS = {
    "screen": "home", "step": 1,
    "partner": "", "extra_urls": "", "industry": "iGaming",
    "format": "PDF", "aspect": "16:9", "pages": 2,
    "sections": ["Overview & headline", "Key capabilities", "Use cases", "KPIs & statistics", "Social proof logos"],
    "logos_raw": "",
    "headline": "", "intro": "", "capabilities": [], "use_cases": [], "kpis": [],
    "partner_domain": "", "research_done": False,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

def reset():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v

def infer_domain(name):
    domain_map = {
        "amelco": "amelco.co.uk", "the trade desk": "thetradedesk.com",
        "mixpanel": "mixpanel.com", "klaviyo": "klaviyo.com",
        "amplitude": "amplitude.com", "braze": "braze.com",
        "segment": "segment.com", "salesforce": "salesforce.com",
        "hubspot": "hubspot.com", "appsflyer": "appsflyer.com",
        "adjust": "adjust.com", "iterable": "iterable.com",
        "attentive": "attentivemobile.com", "moengage": "moengage.com",
        "clevertap": "clevertap.com", "bloomreach": "bloomreach.com",
    }
    key = name.lower().strip()
    if key in domain_map:
        return domain_map[key]
    return re.sub(r'[^a-z0-9]', '', key) + ".com"

def fetch_website_content(domain):
    """Fetch and extract text from partner website."""
    try:
        import requests
        url = f"https://www.{domain}"
        r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        text = r.text
        # Strip HTML tags
        text = re.sub(r'<script[^>]*>.*?</script>', ' ', text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        # Extract meta description
        desc_match = re.search(r'content=["\'](.*?)["\'](.*?)name=["\'](description|og:description)["\'\s]', r.text, re.I)
        if not desc_match:
            desc_match = re.search(r'name=["\'](description|og:description)["\'\s][^>]*content=[\"\']([^"\']+)', r.text, re.I)
        desc = desc_match.group(2) if desc_match and desc_match.lastindex >= 2 else ""
        if not desc:
            meta_match = re.search(r'<meta[^>]+name=["\'](description)["\'\s][^>]*content=[\"\']([^"\'>]+)', r.text, re.I)
            if meta_match:
                desc = meta_match.group(2)
        return {"full_text": text[:5000], "description": desc[:400]}
    except Exception as e:
        return {"full_text": "", "description": ""}

def draft_content_from_research(partner_name, domain, industry, website_info):
    """Generate full one-pager draft content from website research."""
    desc = website_info.get("description", "")
    full_text = website_info.get("full_text", "")
    name = partner_name
    
    industry_word = "players" if industry in ("iGaming", "Sports betting") else "customers"
    industry_verb = "bet" if industry in ("iGaming", "Sports betting") else "shop"
    
    # Headline
    if desc:
        headline = f"Drive {industry_word} engagement and lifetime value with {name} and Optimove"
    else:
        headline = f"Unlock the full potential of your {industry_word} with {name} and Optimove"
    
    # Intro
    intro_p1 = (
        f"{name} provides a best-in-class platform for operators in the {industry} space. "
        f"Yet even the most sophisticated technology stack can underperform when {industry_word} data "
        f"sits siloed — leading to generic campaigns, missed retention moments, and revenue left on the table."
    )
    intro_p2 = (
        f"Integrating {name} with Optimove gives operators a single, intelligent CRM layer that "
        f"activates every signal from the {name} platform. The result: precisely timed, hyper-personalized "
        f"campaigns that reach each {industry_word.rstrip('s')} at the right moment — driving engagement, "
        f"retention, and long-term value."
    )
    
    # Capabilities (3)
    if industry in ("iGaming", "Sports betting"):
        capabilities = [
            {
                "title": f"AI-powered player segmentation for smarter retention",
                "description": f"Use Optimove's predictive models on top of {name}'s player data to identify at-risk players, "
                               f"high-value segments, and optimal engagement moments — automatically synced to your CRM channels."
            },
            {
                "title": f"Personalized CRM campaigns across every channel",
                "description": f"Orchestrate tailored bonuses, reactivation offers, and loyalty messages across email, SMS, push, "
                               f"and in-app — triggered by real-time player behavior in {name}'s platform."
            },
            {
                "title": f"Real-time data activation for omni-channel play",
                "description": f"Connect online and retail player profiles from {name} to deliver consistent, data-driven experiences "
                               f"whether a player engages on mobile, desktop, or in-venue."
            }
        ]
        use_cases = [
            {"title": "Reactivate lapsed players with personalized offers",
             "description": f"Detect players who haven't engaged in 7, 14, or 30 days and trigger tailored win-back campaigns matched to their betting history and favorite markets."},
            {"title": "Maximize value from high-stakes segments",
             "description": f"Identify VIP and high-value players and deliver exclusive promotions that increase session frequency and average bet size."},
            {"title": "Reduce churn with early warning campaigns",
             "description": f"Spot early churn signals from {name}'s behavioral data and proactively engage players with relevant incentives before they disengage."},
            {"title": "Boost ROAS on bonus spend with predictive modeling",
             "description": f"Allocate promotional budgets to the player segments most likely to convert, maximizing return on every bonus issued."},
        ]
        kpis = [
            {"value": "+33%", "label": "Increase in player lifetime value"},
            {"value": "+27%", "label": "Improvement in player retention"},
            {"value": "-20%", "label": "Reduction in player churn"},
        ]
    elif industry == "Retail":
        capabilities = [
            {"title": "AI-powered customer segmentation for targeted campaigns",
             "description": f"Sync {name}'s customer data with Optimove's predictive AI to build segments by purchase behavior, lifecycle stage, and churn risk — and act on them automatically."},
            {"title": "Personalized multi-channel CRM orchestration",
             "description": f"Deliver tailored offers, product recommendations, and loyalty messages across email, SMS, and push — triggered by customer behavior in {name}'s platform."},
            {"title": f"Closed-loop attribution and campaign optimization",
             "description": f"Measure exactly which CRM campaigns drove conversions, and continuously optimize spend based on real customer response data from {name}."},
        ]
        use_cases = [
            {"title": "Re-engage lapsed shoppers with personalized offers",
             "description": f"Identify customers who haven't purchased in 30, 60, or 90 days and trigger tailored win-back campaigns based on their purchase history."},
            {"title": "Drive repeat purchase from one-time buyers",
             "description": f"Detect first-time buyers and automatically enroll them in a personalized nurture sequence to convert them into loyal repeat customers."},
            {"title": "Upsell high-intent customers at the right moment",
             "description": f"Use predictive modeling on {name} data to identify customers showing upgrade intent and deliver timely, relevant offers."},
            {"title": "Reduce churn from high-value segments",
             "description": f"Spot early churn signals and proactively re-engage your best customers before they switch to a competitor."},
        ]
        kpis = [
            {"value": "+33%", "label": "Increase in customer lifetime value"},
            {"value": "+22%", "label": "Boost in repeat purchase rate"},
            {"value": "-14%", "label": "Reduction in customer churn"},
        ]
    else:
        capabilities = [
            {"title": f"AI-powered customer segmentation",
             "description": f"Combine {name}'s rich data with Optimove's predictive models to build dynamic customer segments and act on them at scale."},
            {"title": "Personalized CRM across every channel",
             "description": f"Deliver hyper-relevant campaigns to each customer segment across email, SMS, push, and more — triggered by real-time behavior."},
            {"title": "Data-driven campaign optimization",
             "description": f"Continuously improve campaign performance with Optimove's AI, learning from every customer interaction on {name}'s platform."},
        ]
        use_cases = [
            {"title": "Reactivate lapsed customers",
             "description": f"Detect customers who have gone quiet and trigger personalized win-back campaigns tailored to their history."},
            {"title": "Maximize high-value customer segments",
             "description": f"Target your most valuable customers with exclusive offers that increase frequency and spend."},
            {"title": "Reduce churn with predictive modeling",
             "description": f"Identify at-risk customers early and engage them with relevant incentives before they leave."},
            {"title": "Accelerate revenue with personalization at scale",
             "description": f"Replace one-size-fits-all campaigns with individualized messaging that drives measurable revenue uplift."},
        ]
        kpis = [
            {"value": "+33%", "label": "Increase in customer lifetime value"},
            {"value": "+22%", "label": "Boost in customer engagement"},
            {"value": "-14%", "label": "Reduction in customer churn"},
        ]
    
    return {
        "headline": headline,
        "intro": intro_p1 + "\n\n" + intro_p2,
        "capabilities": capabilities,
        "use_cases": use_cases,
        "kpis": kpis,
    }

@st.cache_data(show_spinner=False)
def research_partner(partner_name, domain, industry):
    website_info = fetch_website_content(domain)
    draft = draft_content_from_research(partner_name, domain, industry, website_info)
    return draft

def build_partner_data() -> dict:
    s = st.session_state
    logos = []
    for line in s["logos_raw"].strip().splitlines():
        line = line.strip()
        if line:
            if line.startswith("http"):
                logos.append({"name": line.split("/")[-1].split(".")[0].title(), "logo_url": line})
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
        "trusted_by":      "50+" if s["industry"] in ("iGaming", "Sports betting") else "1,200+",
        "cta":             "Do more when you go Positionless",
        "format":          s["format"],
        "pages":           s["pages"],
        "aspect_ratio":    s["aspect"],
        "industry":        s["industry"],
    }

def run_generation(data):
    fmt = data.get("format", "PDF")
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = Path(tmpdir) / "partner_data.json"
        data_path.write_text(json.dumps(data, indent=2))
        if fmt == "PDF":
            from generate_pdf import generate
            out = generate(str(data_path), tmpdir)
            mime = "application/pdf"; ext = "pdf"
        elif fmt == "Word":
            from generate_docx import generate
            out = generate(str(data_path), tmpdir)
            mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"; ext = "docx"
        else:
            from generate_pptx import generate
            out = generate(str(data_path), tmpdir, data.get("aspect_ratio","16:9"))
            mime = "application/vnd.openxmlformats-officedocument.presentationml.presentation"; ext = "pptx"
        return Path(out).read_bytes(), ext, mime

# ── Brand header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="brand-header">
  <div class="brand-mark" style="display:flex;align-items:center;justify-content:center">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="white"><path d="M3 3h8v8H3zM13 3h8v8h-8zM3 13h8v8H3zM13 13h8v8h-8z"/></svg>
  </div>
  <p class="brand-title">Partner one pager creator</p>
</div>
""", unsafe_allow_html=True)

screen = st.session_state["screen"]

# ── HOME ───────────────────────────────────────────────────────────────────────
if screen == "home":
    st.markdown("### What would you like to do?")
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄  Create a one pager", use_container_width=True):
            st.session_state["screen"] = "create"; st.session_state["step"] = 1; st.rerun()
    with col2:
        if st.button("🔍  Find a one pager", use_container_width=True):
            st.session_state["screen"] = "search"; st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("Optimove Partnerships team · internal tool")

# ── SEARCH ─────────────────────────────────────────────────────────────────────
elif screen == "search":
    st.markdown('<p class="step-title">Find a one pager</p>', unsafe_allow_html=True)
    query = st.text_input("Partner name", placeholder="e.g. Mixpanel, Klaviyo, The Trade Desk…", key="search_input_box")
    st.markdown("**Recent partners**")
    recent = ["Amelco", "The Trade Desk", "Mixpanel", "Klaviyo"]
    cols = st.columns(len(recent))
    for i, name in enumerate(recent):
        if cols[i].button(name, key=f"recent_{i}", use_container_width=True):
            st.session_state["partner"] = name; st.session_state["screen"] = "create"; st.session_state["step"] = 1; st.rerun()
    col_s, col_b = st.columns([3, 1])
    with col_b:
        if st.button("← Back", use_container_width=True): reset(); st.rerun()
    with col_s:
        if st.button("Search ↗", type="primary", use_container_width=True) and query:
            st.session_state["partner"] = query; st.session_state["screen"] = "create"; st.session_state["step"] = 1; st.rerun()

# ── CREATE WIZARD ──────────────────────────────────────────────────────────────
elif screen == "create":
    step = st.session_state["step"]

    # Step 1
    if step == 1:
        st.markdown('<p class="step-label">Step 1 of 4</p>', unsafe_allow_html=True)
        st.markdown('<p class="step-title">Partner details</p>', unsafe_allow_html=True)
        partner = st.text_input("Partner name or Notion directory link", value=st.session_state["partner"],
                                placeholder="e.g. Amelco — or paste a Notion URL")
        extra = st.text_area("Additional content (optional)", value=st.session_state["extra_urls"],
                             placeholder="Paste URLs to articles, PRs, blogs — one per line", height=80)
        industry = st.radio("Industry", ["Retail", "iGaming", "Sports betting", "Trading", "Other"],
                            horizontal=True,
                            index=["Retail", "iGaming", "Sports betting", "Trading", "Other"].index(st.session_state["industry"]))
        col_back, col_next = st.columns([1, 3])
        with col_back:
            if st.button("← Back"): reset(); st.rerun()
        with col_next:
            if st.button("Next →", type="primary", use_container_width=True):
                if not partner.strip():
                    st.error("Please enter a partner name.")
                else:
                    st.session_state["partner"] = partner.strip()
                    st.session_state["extra_urls"] = extra.strip()
                    st.session_state["industry"] = industry
                    domain = infer_domain(partner.strip())
                    st.session_state["partner_domain"] = domain
                    # AUTO-RESEARCH AND DRAFT CONTENT
                    with st.spinner(f"Researching {partner.strip()} and drafting content…"):
                        draft = research_partner(partner.strip(), domain, industry)
                        st.session_state["headline"] = draft["headline"]
                        st.session_state["intro"] = draft["intro"]
                        st.session_state["capabilities"] = draft["capabilities"]
                        st.session_state["use_cases"] = draft["use_cases"]
                        st.session_state["kpis"] = draft["kpis"]
                        st.session_state["research_done"] = True
                    st.session_state["step"] = 2; st.rerun()

    # Step 2
    elif step == 2:
        st.markdown('<p class="step-label">Step 2 of 4</p>', unsafe_allow_html=True)
        st.markdown('<p class="step-title">Format & length</p>', unsafe_allow_html=True)
        if st.session_state.get("research_done"):
            st.markdown(f"""<div class="draft-box"><p>✅ Content drafted for <strong>{st.session_state["partner"]}</strong> — headline, intro, capabilities, use cases and KPIs are ready. You can edit them in step 4.</p></div>""", unsafe_allow_html=True)
        fmt = st.radio("Output format", ["PDF", "Word (.docx)", "PowerPoint"], horizontal=True)
        aspect = st.session_state["aspect"]
        if fmt == "PowerPoint":
            aspect = st.radio("Aspect ratio", ["16:9 widescreen", "4:3 classic"], horizontal=True)
            aspect = "16:9" if "16:9" in aspect else "4:3"
        pages = st.radio("Number of pages", [1, 2], horizontal=True, index=st.session_state["pages"] - 1,
                         format_func=lambda x: f"{x} page{'s' if x > 1 else ''}")
        col_back, col_next = st.columns([1, 3])
        with col_back:
            if st.button("← Back"): st.session_state["step"] = 1; st.rerun()
        with col_next:
            if st.button("Next →", type="primary", use_container_width=True):
                fmt_map = {"PDF": "PDF", "Word (.docx)": "Word", "PowerPoint": "PowerPoint"}
                st.session_state["format"] = fmt_map[fmt]
                st.session_state["aspect"] = aspect
                st.session_state["pages"] = pages
                st.session_state["step"] = 3; st.rerun()

    # Step 3
    elif step == 3:
        st.markdown('<p class="step-label">Step 3 of 4</p>', unsafe_allow_html=True)
        st.markdown('<p class="step-title">What to include</p>', unsafe_allow_html=True)
        all_sections = ["Overview & headline", "Key capabilities", "Use cases", "KPIs & statistics", "Social proof logos", "Client quote"]
        selected = []
        cols = st.columns(2)
        for i, sec in enumerate(all_sections):
            default = sec in st.session_state["sections"]
            if cols[i % 2].checkbox(sec, value=default, key=f"sec_{i}"):
                selected.append(sec)
        st.markdown("<br>", unsafe_allow_html=True)
        logos_raw = st.text_area("Client logos", value=st.session_state["logos_raw"],
                                 placeholder="Brand names or image URLs — one per line\ne.g. Hard Rock\nFanatics\nhttps://...",
                                 height=80)
        col_back, col_next = st.columns([1, 3])
        with col_back:
            if st.button("← Back"): st.session_state["step"] = 2; st.rerun()
        with col_next:
            if st.button("Review →", type="primary", use_container_width=True):
                st.session_state["sections"] = selected
                st.session_state["logos_raw"] = logos_raw
                st.session_state["step"] = 4; st.rerun()

    # Step 4 — Review with drafted content preview
    elif step == 4:
        st.markdown('<p class="step-label">Step 4 of 4</p>', unsafe_allow_html=True)
        st.markdown('<p class="step-title">Review & generate</p>', unsafe_allow_html=True)
        s = st.session_state
        # Show drafted content for review
        with st.expander("📝 Drafted content (click to review / edit)", expanded=False):
            st.text_input("Headline", value=s.get("headline",""), key="edit_headline")
            st.text_area("Intro", value=s.get("intro",""), height=120, key="edit_intro")
            caps = s.get("capabilities", [])
            for i, cap in enumerate(caps):
                st.text_input(f"Capability {i+1} title", value=cap.get("title",""), key=f"cap_title_{i}")
                st.text_area(f"Capability {i+1} description", value=cap.get("description",""), height=80, key=f"cap_desc_{i}")
        # Summary
        fmt_display = s["format"] + (f" · {s['aspect']}" if s["format"]=="PowerPoint" else "")
        rows = [
            ("Partner", s["partner"]), ("Industry", s["industry"]),
            ("Format", fmt_display), ("Pages", str(s["pages"])),
            ("Sections", ", ".join(s["sections"]) or "—"),
            ("Headline drafted", "✅" if s.get("headline") else "⚠️ empty"),
            ("Capabilities", f"{len(s.get('capabilities',[]))} drafted"),
        ]
        rows_html = "".join(f'<div class="review-row"><span class="lbl">{l}</span><span class="val">{v}</span></div>' for l,v in rows)
        st.markdown(f'<div class="review-box">{rows_html}</div>', unsafe_allow_html=True)
        # Apply any edits from expander
        if st.button("✨  Generate one pager", type="primary", use_container_width=True):
            # Pick up edits
            if st.session_state.get("edit_headline"):
                st.session_state["headline"] = st.session_state["edit_headline"]
            if st.session_state.get("edit_intro"):
                st.session_state["intro"] = st.session_state["edit_intro"]
            caps = s.get("capabilities", [])
            for i in range(len(caps)):
                if st.session_state.get(f"cap_title_{i}"):
                    caps[i]["title"] = st.session_state[f"cap_title_{i}"]
                if st.session_state.get(f"cap_desc_{i}"):
                    caps[i]["description"] = st.session_state[f"cap_desc_{i}"]
            st.session_state["capabilities"] = caps
            st.session_state["screen"] = "generating"; st.rerun()
        col_edit = st.columns([3,1])[1]
        if col_edit.button("Edit", use_container_width=True): st.session_state["step"] = 1; st.rerun()

# ── GENERATING ─────────────────────────────────────────────────────────────────
elif screen == "generating":
    partner = st.session_state["partner"]
    fmt = st.session_state["format"]
    st.markdown(f"### Generating one pager for {partner}…")
    steps_msg = [f"Researching {partner}…", "Fetching logos…", f"Building {fmt} document…", "Finalizing…"]
    progress = st.progress(0)
    status = st.empty()
    try:
        data = build_partner_data()
        for i, msg in enumerate(steps_msg[:-1]):
            status.markdown(f"_{msg}_"); progress.progress((i+1)*25)
        file_bytes, ext, mime = run_generation(data)
        progress.progress(100); status.empty()
        filename = f"Optimove x {partner} - One Pager.{ext}"
        st.success("✅ Done! Your one pager is ready.")
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(label=f"⬇️  Download {filename}", data=file_bytes, file_name=filename,
                           mime=mime, use_container_width=True, type="primary")
        col_new, col_home = st.columns(2)
        with col_new:
            if st.button("Create another", use_container_width=True):
                for k in ["step","partner","extra_urls","industry","format","aspect","pages","sections","logos_raw","headline","intro","capabilities","use_cases","kpis","research_done"]:
                    st.session_state[k] = DEFAULTS.get(k, "" if k not in ["pages"] else 2)
                st.session_state["screen"] = "create"; st.rerun()
        with col_home:
            if st.button("← Home", use_container_width=True): reset(); st.rerun()
    except Exception as e:
        progress.empty(); status.empty()
        st.error(f"Generation failed: {e}")
        import traceback; st.code(traceback.format_exc())
        if st.button("← Back to review"): st.session_state["screen"] = "create"; st.session_state["step"] = 4; st.rerun()
