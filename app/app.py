"""Streamlit demo: semantic shortlist for campus placement. Everything runs on this laptop (local Ollama + local embeddings).

    streamlit run app/app.py          (or scripts\\run_demo.bat)
"""
import csv
import html
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st  # noqa: E402

st.set_page_config(page_title="PlaceIQ demo", layout="wide", initial_sidebar_state="expanded")

import data_access as da  # noqa: E402
import ui  # noqa: E402
from stats import paired  # noqa: E402
from src import extensions as ex  # noqa: E402  (prototype extensions: full list, student view)
from src import student_view as sv  # noqa: E402

MODE_LABELS = {"hybrid": "Hybrid (BM25 + dense), post-hoc variant", "dense": "Dense only (paper main configuration)"}
ui.load_css()


# ------------------------------------------------------------------ sidebar
@st.fragment(run_every=5)
def status_fragment():
    status = da.llm_status()
    ui.status_badge(status)
    prev = st.session_state.get("_last_status")
    st.session_state["_last_status"] = status
    # a full rerun only when the offline state flips (it enables/disables custom Run); warming -> ready just updates the badge,
    # so a click that coincides with it is never lost
    if prev is not None and (prev == "offline") != (status == "offline"):
        st.rerun()


def sample_options():
    reqs = da.requirements()
    ids = [r["id"] for r in reqs]
    rec = [i for i in da.DEMO_EXAMPLES if i in ids]
    return rec + [i for i in ids if i not in rec], {r["id"]: r["text"] for r in reqs}


def sample_label(rid, texts):
    title = da.requirement_title(rid, texts[rid])
    return f"Recommended demo: {title} ({rid})" if rid in da.DEMO_EXAMPLES else f"{title} ({rid})"


with st.sidebar:
    ui.brand()
    status_fragment()
    status = da.llm_status()
    st.markdown('<div class="side-note">Everything runs on this device: a local language model (Ollama) and a local '
                'embedding model. No resume or requirement leaves the laptop.</div>', unsafe_allow_html=True)
    st.divider()
    source = st.radio("Requirement", ["Sample requirement", "Custom requirement"], key="source", label_visibility="collapsed")
    ids, texts = sample_options()
    if source == "Sample requirement":
        st.caption("Recommended demo examples are listed first.")
        sample_id = st.selectbox("Sample requirement", ids, key="sample", format_func=lambda i: sample_label(i, texts))
        st.text_area("Requirement text", texts[sample_id], height=190, disabled=True, key="sample_text")
        text = texts[sample_id]
    else:
        sample_id = None
        text = st.text_area("Requirement text", key="custom_text", height=190, placeholder="Paste a hiring requirement in any style "
                            "(formal, WhatsApp, Hinglish...). Include CGPA, branch and backlog rules if you have them.")
    mode = st.radio("Retrieval mode", list(MODE_LABELS), key="mode", format_func=lambda m: MODE_LABELS[m])
    gt_on = False
    if source == "Sample requirement":
        gt_on = st.toggle("Reveal synthetic ground truth (demo data only)", key="gt")
    else:
        st.caption("Ground truth is only available for sample requirements.")
    custom_blocked = source == "Custom requirement" and (status == "offline" or not text.strip())
    run = st.button("Run", type="primary", width="stretch", disabled=custom_blocked, key="run")
    if source == "Custom requirement" and status == "offline":
        ui.notice("warn", "The local LLM is offline, so custom requirements cannot be scored. Start <b>ollama serve</b> "
                          "or use the sample requirements (they run from the cache).")
    elif source == "Custom requirement" and not text.strip():
        st.caption("Enter a requirement to enable Run.")
    elif source == "Custom requirement":
        st.caption("A live run scores 20 candidates and takes about 50 seconds.")
    run_full = st.button("Run full list (about 2 min)", width="stretch", disabled=custom_blocked, key="run_full")
    st.caption("Prototype: scores the 50 best hybrid-retrieval candidates and lists all that are suited. Shown in the "
               "'All suited candidates' tab.")

# ------------------------------------------------------------------ run
st.markdown("## Find the right students, not just the right keywords")
progress_slot = st.empty()
if run:
    bar = progress_slot.progress(0.0, text="Starting")

    def on_progress(i, n, msg):
        bar.progress(min(1.0, i / max(n, 1)), text=msg)

    try:
        result = da.run_pipeline(text, mode, on_progress)
    except Exception as e:  # parser/LLM unreachable, cache miss while offline, ...
        result = dict(error=str(e)[:300])
    result.update(source=source, req_id=sample_id, mode=mode)
    st.session_state["result"] = result
    progress_slot.empty()

if run_full:
    bar = progress_slot.progress(0.0, text="Starting full list")

    def on_full_progress(i, n, elapsed, eta):
        left = "estimating..." if eta is None else f"about {eta:.0f} s left"
        bar.progress(min(1.0, i / max(n, 1)), text=f"Scoring candidate {min(i + 1, n)} of {n} · {elapsed:.0f} s elapsed · {left}")

    try:
        full = ex.shortlist_full(text, progress=on_full_progress)
    except Exception as e:  # LLM offline, parser failure, ...
        full = dict(error=str(e)[:300])
    full.update(requirement=text, source=source, req_id=sample_id)
    st.session_state["full"] = full
    progress_slot.empty()

result = st.session_state.get("result")
res = da.resources()
students = res["students"]

tab_short, tab_ats, tab_full, tab_student, tab_evid, tab_fair = st.tabs(
    ["Shortlist", "Keyword ATS vs Ours", "All suited candidates", "Student view", "Evidence", "Fairness and limits"])


def need_result():
    if result is None:
        ui.empty_state("No requirement run yet", "Pick a sample requirement in the sidebar (or paste your own) and press Run.")
        return False
    if "error" in result:
        ui.notice("err", "The run could not be completed: " + result["error"] + "<br>If the local LLM is offline, start "
                         "<b>ollama serve</b>; sample requirements work from the cache.")
        return False
    if result.get("empty"):
        ui.empty_state("No eligible students match these rules", "The CGPA, branch and backlog rules in this requirement exclude every student. "
                       "Relax one of them and run again.")
        return False
    return True


def header_line():
    where = f"sample {result['req_id']}" if result["source"] == "Sample requirement" else "custom requirement"
    post = '<span class="chip nice" style="margin-left:.5rem">post-hoc exploratory variant</span>' if result["mode"] == "hybrid" else ""
    st.markdown(f'<div style="color:#5a6180;margin-bottom:.6rem">Showing results for {where} &middot; {html.escape(MODE_LABELS[result["mode"]])}{post}</div>',
                unsafe_allow_html=True)


def gt_set():
    if gt_on and result and result.get("source") == "Sample requirement" and result.get("req_id"):
        return da.qualified_set(result["req_id"])
    return None


# ------------------------------------------------------------------ tab 1: shortlist
with tab_short:
    if need_result():
        header_line()
        top = result["ranked"][:da.SHORTLIST]
        ui.funnel(result["n_students"], len(result["eligible"]), len(result["pool"]), len(top))
        ui.understood_panel(result["parsed"])
        qual = gt_set()
        for rank, entry in enumerate(top, 1):
            s = students[entry["id"]]
            ui.candidate_card(rank, s, entry, gt=(entry["id"] in qual) if qual is not None else None)
            with st.expander(f"Show resume: {s['name']}"):
                st.text(s["resume_text"])
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["rank", "student_id", "name", "branch", "cgpa", "active_backlogs", "score", "matched_skills", "missing_skills", "explanation"])
        for rank, e in enumerate(top, 1):
            s = students[e["id"]]
            w.writerow([rank, s["id"], s["name"], s["branch"], s["cgpa"], s["active_backlogs"], "" if e["score"] is None else e["score"],
                        "; ".join(e["matched"]), "; ".join(e["missing"]), e["explanation"]])
        st.download_button("Download shortlist (CSV)", buf.getvalue(), file_name="shortlist.csv", mime="text/csv", key="dl")
        st.caption("Decision support only: a person reviews every shortlist. Students and resumes are synthetic.")

# ------------------------------------------------------------------ tab 2: ATS vs ours
with tab_ats:
    if need_result():
        header_line()
        parsed, ats = result["parsed"], result["ats"]
        passers = set(ats["passers"])
        top = result["ranked"][:da.SHORTLIST]
        rejected = [e for e in top if e["id"] not in passers]
        line = (f"The strict keyword ATS passes <b>{len(passers)}</b> of <b>{len(result['eligible'])}</b> eligible students; "
                f"<b>{len(rejected)}</b> of our top {len(top)} would have been rejected by it.")
        extra = ""
        if gt_on and result.get("source") == "Sample requirement" and result.get("req_id"):
            nq, nrej = da.ats_rejects_qualified(result, result["req_id"])
            extra = f"<small>Ground truth: this requirement has {nq} qualified students; the strict ATS rejects {nrej} of them.</small>"
        st.markdown(f'<div class="summary">{line}{extra}</div>', unsafe_allow_html=True)
        ui.notice("info", "The strict ATS is baseline B1 from the paper: a student passes only if every must-have skill, exactly as the system "
                          "understood it, appears word for word in the resume (case-insensitive, no synonyms). This ATS uses the keywords our parser extracted from the requirement. A real ATS may extract keywords differently.")
        left, right = st.columns(2, gap="large")
        with left:
            st.markdown("### Strict keyword ATS")
            if not ats["ranking"]:
                ui.empty_state("The ATS passes nobody", "No eligible student contains every must-have keyword.")
            for rank, sid in enumerate(ats["ranking"][:da.SHORTLIST], 1):
                s = students[sid]
                st.markdown(f'<div class="card"><div class="cand-head"><div class="rank">#{rank}</div><div class="who"><div class="name">{html.escape(s["name"])}</div>'
                            f'<div class="meta">{s["id"]} &middot; {s["branch"]} &middot; CGPA {s["cgpa"]:.2f}</div></div></div></div>', unsafe_allow_html=True)
        with right:
            st.markdown("### Our shortlist")
            for rank, e in enumerate(top, 1):
                s = students[e["id"]]
                resc = e["id"] not in passers
                why = None
                if resc:
                    miss = da.missing_keywords(parsed, s["resume_text"])
                    why = "Rejected by the ATS: keyword not found in the text: " + (", ".join(f"&ldquo;{html.escape(m)}&rdquo;" for m in miss) or "(passes the keyword rule but not the eligibility rules)")
                ui.candidate_card(rank, s, e, rescued=resc, why=why)

# ------------------------------------------------------------------ tab 3: evidence
with tab_evid:
    st.markdown("## Evidence")
    st.caption("All numbers come from the final evaluation on 10 held-out test requirements (synthetic data); intervals are 95% bootstrap "
               "CIs over requirements. Complete tables: docs/RESULTS.md.")
    main = ["B1", "B1b", "B1c", "B2", "B3", "B3b", "B4"]
    nd = da.method_ci(main, "ndcg10")
    st.markdown("### Ranking quality (nDCG@10)")
    st.plotly_chart(ui.ci_bar(nd, "nDCG@10 (mean, 95% CI)", highlight="B4"), width="stretch")
    pv = da.per_requirement()
    get = lambda m: pv[pv.method == m].sort_values("req_id").ndcg10.tolist()
    p3, p3b = paired(get("B4"), get("B3")), paired(get("B4"), get("B3b"))
    st.markdown(f'<div class="takeaway"><b>Takeaway.</b> Dense retrieval plus LLM re-ranking (B4) has the highest mean nDCG@10 '
                f'({nd[nd.method == "B4"]["mean"].iloc[0]:.3f}); it beats dense-only by {p3["diff"]:+.3f} (95% CI {p3["lo"]:.3f} to {p3["hi"]:.3f}, '
                f'{p3["verdict"]}), but it is <b>{p3b["verdict"]}</b> from a hybrid BM25+dense ranking without any LLM ({p3b["diff"]:+.3f}, '
                f'CI {p3b["lo"]:.3f} to {p3b["hi"]:.3f}). With 10 requirements the intervals are wide.</div>', unsafe_allow_html=True)
    st.dataframe(da.main_table(main), hide_index=True, width="stretch")

    st.markdown("### What a strict keyword filter rejects")
    st.dataframe(da.ats_rejection_by_archetype(), hide_index=True, width="stretch")
    st.markdown('<div class="takeaway"><b>Takeaway.</b> A strict keyword filter rejects more than half of the qualified students, and every '
                'qualified student whose resume only <i>describes</i> the work (paraphrased). Allowing synonyms helps but, even with aliases from the '
                'generator\'s own taxonomy (a generous baseline), no paraphrased resume passes.</div>', unsafe_allow_html=True)

    st.markdown("### Which qualified students reach the top 20, by resume style")
    ash = da.archetype_share()
    archs = [a for a in ["standard", "paraphrased", "implied", "abbreviated_noisy", "sparse_strong", "generalist_average"] if a in set(ash.archetype)]
    names = {"B1c": "Keyword ATS + synonyms", "B2": "BM25", "B3": "Dense (also B4's pool)", "B3b": "Hybrid ranking"}
    st.plotly_chart(ui.archetype_bars(ash, list(names), names, archs), width="stretch")
    st.markdown('<div class="takeaway"><b>Takeaway.</b> The paraphrase gap is a <b>retrieval</b> problem: no method puts more than 6% of the '
                'qualified paraphrased-only students into its top 20, so the re-ranker never sees them. The post-hoc diagnostic below shows the '
                're-ranker itself judges them well when retrieval is bypassed.</div>', unsafe_allow_html=True)

    st.markdown("### Ablations (pre-declared)")
    st.dataframe(da.main_table(["B4", "B4-K50", "B4-oracle", "B4-noFair"], cols=("ndcg10", "mrr", "recall10_cap", "frr10", "frr20")),
                 hide_index=True, width="stretch")
    st.markdown('<div class="takeaway"><b>Takeaway.</b> Using 50 candidates instead of 20, giving the system the true eligibility rules, or removing the '
                'fairness instruction does not change nDCG@10 distinguishably. K=50 mainly lowers the share of qualified students missed in the pool '
                '(FRR@20).</div>', unsafe_allow_html=True)

    st.markdown('<div class="posthoc"><b>Post-hoc exploratory (designed after seeing test results)</b><br>The two analyses below were added after the test '
                'results were known. They were not pre-declared and do not change any main result.</div>', unsafe_allow_html=True)
    ph = da.posthoc_tables()
    b5 = ph["b5"]
    t = b5[b5.split.str.startswith("test")].set_index("metric")
    st.markdown("#### B5: hybrid retrieval + the same LLM re-ranker (post-hoc exploratory)")
    st.dataframe(ph["paired"].rename(columns=dict(comparison="Comparison", metric="Metric", diff_ci="B5 minus baseline [95% CI]",
                                                  win_loss_tie="Win/loss/tie (B5 better = higher; FRR lower)", verdict="Verdict")), hide_index=True, width="stretch")
    pa = ph["arch"]
    tot_found = {m: int(pa[pa.method == m].found_in_pool.sum()) for m in pa.method.unique()}
    tot_q = int(pa[pa.method == pa.method.iloc[0]].qualified.sum())
    st.markdown(f'<div class="takeaway"><b>Takeaway (exploratory).</b> Hybrid retrieval puts {tot_found.get("B5 (hybrid pool)")} of {tot_q} qualified students into the '
                f'pool versus {tot_found.get("B4 (dense pool)")} for the dense pool, and B5\'s nDCG@10 is {t.loc["ndcg10", "mean"]:.3f}. '
                'Against B4 the nDCG@10 difference is <b>not distinguishable</b>; the clear gain is in pool coverage (FRR@20). '
                'Paraphrased-only resumes are still almost never in the pool.</div>', unsafe_allow_html=True)
    st.dataframe(pa.assign(share=lambda d: (d.found_in_pool / d.qualified).map("{:.0%}".format))
                 .pivot(index="method", columns="archetype", values="share").reset_index().rename(columns=dict(method="Pool")),
                 hide_index=True, width="stretch")

    st.markdown("#### D1: can the re-ranker judge paraphrased resumes when retrieval is bypassed? (post-hoc exploratory)")
    d1 = ph["d1"].rename(columns=dict(req_id="Requirement", n_paraphrased_qualified="Paraphrased qualified", n_nonqualified="Non-qualified",
                                       mean_score_pos="Mean score qualified", mean_score_neg="Mean score non-qualified",
                                       mean_score_stuffed="Mean score stuffed", auc="AUC", pos_in_top10="Qualified in top 10"))
    st.dataframe(d1.round(2), hide_index=True, width="stretch")
    st.dataframe(ph["d1s"].rename(columns=dict(metric="Pooled measure", value="Value")), hide_index=True, width="stretch")
    st.markdown('<div class="takeaway"><b>Takeaway (exploratory).</b> When every paraphrased qualified student is placed next to 15 other eligible students, '
                'the re-ranker separates them well and almost always ranks them in the top 10. The weakness of the pipeline on paraphrased resumes '
                'therefore sits in retrieval, not in the re-ranker. The candidate sets are small and the negatives are easy (many are stuffed '
                'resumes), so this is a diagnostic, not a benchmark.</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ tab 4: fairness and limits
with tab_fair:
    st.markdown("## Fairness and limits")
    fs = da.fairness_summary()
    st.markdown("### Does the name change the score?")
    st.plotly_chart(ui.fairness_bars(fs), width="stretch")
    on, off = fs["on"]["abs_score_change"], fs["off"]["abs_score_change"]
    st.markdown(f'<div class="takeaway"><b>Names only; no name effect detected; wide CIs.</b> 100 top-10 candidates (10 requirements) were re-scored with '
                f'their name replaced: a same-group name (control) and names from other groups. Mean absolute score change with the instruction on: control '
                f'{on["control"][0]:.2f}, cross-group {on["cross"][0]:.2f}; instruction off: control {off["control"][0]:.2f}, cross-group '
                f'{off["cross"][0]:.2f} points. In neither condition is the cross-group change distinguishable from the control, and the retrieval '
                f'similarity shifts by the same small amount for both. Most of the change is noise from re-wording the prompt text, not a group effect. '
                f'This does not prove the absence of bias.</div>', unsafe_allow_html=True)
    st.markdown("### Limitations")
    st.markdown('<ul class="limits">'
                '<li><b>Synthetic data.</b> Students, resumes and requirements are generated; real resumes are messier.</li>'
                '<li><b>Circular labels.</b> The ground truth comes from the same generator as the resumes. A human spot-check of 20 pairs agreed with it '
                '(quadratic-weighted kappa 0.96), which is a small sample.</li>'
                '<li><b>Names only.</b> The fairness test swaps names; it does not cover college prestige, gender cues elsewhere in a resume, or other proxies.</li>'
                '<li><b>Paraphrased resumes.</b> Only 2&ndash;6% of qualified paraphrased-only resumes reach the candidate pool (dense 6%, hybrid 4%).</li>'
                '<li><b>Small test set.</b> 10 test requirements, so intervals are wide and many differences are not distinguishable.</li>'
                '<li><b>Decision support only.</b> A human reviews every shortlist; the score is not a hiring decision.</li>'
                '</ul>', unsafe_allow_html=True)

# ------------------------------------------------------------------ prototype extensions (new tabs)
import extension_tabs  # noqa: E402

with tab_full:
    extension_tabs.full_tab(st.session_state.get("full"), students)

with tab_student:
    extension_tabs.student_tab(students, {i: texts[i] for i in ids}, lambda i: sample_label(i, texts), st.session_state.get("full"))
