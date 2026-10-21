def build_print_html():
    """A clean, modern, A4-ready copy of every answer in the form (AUB red & white)."""
    e = lambda v: html.escape(str(v))

    if not S.student_name.strip():
        name = "—"
    elif S.hide_name and not PRINT_HIDDEN_NAMES:
        name = "Hidden for privacy"
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
  <div class="avatar">{e(name[0].upper() if name not in ("—", "Hidden for privacy") else "•")}</div>
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


