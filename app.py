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
    "hide_name": False, "student_name": "", "aub_id": "", "slate_id": "",
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
    """A clean, A4-ready copy of every answer in the form, in AUB red and white."""
    e = lambda v: html.escape(str(v))

    if not S.student_name.strip():
        name = "—"
    elif S.hide_name and not PRINT_HIDDEN_NAMES:
        name = "Hidden (privacy)"
    else:
        name = S.student_name.strip()

    def rows(pairs):
        return "".join(f"<tr><th>{e(k)}</th><td>{e(v)}</td></tr>" for k, v in pairs)

    student = rows([
        ("Student name", name), ("AUB ID", txt(S.aub_id)), ("Slate ID", txt(S.slate_id)),
        ("School name", txt(S.school_name)), ("Residing in", txt(S.residing_in)),
        ("Major", txt(S.major)), ("Class", opt(S.class_year)),
        ("Cumulative GPA", "—" if S.gpa is None else f"{S.gpa:.2f}"),
        ("Deferred payment", opt(S.deferred_payment)),
        ("Outstanding balance", money(S.outstanding_balance)),
        ("FAID %", pct(S.faid_pct)), ("Merit %", pct(S.merit_pct)), ("O&A", txt(S.oa)),
    ])

    parents = ""
    for p, label in PARENTS:
        works = parent_works(p)
        parents += f"<div class='half'><h3>{label}</h3><table>" + rows([
            ("Employment status", opt(S[f"{p}_status"])),
            ("Employer", txt(S[f"{p}_employer"]) if works else "—"),
            ("Job title", txt(S[f"{p}_job"]) if works else "—"),
            ("Annual income", money(S[f"{p}_income"])),
        ]) + "</table></div>"

    if S.sib_ids:
        sib_rows = ""
        for n, sid in enumerate(S.sib_ids, 1):
            aub = S[f"sib_{sid}_isaub"]
            sib_rows += (
                f"<tr><td>{n}</td><td>{e(txt(S[f'sib_{sid}_school']))}</td>"
                f"<td>{e(money(S[f'sib_{sid}_tuition']))}</td><td>{'Yes' if aub else 'No'}</td>"
                f"<td>{e(txt(S[f'sib_{sid}_aubid'])) if aub else '—'}</td>"
                f"<td>{e(pct(S[f'sib_{sid}_faid'])) if aub else '—'}</td></tr>"
            )
        siblings = ("<table class='grid'><tr><th>#</th><th>School name</th><th>Tuition fees</th>"
                    "<th>AUB student</th><th>AUB ID</th><th>FAID % in AUB</th></tr>"
                    f"{sib_rows}</table>")
    else:
        siblings = "<p class='muted'>No siblings listed.</p>"

    def box(title, value):
        v = e(value.strip()) if value.strip() else "<span class='muted'>—</span>"
        return f"<div class='half'><h3>{title}</h3><div class='box'>{v}</div></div>"

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>{e(FORM_TITLE)}</title>
<style>
  @page {{ size: A4; margin: 12mm; }}
  * {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  body {{ font-family: Arial, Helvetica, sans-serif; font-size: 11.5px; color: #1f1f1f; margin: 0; }}
  header {{ background: {RED}; color: #fff; padding: 12px 16px; border-radius: 6px;
           display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 10px; }}
  header h1 {{ font-size: 18px; margin: 0; }}
  header .s {{ font-size: 11px; opacity: .9; }}
  h2 {{ font-size: 13px; color: {RED}; border-bottom: 2px solid {RED};
        padding-bottom: 3px; margin: 14px 0 7px; }}
  h3 {{ font-size: 12px; margin: 4px 0; color: #333; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ border: 1px solid #e3c9d2; padding: 4px 6px; text-align: left; vertical-align: top; }}
  th {{ width: 42%; background: {RED_LIGHT}; font-weight: 600; }}
  table.grid th {{ width: auto; background: {RED}; color: #fff; border-color: {RED}; }}
  .row {{ display: flex; gap: 12px; }}
  .half {{ flex: 1; }}
  .box {{ border: 1px solid #e3c9d2; min-height: 40px; padding: 5px 6px; white-space: pre-wrap; }}
  .muted {{ color: #888; }}
  .sign {{ display: flex; gap: 30px; margin-top: 30px; }}
  .sign div {{ flex: 1; border-top: 1px solid #1f1f1f; padding-top: 4px; }}
  section {{ break-inside: avoid; }}
</style></head><body>
<header><div><h1>{e(FORM_TITLE)}</h1><div class="s">{e(FORM_SUBTITLE)}</div></div>
<div class="s">Printed {datetime.now().strftime("%d/%m/%Y %H:%M")}</div></header>
<section><h2>1. Student Information</h2><table>{student}</table></section>
<section><h2>2. Parents</h2><div class="row">{parents}</div></section>
<section><h2>3. Siblings</h2>{siblings}</section>
<section><h2>4. Cars</h2><div class="row">
  {box("From FAID application", S.cars_faid)}{box("From Nef3a application", S.cars_nef3a)}</div></section>
<section><h2>5. Properties</h2><div class="row">
   {box("On FAID application", S.props_faid)}{box("From Certificate of Ownership", S.props_cert)}</div></section>
<section><h2>6. Additional Comments</h2><div class="row">{box("Comments", S.comments)}</div></section>
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
    st.checkbox("🔒 Hide name for privacy", key="hide_name")
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
