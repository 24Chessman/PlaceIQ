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
COVERAGE_NOTE = "This is arithmetic on the skill lists, not a predicted score or rank."


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


def _suggestion_card(item):
    """One small card per missing skill; a failed generation shows a plain message, never a template."""
    e = html.escape
    # the Required / Nice-to-have label comes from the parsed requirement (item["kind"]), rendered here, never written by the model
    head = f'<div class="name">{e(item["skill"])} {ui.chips([item["kind"]], "must" if item["kind"] == "Required" else "nice")}</div>'
    if not item.get("ok"):
        st.markdown(f'<div class="card">{head}<p class="expl">{e(item["error"])}</p></div>', unsafe_allow_html=True)
        return
    steps = "".join(f"<li>{e(s)}</li>" for s in item["how_to_learn"])
    st.markdown(
        f'<div class="card">{head}'
        f'<div class="rowlabel">Why it matters</div><p class="expl">{e(item["why_it_matters"])}</p>'
        f'<div class="rowlabel">What to build</div><p class="expl">{e(item["what_to_build"])}</p>'
        f'<div class="rowlabel">How to learn</div><ol class="expl">{steps}</ol>'
        f'<div class="rowlabel">Resume bullet example (use only after you have done the work)</div>'
        f'<p class="expl"><i>{e(item["resume_bullet_example"])}</i></p></div>', unsafe_allow_html=True)


REVISION_LABEL = "Simulated bullets, not the student's work. The student must do the work and write it themselves."
NOISE_NOTE = "A small model's score is noisy and rewards added text; do not read this as a prediction."
RETRIEVAL_NOTE = ("Retrieval figures are computed in memory with the same embedding model and a rebuilt BM25 index; "
                  "the vector index and the student data are not changed.")


def _rescore(state, req, parsed, stu, chosen, full, students, edited):
    """Button callback (runs before the page is drawn). Generates bullets for the ticked skills (first click) or takes the edited text,
    re-scores it with the same re-ranker, and computes the retrieval effect and the placement in the cached full list."""
    try:
        from src import revision as rev
        from src.pipeline import retriever
        from src.rerank import score_candidate
        if edited:
            old = state["revision"]
            bullets, revised = old["bullets"], st.session_state["sv_revised_text"]
        else:
            bullets = rev.generate_bullets(stu["resume_text"], chosen)
            revised, _ = rev.build_revised_text(stu["resume_text"], bullets)
            st.session_state["sv_revised_text"] = revised
        scored_after = score_candidate(req, parsed, revised, True)[0]
        effect = rev.retrieval_effect(parsed, stu["id"], revised, students, retriever())
        saved = full if (full and "error" not in full and full.get("requirement", "").strip() == req.strip()) else ex.load_full_list(req)
        threshold = st.session_state.get("threshold", ex.THRESHOLD)
        place = rev.place_in_full_list(saved, stu["id"], scored_after["score"], effect, threshold) if (saved and effect["eligible"]) else None
        state["revision"] = dict(skills=chosen, bullets=bullets, original=stu["resume_text"], revised=revised, scored=scored_after,
                                 effect=effect, place=place, edited=edited, error=None)
    except Exception as e:
        state["revision"] = dict(error=str(e)[:300])


def _revised_html(original, revised):
    from src import revision as rev
    new = set(rev.added_lines(original, revised))
    rows = []
    for line in revised.split("\n"):
        style = ' style="background:#e7f6ec;border-left:4px solid #15803d;padding:0 .4rem"' if line in new else ""
        rows.append(f"<div{style}>{html.escape(line) or '&nbsp;'}</div>")
    return '<div class="expl" style="font-family:monospace;font-size:.82rem;white-space:pre-wrap">' + "".join(rows) + "</div>"


def _revision_panel(state, parsed, before):
    from src import revision as rev
    r = state["revision"]
    if r.get("error"):
        ui.notice("err", "The re-score could not be completed: " + html.escape(r["error"]) + "<br>Start <b>ollama serve</b> if the local LLM is offline.")
        return
    st.markdown(f'<div class="notice warn"><b>{REVISION_LABEL}</b></div>', unsafe_allow_html=True)
    for b in r["bullets"]:
        if not b["ok"]:
            ui.notice("err", html.escape(b["error"]) + ": no bullet was added for this skill.")
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("**Original resume**")
        st.text(r["original"])
    with right:
        st.markdown("**Revised resume** (additions highlighted)")
        st.markdown(_revised_html(r["original"], r["revised"]), unsafe_allow_html=True)
    st.text_area("Edit the revised resume (then re-score the edited text)", key="sv_revised_text", height=260)
    st.button("Re-score edited text", key="sv_rescore_edit", on_click=_rescore,
              args=(state, st.session_state["sv"]["text"], parsed, st.session_state["_sv_stu"], r["skills"], st.session_state.get("_sv_full"),
                    st.session_state["_sv_students"], True))

    after = r["scored"]
    st.markdown("#### Before and after (model re-score)")
    b, a = st.columns(2, gap="large")
    with b:
        st.markdown("**Before**")
        _score_block(before)
    with a:
        st.markdown("**After** (revised resume" + (", edited" if r["edited"] else "") + ")")
        _score_block(after)
    cb, ca = sv.coverage(parsed, before), sv.coverage(parsed, after)
    st.write(f"Required skills matched by the re-ranker: {cb['must']['before']} of {cb['must']['total']} before, "
             f"{ca['must']['before']} of {ca['must']['total']} after. Nice-to-have: {cb['nice']['before']} of {cb['nice']['total']} before, "
             f"{ca['nice']['before']} of {ca['nice']['total']} after.")
    if after["score"] <= before["score"]:
        st.caption("The score did not improve.")
    st.caption(NOISE_NOTE)

    st.markdown("#### Retrieval effect of the revised text")
    e = r["effect"]
    if not e["eligible"]:
        st.write("This student fails an eligibility rule for this requirement, so they are never retrieved.")
    else:
        st.dataframe(pd.DataFrame([
            {"Measure": "Dense similarity to the query", "Before": f"{e['sim_before']:.3f}", "After": f"{e['sim_after']:.3f}"},
            {"Measure": f"Dense rank among {e['eligible_count']} eligible", "Before": e["dense_rank_before"], "After": e["dense_rank_after"]},
            {"Measure": "BM25 rank", "Before": e["bm25_rank_before"], "After": e["bm25_rank_after"]},
            {"Measure": "Hybrid rank (BM25 + dense, RRF k=60)", "Before": e["hybrid_rank_before"], "After": e["hybrid_rank_after"]},
            {"Measure": f"In the pool of {e['pool']}", "Before": "yes" if e["in_pool_before"] else "no", "After": "yes" if e["in_pool_after"] else "no"},
        ]), hide_index=True, width="stretch")
        if r["place"]:
            st.write(rev.placement_text(r["place"], after["score"]))
        else:
            st.caption("Run the full list for this requirement to also see where the new score would land (Top-10 cutoff and threshold).")
        st.caption(RETRIEVAL_NOTE)


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
        _suggestion_card(item)
    if not (must or nice):
        st.write("No missing skills to suggest for.")

    st.markdown("#### What if the student gains a skill?")
    gaps = must + [g for g in nice if g not in must]
    chosen = [g for g in gaps if st.checkbox(f"Assume I gain this skill: {g}", key=f"sv_assume_{g}")]
    st.session_state.update(_sv_stu=stu, _sv_full=full, _sv_students=students)
    st.button("Re-score with updated resume", type="primary", key="sv_rescore", disabled=not chosen, on_click=_rescore,
              args=(state, req, parsed, stu, chosen, full, students, False))
    st.caption(REVISION_LABEL)
    cov = sv.coverage(parsed, scored, chosen)
    c1, c2 = st.columns(2, gap="large")
    c1.metric("Required skills matched", f"{cov['must']['before']} of {cov['must']['total']}",
              delta=f"{cov['must']['after'] - cov['must']['before']} if gained" if chosen else None)
    c2.metric("Nice-to-have skills matched", f"{cov['nice']['before']} of {cov['nice']['total']}",
              delta=f"{cov['nice']['after'] - cov['nice']['before']} if gained" if chosen else None)
    for line in sv.coverage_text(cov):
        st.write(line)
    st.caption(COVERAGE_NOTE)
    if state.get("revision"):
        _revision_panel(state, parsed, scored)
