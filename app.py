"""
app.py — Streamlit UI for the FOA Pipeline.

Run:
    streamlit run app.py

The app loads pre-processed FOA JSON from ./output/foa_dataset.json.
To refresh data, run run_pipeline.py first.
"""

import json
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Funding Intelligence",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

OUTPUT_PATH = Path(__file__).parent / "output" / "foa_dataset.json"


@st.cache_data
def load_data(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def all_tag_values(records: list[dict], category: str) -> list[str]:
    vals = set()
    for r in records:
        vals.update(r.get("tags", {}).get(category, []))
    return sorted(vals)


def fmt_currency(val) -> str:
    if val is None:
        return "—"
    return f"${int(val):,}"


def fmt_date(val) -> str:
    if not val:
        return "—"
    try:
        return datetime.fromisoformat(val).strftime("%b %d, %Y")
    except Exception:
        return str(val)


def render_sidebar(records: list[dict]):
    st.sidebar.title("🔬 Funding Intelligence")
    st.sidebar.caption("AI-Powered FOA Search & Tagging")
    st.sidebar.divider()

    keyword = st.sidebar.text_input(
        "🔍 Keyword search", placeholder="e.g. machine learning, climate"
    )

    st.sidebar.subheader("Filter by Tags")
    sel_domains = st.sidebar.multiselect(
        "Research Domain", all_tag_values(records, "research_domains")
    )
    sel_methods = st.sidebar.multiselect("Methods", all_tag_values(records, "methods"))
    sel_pops = st.sidebar.multiselect(
        "Populations", all_tag_values(records, "populations")
    )
    sel_themes = st.sidebar.multiselect(
        "Sponsor Themes", all_tag_values(records, "sponsor_themes")
    )

    st.sidebar.subheader("Filter by Source")
    sources = sorted({r.get("source", "") for r in records if r.get("source")})
    sel_sources = st.sidebar.multiselect("Source", sources)

    st.sidebar.divider()
    only_tagged = st.sidebar.checkbox("Only show tagged records")

    return {
        "keyword": keyword.strip().lower(),
        "domains": sel_domains,
        "methods": sel_methods,
        "populations": sel_pops,
        "themes": sel_themes,
        "sources": sel_sources,
        "only_tagged": only_tagged,
    }


def apply_filters(records: list[dict], f: dict) -> list[dict]:
    out = []
    for r in records:
        tags = r.get("tags", {})
        all_tags = (
            tags.get("research_domains", [])
            + tags.get("methods", [])
            + tags.get("populations", [])
            + tags.get("sponsor_themes", [])
        )

        if f["only_tagged"] and not all_tags:
            continue

        if f["keyword"]:
            haystack = " ".join(
                [
                    r.get("title", ""),
                    r.get("description", ""),
                    r.get("agency", ""),
                    r.get("eligibility", ""),
                ]
            ).lower()
            if f["keyword"] not in haystack:
                continue

        if f["domains"] and not any(
            d in tags.get("research_domains", []) for d in f["domains"]
        ):
            continue
        if f["methods"] and not any(m in tags.get("methods", []) for m in f["methods"]):
            continue
        if f["populations"] and not any(
            p in tags.get("populations", []) for p in f["populations"]
        ):
            continue
        if f["themes"] and not any(
            t in tags.get("sponsor_themes", []) for t in f["themes"]
        ):
            continue
        if f["sources"] and r.get("source") not in f["sources"]:
            continue

        out.append(r)
    return out


def render_card(r: dict):
    tags = r.get("tags", {})
    all_tags = (
        tags.get("research_domains", [])
        + tags.get("methods", [])
        + tags.get("populations", [])
        + tags.get("sponsor_themes", [])
    )

    tag_html = (
        " ".join(
            f'<span style="background:#1f4e79;color:white;padding:2px 8px;border-radius:10px;font-size:12px;margin:2px">{t}</span>'
            for t in all_tags
        )
        or '<span style="color:#888;font-size:12px">No tags assigned</span>'
    )

    with st.expander(
        f"**{r.get('title') or 'Untitled'}**  —  {r.get('agency') or 'Unknown Agency'}",
        expanded=False,
    ):
        col1, col2, col3 = st.columns(3)
        col1.metric("Open Date", fmt_date(r.get("open_date")))
        col2.metric("Close Date", fmt_date(r.get("close_date")))
        col3.metric("Award Max", fmt_currency(r.get("award_max")))

        st.markdown("**Semantic Tags**")
        st.markdown(tag_html, unsafe_allow_html=True)

        if r.get("description"):
            st.markdown("**Description**")
            desc = r["description"]
            st.write(desc[:600] + ("..." if len(desc) > 600 else ""))

        if r.get("eligibility"):
            with st.popover("Eligibility details"):
                st.write(r["eligibility"])

        cols = st.columns([1, 1, 2])
        if r.get("source_url"):
            cols[0].link_button("🔗 Source", r["source_url"])
        cols[1].caption(f"Source: `{r.get('source', '—')}`")
        cols[2].caption(f"ID: `{r.get('foa_id', '—')}`")


def render_metrics(records: list[dict], filtered: list[dict]):
    tagged = sum(
        1
        for r in filtered
        if any(
            r.get("tags", {}).get(k)
            for k in ["research_domains", "methods", "populations", "sponsor_themes"]
        )
    )
    total_tags = sum(
        len(r.get("tags", {}).get("research_domains", []))
        + len(r.get("tags", {}).get("methods", []))
        + len(r.get("tags", {}).get("populations", []))
        + len(r.get("tags", {}).get("sponsor_themes", []))
        for r in filtered
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Records", len(records))
    c2.metric("Matching", len(filtered))
    c3.metric("Tagged", tagged)
    c4.metric("Total Tags", total_tags)


def render_downloads(filtered: list[dict]):
    if not filtered:
        return
    c1, c2 = st.columns(2)
    c1.download_button(
        "⬇ Download JSON",
        data=json.dumps(filtered, indent=2, default=str),
        file_name="foa_filtered.json",
        mime="application/json",
    )

    rows = []
    for r in filtered:
        tags = r.get("tags", {})
        rows.append(
            {
                "foa_id": r.get("foa_id"),
                "title": r.get("title"),
                "agency": r.get("agency"),
                "source": r.get("source"),
                "open_date": r.get("open_date"),
                "close_date": r.get("close_date"),
                "award_min": r.get("award_min"),
                "award_max": r.get("award_max"),
                "research_domains": "; ".join(tags.get("research_domains", [])),
                "methods": "; ".join(tags.get("methods", [])),
                "populations": "; ".join(tags.get("populations", [])),
                "sponsor_themes": "; ".join(tags.get("sponsor_themes", [])),
                "source_url": r.get("source_url"),
            }
        )
    c2.download_button(
        "⬇ Download CSV",
        data=pd.DataFrame(rows).to_csv(index=False),
        file_name="foa_filtered.csv",
        mime="text/csv",
    )


def render_tag_chart(filtered: list[dict]):
    from collections import Counter

    counter: Counter = Counter()
    for r in filtered:
        tags = r.get("tags", {})
        for cat in ["research_domains", "methods", "populations", "sponsor_themes"]:
            counter.update(tags.get(cat, []))

    if not counter:
        st.info("No tags in current results.")
        return

    df = pd.DataFrame(counter.most_common(20), columns=["Tag", "Count"])
    st.bar_chart(df.set_index("Tag"))


def main():
    if not OUTPUT_PATH.exists():
        st.error(
            f"No data found at `{OUTPUT_PATH}`. "
            "Run the pipeline first:\n\n"
            "```\npython run_pipeline.py --source grants_gov --limit 50 --out_dir ./output\n```"
        )
        st.stop()

    records = load_data(OUTPUT_PATH)
    filters = render_sidebar(records)
    filtered = apply_filters(records, filters)

    st.title("🔬 Funding Intelligence")
    st.caption("AI-Powered Funding Opportunity Discovery & Semantic Tagging")

    render_metrics(records, filtered)
    st.divider()

    tab1, tab2 = st.tabs([f"📄 Results ({len(filtered)})", "📊 Tag Distribution"])

    with tab1:
        render_downloads(filtered)
        st.markdown("---")
        if not filtered:
            st.warning("No records match the current filters.")
        else:
            for r in filtered:
                render_card(r)

    with tab2:
        render_tag_chart(filtered)


if __name__ == "__main__":
    main()
