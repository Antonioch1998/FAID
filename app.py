import copy
import html
import json
from datetime import datetime

import streamlit as st

# ═══════════════════════════ CONFIG ═══════════════════════════
FORM_TITLE = "Financial Aid Review Form"
FORM_SUBTITLE = "American University of Beirut"
PRINT_HIDDEN_NAMES = False           # True → hidden names still appear on printouts

RED = "#840132"          # AUB red
RED_DARK = "#5e0123"
RED_LIGHT = "#fbf1f4"

st.set_page_config(page_title=FORM_TITLE, page_icon="📝", layout="centered")

CLASSES = ["Freshman", "Sophomore", "Junior", "Senior", "Fourth Year", "Graduate", "Other"]
STATUSES = ["Employed", "Unemployed", "Self-Employed"]
PARENTS = [("father", "Father"), ("mother", "Mother")]
STEPS = ["Student", "Parents", "Siblings & Assets"]

# ═══════════════════════════ STYLE ════════════════════════════
st.markdown(f"""
<style>
/* page */
.stApp {{ background: #ffffff; color: #1f1f1f; }}
.block-container {{ padding-top: 2rem; max-width: 720px; }}
[data-testid="stSidebar"] {{ background: #f7f7f7; }}
.stAppDeployButton {{ display: none; }}

/* header */
.aub-header {{ background: linear-gradient(135deg, {RED} 0%, {RED_DARK} 100%);
  color: #fff; border-radius: 14px; padding: 22px 26px; margin-bottom: 22px; }}
.aub-header .t {{ font-size: 1.6rem; font-weight: 700; letter-spacing: .2px; }}
.aub-header .s {{ font-size: .95rem; opacity: .85; margin-top: 2px; }}

/* stepper */
.stepper {{ display: flex; align-items: center; margin: 4px 0 26px; }}
.step {{ display: flex; flex-direction: column; align-items: center; width: 110px; }}
.dot {{ width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center;
  justify-content: center; font-weight: 700; border: 2px solid #cfcfcf; color: #9a9a9a; background: #fff; }}
.step.active .dot, .step.done .dot {{ background: {RED}; border-color: {RED}; color: #fff; }}
.step .lbl {{ font-size: .8rem; margin-top: 6px; color: #9a9a9a; text-align: center; }}
.step.active .lbl {{ color: {RED}; font-weight: 700; }}
.step.done .lbl {{ color: #555; }}
.line {{ flex: 1; height: 2px; background: #dedede; margin-bottom: 22px; }}
.line.done {{ background: {RED}; }}

/* section titles */
.sec {{ color: {RED}; font-size: 1.15rem; font-weight: 700; border-bottom: 2px solid {RED};
  padding-bottom: 6px; margin: 18px 0 14px; }}
.sub {{ color: #333; font-size: 1rem; font-weight: 700; margin: 6px 0 10px; }}
.hint {{ color: #8a8a8a; font-size: .85rem; margin: -6px 0 12px; }}

/* fields: one per row, clearly separated */
[data-testid="stElementContainer"]:has(input),
[data-testid="stElementContainer"]:has(textarea),
[data-testid="stElementContainer"]:has([data-testid="stSelectbox"]) {{ margin-bottom: 6px; }}
[data-testid="stTextInputRootElement"], [data-testid="stNumberInputContainer"],
[data-testid="stTextAreaRootElement"], [data-testid="stSelectbox"] div:has(> div > input) {{
  background: #fff !important; border: 1.5px solid #d9d9d9 !important; border-radius: 10px !important;
  transition: border-color .15s, box-shadow .15s; }}
[data-testid="stTextInputRootElement"]:focus-within, [data-testid="stNumberInputContainer"]:focus-within,
[data-testid="stTextAreaRootElement"]:focus-within, [data-testid="stSelectbox"] div:has(> div > input):focus-within {{
  border-color: {RED} !important; box-shadow: 0 0 0 3px rgba(132,1,50,.12) !important; }}
[data-testid="stTextInputRootElement"] *, [data-testid="stNumberInputContainer"] *,
[data-testid="stTextAreaRootElement"] *, [data-testid="stSelectbox"] div {{ background: transparent !important; }}
input, textarea {{ color: #1f1f1f !important; }}
input, textarea {{ font-size: 1rem !important; padding-top: 12px !important; padding-bottom: 12px !important; }}
input::placeholder, textarea::placeholder {{ color: #9a9a9a !important; opacity: 1 !important; }}
[data-testid="stSelectbox"] {{ font-size: 1rem; }}
/* hide the +/- buttons next to number fields */
button[data-testid="stNumberInputStepUp"], button[data-testid="stNumberInputStepDown"] {{ display: none !important; }}

/* buttons */
[data-testid="stBaseButton-primary"] {{ background: {RED} !important; border: 1px solid {RED} !important;
  color: #fff !important; border-radius: 10px !important; padding: 8px 26px !important; font-weight: 600; }}
[data-testid="stBaseButton-primary"]:hover {{ background: {RED_DARK} !important; }}
[data-testid="stBaseButton-secondary"] {{ background: #fff !important; border: 1.5px solid {RED} !important;
  color: {RED} !important; border-radius: 10px !important; padding: 8px 22px !important; font-weight: 600; }}
[data-testid="stBaseButton-secondary"]:hover {{ background: {RED_LIGHT} !important; }}
[data-testid="stDownloadButton"] button {{ border-radius: 10px !important; }}

/* cards (siblings, parents) */
[data-testid="stVerticalBlockBorderWrapper"], div[class*="stVerticalBlock"][style*="border"] {{
  border-color: #ececec !important; border-radius: 14px !important; }}

/* checkboxes and expander */
[data-testid="stCheckbox"] label p {{ font-size: .95rem; }}
[data-testid="stExpander"] details {{ border: 1.5px solid #ececec; border-radius: 12px; }}
[data-testid="stExpander"] summary p {{ color: {RED}; font-weight: 600; }}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════ STATE / DEFAULTS ═════════════════════
DEFAULTS = {
    "page": 1,
    # Page 1 – student
    "hide_name": True, "student_name": "", "aub_id": "", "slate_id": "",
    "school_name": "", "residing_in": "", "major": "", "class_year": None,
    "gpa": None, "deferred_payment": None, "outstanding_balance": None,
    "faid_pct": None, "merit_pct": None, "oa": "",
    # Page 3 – siblings / cars / properties
    "sib_ids": [], "next_sib": 0,
    "cars_faid": "", "cars_nef3a": "",
    "props_faid": "", "props_cert": "",
    "comments": "",
}
for p, _ in PARENTS:
    DEFAULTS.update({f"{p}_status": None, f"{p}_employer": "",
                     f"{p}_job": "", f"{p}_income": None})


def sib_keys(sid):
    return {f"sib_{sid}_school": "", f"sib_{sid}_tuition": None,
            f"sib_{sid}_isaub": False, f"sib_{sid}_aubid": "", f"sib_{sid}_faid": None}


for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = copy.deepcopy(v)
for sid in st.session_state.sib_ids:
    for k, v in sib_keys(sid).items():
        st.session_state.setdefault(k, v)

# Keep every answer alive when moving between pages
for k in list(DEFAULTS) + [k for s in st.session_state.sib_ids for k in sib_keys(s)]:
    st.session_state[k] = st.session_state[k]

S = st.session_state


# ══════════════════════ FIELD HELPERS ═════════════════════════
# The field name is shown in gray inside the box until the user types.
def text_field(label, key, **kw):
    st.text_input(label, key=key, placeholder=label, label_visibility="collapsed", **kw)


def number_field(label, key, **kw):
    st.number_input(label, key=key, placeholder=label, label_visibility="collapsed", **kw)


def money_field(label, key):
    number_field(label, key, min_value=0.0, step=100.0, format="%.2f")


def pct_field(label, key):
    number_field(label, key, min_value=0.0, max_value=100.0, step=1.0, format="%.1f")


def select_field(label, options, key):
    st.selectbox(label, options, key=key, index=None, placeholder=label,
                 label_visibility="collapsed")


def area_field(label, key, height=100):
    st.text_area(label, key=key, placeholder=label, height=height, label_visibility="collapsed")


def section(title):
    st.markdown(f"<div class='sec'>{title}</div>", unsafe_allow_html=True)


def sub(title):
    st.markdown(f"<div class='sub'>{title}</div>", unsafe_allow_html=True)


def stepper(current):
    parts = []
    for i, name in enumerate(STEPS, 1):
        state = "done" if i < current else "active" if i == current else ""
        mark = "✓" if i < current else str(i)
        parts.append(f"<div class='step {state}'><div class='dot'>{mark}</div>"
                     f"<div class='lbl'>{name}</div></div>")
        if i < len(STEPS):
            parts.append(f"<div class='line {'done' if i < current else ''}'></div>")
    st.markdown(f"<div class='stepper'>{''.join(parts)}</div>", unsafe_allow_html=True)


# ═════════════════════════ HELPERS ════════════════════════════
def go(page):
    S.page = page


def add_sib():
    sid = S.next_sib
    S.next_sib += 1
    S.sib_ids = S.sib_ids + [sid]
    for k, v in sib_keys(sid).items():
        S[k] = v


def remove_sib(sid):
    S.sib_ids = [s for s in S.sib_ids if s != sid]
    for k in sib_keys(sid):
        S.pop(k, None)


def reset_form():
    for k in list(S.keys()):
        del S[k]


def txt(v):
    return v.strip() if isinstance(v, str) and v.strip() else "—"


def opt(v):
    return v if v else "—"


def money(v):
    return "—" if v is None else f"${v:,.0f}"


def pct(v):
    return "—" if v is None else f"{v:g}%"


def raw(v):
    return "" if v is None else v


def shown_name():
    if not S.student_name.strip():
        return "—"
    return "•••••• (hidden)" if S.hide_name else S.student_name.strip()


def parent_works(p):
    return S[f"{p}_status"] in ("Employed", "Self-Employed")


def siblings_summary():
    parts = []
    for n, sid in enumerate(S.sib_ids, 1):
        line = (f"Sibling {n}: School={txt(S[f'sib_{sid}_school'])}; "
                f"Tuition={money(S[f'sib_{sid}_tuition'])}")
        if S[f"sib_{sid}_isaub"]:
            line += (f"; AUB ID={txt(S[f'sib_{sid}_aubid'])}; "
                     f"AUB FAID={pct(S[f'sib_{sid}_faid'])}")
        else:
            line += "; Not at AUB"
        parts.append(line)
    return parts


# ═══════════════════════ PRINTING ═════════════════════════════
def build_print_html():
    """A clean, modern, A4-ready copy of every answer in the form (AUB red & white)."""
    e = lambda v: html.escape(str(v))

    if not S.student_name.strip():
        name = "—"
    elif S.hide_name and not PRINT_HIDDEN_NAMES:
              name = "Case"
    else:
        name = S.student_name.strip()

    def tile(label, value, wide=False):
        v = value if str(value).strip() else "—"
        empty = " empty" if v == "—" else ""
        return (f"<div class='tile{' wide' if wide else ''}'><div class='lbl'>{e(label)}</div>"
                f"<div class='val{empty}'>{e(v)}</div></div>")

    def stat(label, value):
        empty = " empty" if value == "—" else ""
        return f"<div class='stat'><div class='num{empty}'>{e(value)}</div><div class='lbl'>{e(label)}</div></div>"

    def pill(value):
        if not value or value == "—":
            return "<span class='pill none'>Not specified</span>"
        cls = {"Yes": "yes", "No": "no", "Employed": "yes", "Self-Employed": "yes",
               "Unemployed": "no"}.get(value, "none")
        return f"<span class='pill {cls}'>{e(value)}</span>"

    def note(label, value):
        body = e(value.strip()) if value.strip() else "<span class='empty'>Nothing listed</span>"
        return f"<div class='note'><div class='lbl'>{e(label)}</div><div class='txt'>{body}</div></div>"

    # ── student ──
    student_tiles = "".join([
        tile("AUB ID", txt(S.aub_id)), tile("Slate ID", txt(S.slate_id)),
        tile("Class", opt(S.class_year)), tile("Major", txt(S.major)),
        tile("School name", txt(S.school_name)), tile("Residing in", txt(S.residing_in)),
    ])
    stats = "".join([
        stat("Cumulative GPA", "—" if S.gpa is None else f"{S.gpa:.2f}"),
        stat("FAID", pct(S.faid_pct)),
        stat("Merit", pct(S.merit_pct)),
        stat("Outstanding balance", money(S.outstanding_balance)),
    ])
    finance_tiles = (
        f"<div class='tile'><div class='lbl'>Deferred payment</div><div class='val'>{pill(S.deferred_payment)}</div></div>"
        + tile("O&A", txt(S.oa), wide=True)
    )

    # ── parents ──
    parents = ""
    for p, label in PARENTS:
        works = parent_works(p)
        parents += (
            f"<div class='card'><div class='card-h'><span>{label}</span>{pill(S[f'{p}_status'])}</div>"
            "<div class='grid g1'>"
            + tile("Employer", txt(S[f"{p}_employer"]) if works else "—")
            + tile("Job title", txt(S[f"{p}_job"]) if works else "—")
            + tile("Annual income", money(S[f"{p}_income"]))
            + "</div></div>"
        )

    # ── siblings ──
    if S.sib_ids:
        rows = ""
        for n, sid in enumerate(S.sib_ids, 1):
            aub = S[f"sib_{sid}_isaub"]
            rows += (
                f"<tr><td class='n'>{n}</td><td>{e(txt(S[f'sib_{sid}_school']))}</td>"
                f"<td>{e(money(S[f'sib_{sid}_tuition']))}</td>"
                f"<td>{pill('Yes' if aub else 'No')}</td>"
                f"<td>{e(txt(S[f'sib_{sid}_aubid'])) if aub else '—'}</td>"
                f"<td>{e(pct(S[f'sib_{sid}_faid'])) if aub else '—'}</td></tr>"
            )
        siblings = ("<table><thead><tr><th>#</th><th>School name</th><th>Tuition fees</th>"
                    "<th>AUB student</th><th>AUB ID</th><th>FAID % in AUB</th></tr></thead>"
                    f"<tbody>{rows}</tbody></table>")
    else:
        siblings = "<div class='emptybox'>No siblings listed</div>"

    printed = datetime.now().strftime("%d %b %Y, %H:%M")

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>{e(FORM_TITLE)} - {e(txt(S.aub_id))}</title>
<style>
  @page {{ size: A4; margin: 11mm 12mm; }}
  * {{ box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  body {{ margin: 0; font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
         font-size: 10.5px; color: #1f2328; background: #fff; }}

  .top {{ background: linear-gradient(120deg, {RED} 0%, {RED_DARK} 100%); color: #fff;
          border-radius: 12px; padding: 14px 18px; display: flex; justify-content: space-between;
          align-items: flex-end; }}
  .top .kicker {{ font-size: 9px; letter-spacing: 1.6px; text-transform: uppercase; opacity: .8; }}
  .top h1 {{ margin: 2px 0 0; font-size: 19px; font-weight: 700; letter-spacing: .2px; }}
  .top .meta {{ text-align: right; font-size: 9.5px; opacity: .9; line-height: 1.5; }}

  .hero {{ display: flex; align-items: center; gap: 14px; padding: 12px 4px 4px; }}
  .avatar {{ width: 40px; height: 40px; border-radius: 50%; background: {RED_LIGHT}; color: {RED};
             display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 16px;
             border: 1.5px solid #ecd3dc; flex: none; }}
  .hero .who {{ font-size: 16px; font-weight: 700; }}
  .hero .sub {{ color: #6b7280; font-size: 10px; margin-top: 1px; }}

  h2 {{ display: flex; align-items: center; gap: 8px; font-size: 11px; font-weight: 700;
        color: {RED}; text-transform: uppercase; letter-spacing: 1.1px; margin: 14px 0 7px; }}
  h2 .no {{ background: {RED}; color: #fff; border-radius: 6px; width: 18px; height: 18px;
            display: inline-flex; align-items: center; justify-content: center; font-size: 10px; }}
  h2::after {{ content: ""; flex: 1; height: 1px; background: #ecd3dc; }}

  .grid {{ display: grid; gap: 6px; }}
  .g3 {{ grid-template-columns: repeat(3, 1fr); }}
  .g2 {{ grid-template-columns: repeat(2, 1fr); }}
  .g1 {{ grid-template-columns: 1fr; }}
  .tile {{ background: #fafafa; border: 1px solid #eeeeee; border-radius: 9px; padding: 6px 9px; }}
  .tile.wide {{ grid-column: span 2; }}
  .lbl {{ font-size: 8.5px; color: #8a8f98; text-transform: uppercase; letter-spacing: .7px; }}
  .val {{ font-size: 11.5px; font-weight: 600; margin-top: 2px; word-break: break-word; }}
  .empty {{ color: #b5b9c0; font-weight: 400; }}

  .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin-bottom: 6px; }}
  .stat {{ background: {RED_LIGHT}; border: 1px solid #f0d9e2; border-radius: 10px; padding: 8px 10px; }}
  .stat .num {{ font-size: 17px; font-weight: 700; color: {RED}; }}
  .stat .num.empty {{ color: #c9a9b5; }}

  .pill {{ display: inline-block; padding: 2px 9px; border-radius: 999px; font-size: 9.5px; font-weight: 600; }}
  .pill.yes {{ background: {RED}; color: #fff; }}
  .pill.no {{ background: #f1f1f1; color: #555; border: 1px solid #e2e2e2; }}
  .pill.none {{ background: #fff; color: #9aa0a6; border: 1px dashed #d5d5d5; font-weight: 400; }}

  .two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
  .card {{ border: 1px solid #eeeeee; border-radius: 12px; padding: 9px; background: #fff; }}
  .card-h {{ display: flex; justify-content: space-between; align-items: center;
             font-weight: 700; font-size: 12px; margin: 0 2px 7px; }}

  table {{ width: 100%; border-collapse: separate; border-spacing: 0; border: 1px solid #eeeeee;
           border-radius: 10px; overflow: hidden; }}
  th {{ background: {RED}; color: #fff; font-size: 9px; text-transform: uppercase; letter-spacing: .6px;
        text-align: left; padding: 6px 8px; font-weight: 600; }}
  td {{ padding: 6px 8px; border-top: 1px solid #f0f0f0; font-weight: 500; }}
  tbody tr:nth-child(even) td {{ background: #fafafa; }}
  td.n {{ color: {RED}; font-weight: 700; width: 22px; }}

  .note {{ border: 1px solid #eeeeee; border-left: 3px solid {RED}; border-radius: 9px;
           padding: 7px 10px; background: #fff; }}
  .note .txt {{ margin-top: 3px; font-size: 11px; white-space: pre-wrap; min-height: 26px; }}
  .note.full .txt {{ min-height: 40px; }}
  .emptybox {{ border: 1px dashed #dcdcdc; border-radius: 10px; padding: 9px; text-align: center;
               color: #9aa0a6; }}

  section {{ break-inside: avoid; }}
  footer {{ margin-top: 16px; padding-top: 7px; border-top: 1px solid #eeeeee; display: flex;
            justify-content: space-between; color: #9aa0a6; font-size: 8.5px; }}
</style></head><body>

<div class="top">
  <div><div class="kicker">{e(FORM_SUBTITLE)}</div><h1>{e(FORM_TITLE)}</h1></div>
  <div class="meta">Printed {printed}<br>AUB ID: <b>{e(txt(S.aub_id))}</b></div>
</div>

<div class="hero">
  <div class="avatar">{e(name[0].upper() if name not in ("—", "Case") else "•")}</div>
  <div><div class="who">{e(name)}</div>
  <div class="sub">{e(txt(S.major))} · {e(opt(S.class_year))}</div></div>
</div>

<section><h2><span class="no">1</span>Student Information</h2>
  <div class="grid g3">{student_tiles}</div></section>

<section><h2><span class="no">2</span>Academic &amp; Financial Standing</h2>
  <div class="stats">{stats}</div>
  <div class="grid g3">{finance_tiles}</div></section>

<section><h2><span class="no">3</span>Parents</h2><div class="two">{parents}</div></section>

<section><h2><span class="no">4</span>Siblings</h2>{siblings}</section>

<section><h2><span class="no">5</span>Cars</h2><div class="two">
  {note("From FAID application", S.cars_faid)}{note("From Nef3a application", S.cars_nef3a)}</div></section>

<section><h2><span class="no">6</span>Properties</h2><div class="two">
  {note("On FAID application", S.props_faid)}{note("From Certificate of Ownership", S.props_cert)}</div></section>

<section><h2><span class="no">7</span>Additional Comments</h2>
  <div class="note full"><div class="txt">{e(S.comments.strip()) if S.comments.strip() else "<span class='empty'>No comments</span>"}</div></div></section>

<footer><span>{e(FORM_TITLE)} · {e(FORM_SUBTITLE)}</span><span>Confidential</span></footer>
</body></html>"""


def print_buttons(where):
    doc = build_print_html()
    doc_js = json.dumps(doc).replace("</", "<\\/")
    button_html = f"""<style>body{{margin:0;}}</style>
<button id="p" style="font:600 15px 'Source Sans Pro',sans-serif;padding:9px 24px;border-radius:10px;
  border:1px solid {RED};background:{RED};color:#fff;cursor:pointer;">🖨 Print form</button>
<script>
document.getElementById('p').onclick = function () {{
  var old = document.getElementById('pf'); if (old) old.remove();
  var f = document.createElement('iframe');
  f.id = 'pf';
  f.style.cssText = 'position:fixed;width:0;height:0;border:0;';
  document.body.appendChild(f);
  f.onload = function () {{ f.contentWindow.focus(); f.contentWindow.print(); }};
  f.srcdoc = {doc_js};
}};
</script>"""
    if hasattr(st, "iframe"):          # newer Streamlit
        st.iframe(button_html, height=52)
    else:                              # older Streamlit
        import streamlit.components.v1 as components
        components.html(button_html, height=52)
    st.download_button("⬇ Download a copy", doc, mime="text/html",
                       file_name=f"aid_form_{S.aub_id.strip() or S.slate_id.strip() or 'record'}.html",
                       key=f"dl_print_{where}",
                       help="Saves the form as a file you can open in your browser and print later (Ctrl+P).")


# ═════════════════════════ HEADER ═════════════════════════════
st.markdown(f"<div class='aub-header'><div class='t'>{FORM_TITLE}</div>"
            f"<div class='s'>{FORM_SUBTITLE}</div></div>", unsafe_allow_html=True)

stepper(S.page)

# ═════════════════════════ PAGE 1 ═════════════════════════════
if S.page == 1:
    section("Student Information")

    text_field("Student name", "student_name", autocomplete="off")
    if S.hide_name:
        st.markdown("<style>input[aria-label='Student name']{-webkit-text-security:disc;}</style>",
                    unsafe_allow_html=True)
    text_field("AUB ID", "aub_id")
    text_field("Slate ID", "slate_id")
    text_field("School name", "school_name")
    text_field("Residing in", "residing_in")
    text_field("Major", "major")
    select_field("Class", CLASSES, "class_year")
    number_field("Cumulative GPA (0.00 – 4.30)", "gpa",
                 min_value=0.0, max_value=4.3, step=0.01, format="%.2f")

    section("Financial Standing")
    select_field("Deferred payment", ["Yes", "No"], "deferred_payment")
    money_field("Outstanding balance (USD)", "outstanding_balance")
    pct_field("FAID %", "faid_pct")
    pct_field("Merit %", "merit_pct")
    text_field("O&A", "oa")

    st.write("")
    if st.button("Next →", type="primary"):
        errors = []
        if not S.aub_id.strip() and not S.slate_id.strip():
            errors.append("Enter at least an AUB ID or a Slate ID.")
        if S.aub_id.strip() and not S.aub_id.strip().isdigit():
            errors.append("AUB ID must contain digits only.")
        if errors:
            for e in errors:
                st.error(e)
        else:
            go(2)
            st.rerun()

# ═════════════════════════ PAGE 2 ═════════════════════════════
elif S.page == 2:
    for p, label in PARENTS:
        section(f"{label}")
        select_field("Employment status", STATUSES, f"{p}_status")
        if parent_works(p):
            text_field("Employer" if S[f"{p}_status"] == "Employed" else "Employer / business name",
                       f"{p}_employer")
            text_field("Job title", f"{p}_job")
        money_field("Annual income (USD)", f"{p}_income")

    st.write("")
    b1, _, b2 = st.columns([1, 2, 1])
    if b1.button("← Back"):
        go(1)
        st.rerun()
    with b2:
        if st.button("Next →", type="primary"):
            go(3)
            st.rerun()

# ═════════════════════════ PAGE 3 ═════════════════════════════
elif S.page == 3:
    # ── Siblings ──
    section("Siblings")
    if not S.sib_ids:
        st.markdown("<div class='hint'>No siblings added yet.</div>", unsafe_allow_html=True)
    for n, sid in enumerate(S.sib_ids, 1):
        with st.container(border=True):
            sub(f"Sibling {n}")
            text_field("School name", f"sib_{sid}_school")
            money_field("Tuition fees (USD)", f"sib_{sid}_tuition")
            if st.checkbox("AUB student", key=f"sib_{sid}_isaub"):
                text_field("AUB ID", f"sib_{sid}_aubid")
                pct_field("FAID % in AUB", f"sib_{sid}_faid")
            st.button(f"Remove sibling {n}", on_click=remove_sib, args=(sid,))
    st.button("＋ Add sibling", on_click=add_sib)

    # ── Cars ──
    section("Cars")
    area_field("Cars from FAID application", "cars_faid")
    area_field("Cars from Nef3a application", "cars_nef3a")

    # ── Properties ──
    section("Properties")
    area_field("Properties on FAID application", "props_faid")
    area_field("Properties from Certificate of Ownership", "props_cert")

    # ── Comments ──
    section("Additional Comments")
    area_field("Comments / additional comments", "comments", height=130)

    # ── Review ──
    section("Review & Print")
    with st.expander("Review all answers before printing"):
        st.markdown(f"""
**Student**
- Name: {shown_name()}
- AUB ID: {txt(S.aub_id)} | Slate ID: {txt(S.slate_id)}
- School: {txt(S.school_name)} | Residing in: {txt(S.residing_in)}
- Major: {txt(S.major)} | Class: {opt(S.class_year)}
- GPA: {'—' if S.gpa is None else f'{S.gpa:.2f}'}
- Deferred payment: {opt(S.deferred_payment)} | Outstanding balance: {money(S.outstanding_balance)}
- FAID: {pct(S.faid_pct)} | Merit: {pct(S.merit_pct)} | O&A: {txt(S.oa)}
""")
        for p, label in PARENTS:
            extra = (f" | Employer: {txt(S[f'{p}_employer'])} | Job: {txt(S[f'{p}_job'])}"
                     if parent_works(p) else "")
            st.markdown(f"**{label}:** {opt(S[f'{p}_status'])}{extra} | "
                        f"Income: {money(S[f'{p}_income'])}")
        st.markdown("**Siblings:** " + ("None" if not S.sib_ids else ""))
        for line in siblings_summary():
            st.markdown(f"- {line}")
        st.markdown(f"""
**Cars** — FAID: {txt(S.cars_faid)} | Nef3a: {txt(S.cars_nef3a)}

**Properties** — FAID: {txt(S.props_faid)} | Certificate: {txt(S.props_cert)}

**Comments** — {txt(S.comments)}
""")

    st.markdown("<div class='hint'>In the print window, choose your printer, or choose "
                "<b>Save as PDF</b> to keep a copy on your computer.</div>", unsafe_allow_html=True)
    print_buttons("page3")

    st.write("")
    b1, _, b2 = st.columns([1, 2, 1])
    if b1.button("← Back"):
        go(2)
        st.rerun()
    with b2:
        if st.button("New form", type="primary",
                     help="Clears all fields. Print or save the current form first."):
            reset_form()
            st.rerun()
