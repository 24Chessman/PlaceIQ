"""UI for the prototype extensions: 'All suited candidates' (company view) and 'Student view'. Prototype, not evaluated."""
import html

import pandas as pd
import streamlit as st

import ui
from src import extensions as ex
from src import student_view as sv

TOP10_NOTE = "Top 10 here may differ from the Shortlist tab, which uses a dense-only pool; this view uses a hybrid pool."
SUITED_NOTE = ("Suited = re-ranker score at or above the threshold, among the 50 best candidates from hybrid retrieval. "
               "Students outside the pool are not scored.")
PROJECTION_NOTE = "Projection only. It assumes the student genuinely does this work. Not a guarantee."
COVERAGE_NOTE = "This is arithmetic on the skill lists, not a predicted score or rank."
EXPERIMENTAL_NOTE = "The small model's score can go down when text is added; do not read this as a prediction."


def _table(rows, students):
    out = []
    for r in rows:
        s = students[r["id"]]
        out.append({"Rank": r["rank"], "Student": f"{s['name']} ({s['id']})", "Branch": s["branch"],
                    "Score": "not scored" if r["score"] is None else r["score"],
                    "Matched skills": ", ".join(r["matched"]), "Missing skills": ", ".join(r["missing"]),
                    "Explanation": r["explanation"] or (r.get("error") or "")})
    return pd.DataFrame(out)


def full_tab(full, students):
    if full is None:
        ui.empty_state("No full list yet", "Pick a requirement in the sidebar and press 'Run full list (about 2 min)'. "
                       "The quick Top-10 button is unchanged.")
        return
    if "error" in full:
        ui.notice("err", "The full list could not be completed: " + html.escape(full["error"]) +
                  "<br>If the local LLM is offline, start <b>ollama serve</b>.")
        return
    if full["pool_size"] == 0:
        ui.empty_state("No eligible students match these rules", "The CGPA, branch and backlog rules in this requirement exclude every student.")
        return
    threshold = st.slider("Suited threshold (re-ranker score)", 0, 100, ex.THRESHOLD, key="threshold")
    ranked = [dict(r, rank=i) for i, r in enumerate(full["ranked"], 1)]
    ex.label_candidates(ranked, threshold, full["top_n"])
    suited = ex.count_suited(ranked)
    st.markdown(f'<div class="summary">{suited} suited of {full["eligible_count"]} eligible; pool of {full["pool_size"]}'
                f'<small>Prototype extension, not evaluated. Scores come from the same re-ranker as the Shortlist tab.</small></div>',
                unsafe_allow_html=True)
    ui.understood_panel(full["parsed"])
    st.caption(TOP10_NOTE)
    top = [r for r in ranked if r["group"] == ex.GROUPS[0]]
    also = [r for r in ranked if r["group"] == ex.GROUPS[1]]
    st.markdown("### Top 10")
    st.dataframe(_table(top, students), hide_index=True, width="stretch")
    st.markdown(f"### Also suited ({len(also)})")
    if also:
        st.dataframe(_table(also, students), hide_index=True, width="stretch")
    else:
        st.write("No further candidate reaches the threshold.")
    st.caption(SUITED_NOTE)
    st.download_button("Download full list (CSV)", ex.full_list_csv(ranked, students), file_name="full_list.csv", mime="text/csv", key="dl_full")
    st.caption("Decision support only: a person reviews every list. Students and resumes are synthetic.")


def _score_block(scored):
    c = ui.score_color(scored["score"])
    st.markdown(
        f'<div class="card"><div class="cand-head"><div class="who"><div class="name">Current fit score</div></div>'
        f'<div class="score-box"><div class="score" style="color:{c}">{scored["score"]}</div>'
        f'<div class="bar"><span style="width:{scored["score"]}%;background:{c}"></span></div></div></div>'
        f'<div class="chips">{ui.chips(scored["matched_skills"], "ok", "Matched")}{ui.chips(scored["missing_skills"], "miss", "Missing")}</div>'
        f'<p class="expl">{html.escape(scored["explanation"])}</p></div>', unsafe_allow_html=True)


def student_tab(students, req_texts, req_label, full):
    st.markdown("### Student view")
    st.caption("Prototype, not evaluated. A student's fit for a requirement, what is missing, and a what-if projection.")
    c1, c2 = st.columns(2, gap="large")
    sid = c1.selectbox("Student", list(students), format_func=lambda s: f"{s} · {students[s]['name']}", key="sv_student")
    mode = c2.radio("Requirement", ["Benchmark requirement", "Free text"], horizontal=True, key="sv_mode")
    if mode == "Benchmark requirement":
        rid = c2.selectbox("Benchmark requirement", list(req_texts), format_func=req_label, key="sv_req")
        text = req_texts[rid]
    else:
        text = c2.text_area("Requirement text", key="sv_text", height=140, placeholder="Paste a company requirement.")
    student = students[sid]
    if st.button("Check fit", type="primary", key="sv_go", disabled=not text.strip()):
        try:
            from src.parser import parse_requirement
            from src.rerank import score_candidate
            parsed = parse_requirement(text)[0]
            scored = score_candidate(text, parsed, student["resume_text"], True)[0]
            st.session_state["sv"] = dict(sid=sid, text=text, parsed=parsed, scored=scored, suggestions=None, whatif=None)
        except Exception as e:
            st.session_state["sv"] = dict(error=str(e)[:300])
    state = st.session_state.get("sv")
    if state is None:
        ui.empty_state("Nothing checked yet", "Pick a student and a requirement, then press Check fit.")
        return
    if "error" in state:
        ui.notice("err", "The check could not be completed: " + html.escape(state["error"]) + "<br>Start <b>ollama serve</b> if the local LLM is offline.")
        return
    stu, parsed, scored, req = students[state["sid"]], state["parsed"], state["scored"], state["text"]
    st.markdown(f"**{html.escape(stu['name'])} ({stu['id']}, {stu['branch']})** against the requirement: *{html.escape(parsed['role_title'])}*")
    _score_block(scored)
    with st.expander("Show resume"):
        st.text(stu["resume_text"])

    st.markdown("#### Eligibility")
    rows = sv.eligibility_table(parsed, stu)
    st.dataframe(pd.DataFrame([{"Rule": r["rule"], "Required": r["required"], "Student": r["student"],
                                "Result": "Pass" if r["passed"] else "Fail", "Note": "" if r["passed"] else r["note"]} for r in rows]),
                 hide_index=True, width="stretch")
    if not all(r["passed"] for r in rows):
        st.caption("Eligibility rules are hard filters: a failed rule is not fixable by editing the resume.")

    must, nice = sv.skill_gaps(parsed, scored)
    st.markdown("#### Gaps")
    st.markdown(f'<div class="chips">{ui.chips(must, "miss", "Must-have") or "<span class=chiplabel>Must-have</span> none"}</div>'
                f'<div class="chips">{ui.chips(nice, "nice", "Nice-to-have") or "<span class=chiplabel>Nice-to-have</span> none"}</div>',
                unsafe_allow_html=True)

    st.markdown("#### Suggestions")
    if st.button("Get suggestions", key="sv_sugg", disabled=not (must or nice)):
        try:
            state["suggestions"] = sv.suggest_improvements(req, parsed, stu["resume_text"], must, nice)
        except Exception as e:
            ui.notice("err", "Suggestions could not be generated: " + html.escape(str(e)[:200]))
    for item in state.get("suggestions") or []:
        st.markdown(f"- **{html.escape(item['gap'])}**: {html.escape(item['suggestion'])}")
    if not (must or nice):
        st.write("No missing skills to suggest for.")

    st.markdown("#### What if the student gains a skill?")
    gaps = must + [g for g in nice if g not in must]
    chosen = [g for g in gaps if st.checkbox(f"Assume I gain this skill: {g}", key=f"sv_assume_{g}")]
    cov = sv.coverage(parsed, scored, chosen)
    c1, c2 = st.columns(2, gap="large")
    c1.metric("Required skills matched", f"{cov['must']['before']} of {cov['must']['total']}",
              delta=f"{cov['must']['after'] - cov['must']['before']} if gained" if chosen else None)
    c2.metric("Nice-to-have skills matched", f"{cov['nice']['before']} of {cov['nice']['total']}",
              delta=f"{cov['nice']['after'] - cov['nice']['before']} if gained" if chosen else None)
    for line in sv.coverage_text(cov):
        st.write(line)
    st.caption(COVERAGE_NOTE)

    with st.expander("Experimental: re-score with the model", expanded=False):
        st.caption(EXPERIMENTAL_NOTE)
        if st.button("Re-score", key="sv_rescore", disabled=not chosen):
            try:
                state["whatif"] = dict(skills=chosen, **sv.what_if(req, parsed, stu["resume_text"], chosen))
            except Exception as e:
                ui.notice("err", "Re-scoring failed: " + html.escape(str(e)[:200]))
        w = state.get("whatif")
        if w:
            threshold = st.session_state.get("threshold", ex.THRESHOLD)
            saved = full if (full and "error" not in full and full.get("requirement", "").strip() == req.strip()) else ex.load_full_list(req)
            cutoff = sv.top10_cutoff(saved) if saved else None
            before, after = scored, w["scored"]
            st.markdown(f'<div class="notice warn"><b>{PROJECTION_NOTE}</b></div>', unsafe_allow_html=True)
            b, a = st.columns(2, gap="large")
            with b:
                st.markdown("**Before**")
                _score_block(before)
            with a:
                st.markdown(f"**After** (assumed: {html.escape(', '.join(w['skills']))})")
                _score_block(after)
            st.write(sv.position_vs(after["score"], threshold, cutoff))
            if after["score"] <= before["score"]:
                st.caption("The score did not improve. The added bullets are generic and the 4B model's scores can vary between resume "
                           "versions, so a projection can move for reasons unrelated to the added work.")
            if cutoff is None:
                st.caption("Run the full list for this requirement to also compare with the Top-10 cutoff.")
            st.markdown("**Resume text used for the re-score**")  # no nested expander: Streamlit does not allow it
            st.text(w["text"])
