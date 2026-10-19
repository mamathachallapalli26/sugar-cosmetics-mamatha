"""
Sugar Cosmetics - Instagram Performance Dashboard (presentation style)
Run:  python -m streamlit run app.py
Needs: sugar_cosmetics_instagram_data.csv in the same folder as this file.

Structure:  1) Project title   2) Project overview
            3) Four dashboards, each with its own insights   4) Business recommendations
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Sugar Cosmetics | Instagram Analysis",
    page_icon="💄",
    layout="wide",
)

DATA_FILE = Path(__file__).resolve().parent / "sugar_cosmetics_instagram_data.csv"
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
PALETTE = ["#C4B5FD", "#C084FC", "#A78BFA", "#E879F9", "#818CF8", "#D8B4FE"]
CARD = "#2A1D52"
SETS = [
    ["#DDD6FE", "#7C3AED", "#C4B5FD", "#8B5CF6", "#EDE9FE", "#A78BFA"],
    ["#F3E8FF", "#9333EA", "#E9D5FF", "#A855F7", "#D8B4FE", "#C084FC"],
    ["#FAE8FF", "#C026D3", "#F5D0FE", "#D946EF", "#F0ABFC", "#E879F9"],
    ["#E0E7FF", "#6366F1", "#C7D2FE", "#818CF8", "#EEF2FF", "#A5B4FC"],
]


def slide_palette(i):
    """A different colour set (and order) for every chart."""
    base = SETS[i % len(SETS)]
    k = (i // len(SETS)) % len(base)
    return base[k:] + base[:k]

ACCENT = "#7A6BA8"
INK = "#2F3A4A"
METRICS = [
    "Engagement Rate %",
    "Follows per 1K Reach",
    "Avg Reach per Post",
    "Profile Visit Rate %",
    "Follow Conversion %",
]

CSS = """
<style>
.stApp {background: linear-gradient(160deg,#150C2E 0%,#221343 55%,#2E1A5C 100%);}
[data-testid="stHeader"] {background: transparent;}
[data-testid="stToolbar"] * {color:#E4DAFB !important;}
[data-testid="stSidebar"] {background: linear-gradient(180deg,#1B1038 0%,#2A1A55 100%);}
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp li, .stApp label {color:#E8E0FF;}
[data-testid="stCaptionContainer"] {color:#B8A9E0;}
.stButton button {background:#3A2A73;border:1px solid #5B45A0;border-radius:10px;}
.stApp .stButton button p {color:#F3EEFF;}
.stButton button:disabled {opacity:0.45;}
[role="radiogroup"] label:has(input:checked) > div:first-child {background-color:#A78BFA !important;border-color:#A78BFA !important;}
[data-testid="stSidebar"] .nav-title {font-size:20px;font-weight:800;color:#FFFFFF;margin-bottom:6px;}
.hero {background: linear-gradient(120deg,#4C1D95 0%,#6D28D9 55%,#9333EA 100%);border-radius:24px;padding:34px 40px;margin-bottom:18px;box-shadow:0 8px 24px rgba(0,0,0,.35);}
.hero-tag {font-size:14px;font-weight:700;letter-spacing:3px;color:#E9D5FF;}
.hero-title {font-size:40px;font-weight:800;line-height:1.15;color:#FFFFFF;margin-top:6px;}
.hero-sub {font-size:18px;color:#EDE9FE;margin-top:8px;}
.kpi {background:#2A1D52;border:1px solid #46356F;border-radius:18px;padding:16px 18px;box-shadow:0 4px 14px rgba(0,0,0,.30);border-top:5px solid #A78BFA;}
.kpi-label {font-size:12px;font-weight:700;letter-spacing:0.5px;color:#B8A9E0;text-transform:uppercase;}
.kpi-value {white-space:nowrap;font-size:26px;font-weight:800;color:#FFFFFF;line-height:1.2;}
.kpi-sub {font-size:12px;color:#B8A9E0;}
.sec-title {font-size:26px;font-weight:800;color:#FFFFFF;border-left:8px solid #A78BFA;padding-left:14px;margin:6px 0 2px 0;}
.sec-sub {font-size:15px;color:#B8A9E0;margin:0 0 12px 22px;}
.card {background:#2A1D52;border:1px solid #46356F;border-radius:18px;padding:22px 24px;box-shadow:0 4px 14px rgba(0,0,0,.30);height:100%;}
.card-title {font-size:20px;font-weight:800;color:#C4B5FD;margin-bottom:6px;}
.card-text {font-size:16px;line-height:1.5;color:#E8E0FF;}
.insight {background:#34256A;border-radius:18px;padding:26px 32px;margin-top:14px;border-left:8px solid #A78BFA;}
.insight-title {font-size:28px;font-weight:800;color:#E9D5FF;margin-bottom:6px;}
.stApp .insight li {color:#F3EEFF;font-size:21px;line-height:1.6;margin-bottom:10px;}
.stApp .insight b {color:#F5D0FE;}
.rec {background:#2A1D52;border:1px solid #46356F;border-radius:18px;padding:22px 24px;box-shadow:0 4px 14px rgba(0,0,0,.30);border-left:8px solid #A78BFA;margin-bottom:14px;}
.rec-num {font-size:14px;font-weight:800;color:#C4B5FD;letter-spacing:2px;}
.rec-title {font-size:21px;font-weight:800;color:#FFFFFF;}
.rec-text {font-size:16px;line-height:1.5;color:#D9CFF5;}
[data-testid="stPlotlyChart"] {background:#2A1D52;border:1px solid #46356F;border-radius:18px;padding:10px;box-shadow:0 4px 14px rgba(0,0,0,.30);}
</style>
"""


# --------------------------------------------------------------------------
# Data helpers
# --------------------------------------------------------------------------
def safe_div(a, b):
    """Division that returns NaN instead of inf/errors when b is 0."""
    if isinstance(b, pd.Series):
        return a / b.replace(0, np.nan)
    return a / b if b else np.nan


@st.cache_data(show_spinner="Loading data...")
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = [str(c).replace("\ufeff", "").replace("_", " ").strip().title() for c in df.columns]
    required = ["Post Date", "Post Type", "Campaign Type", "Hashtags", "Audience Emotion",
                "Engagement Source", "Impressions", "Reach", "Likes", "Comments",
                "Shares", "Saves", "Profile Visits", "Follows"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error(f"Your CSV is missing these columns: {missing}\n\nColumns found: {list(df.columns)}")
        st.stop()
    df["Post Date"] = pd.to_datetime(df["Post Date"], errors="coerce")
    df = df.dropna(subset=["Post Date"])
    df["Engagements"] = df[["Likes", "Comments", "Shares", "Saves"]].sum(axis=1)
    df["Month"] = df["Post Date"].dt.to_period("M").dt.to_timestamp()
    df["Weekday"] = pd.Categorical(
        df["Post Date"].dt.day_name(), categories=WEEKDAYS, ordered=True
    )
    tag_count = df["Hashtags"].fillna("").apply(
        lambda s: len([t for t in s.split(",") if t.strip()])
    )
    df["Hashtags Used"] = tag_count.astype(str) + " tag(s)"
    return df


def summarize(df: pd.DataFrame, by) -> pd.DataFrame:
    """Aggregate metrics for one or more grouping columns (ratio-of-sums)."""
    g = df.groupby(by, observed=True).agg(
        Posts=("Reach", "size"),
        Impressions=("Impressions", "sum"),
        Reach=("Reach", "sum"),
        Likes=("Likes", "sum"),
        Comments=("Comments", "sum"),
        Shares=("Shares", "sum"),
        Saves=("Saves", "sum"),
        Engagements=("Engagements", "sum"),
        ProfileVisits=("Profile Visits", "sum"),
        Follows=("Follows", "sum"),
    )
    g = g.reset_index()
    g["Engagement Rate %"] = safe_div(g["Engagements"], g["Reach"]) * 100
    g["Follows per 1K Reach"] = safe_div(g["Follows"], g["Reach"]) * 1000
    g["Profile Visit Rate %"] = safe_div(g["ProfileVisits"], g["Reach"]) * 100
    g["Follow Conversion %"] = safe_div(g["Follows"], g["ProfileVisits"]) * 100
    g["Avg Reach per Post"] = safe_div(g["Reach"], g["Posts"])
    return g


def fmt_num(n) -> str:
    n = float(n)
    for unit, size in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(n) >= size:
            return f"{n / size:,.2f}{unit}"
    return f"{n:,.0f}"


# --------------------------------------------------------------------------
# Chart helpers
# --------------------------------------------------------------------------
def style_fig(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=CARD,
        plot_bgcolor=CARD,
        font=dict(color="#EDE7FF"),
        margin=dict(t=60, b=20, l=10, r=10),
    )
    fig.update_xaxes(gridcolor="#3E2F6E", zerolinecolor="#3E2F6E")
    fig.update_yaxes(gridcolor="#3E2F6E", zerolinecolor="#3E2F6E")
    return fig


def bar_chart(g, x, y, title, pal, keep_order=False):
    if not keep_order:
        g = g.sort_values(y, ascending=False)
    g = g.copy()
    g[x] = g[x].astype(str)
    fig = px.bar(
        g, x=x, y=y, text=y, color=x,
        color_discrete_sequence=list(pal) * 2, title=title,
        category_orders={x: list(g[x])},
    )
    fig.update_traces(texttemplate="%{text:,.2f}", textposition="outside", cliponaxis=False)
    fig.update_layout(showlegend=False)
    fig.update_yaxes(rangemode="tozero")
    return style_fig(fig)


def heatmap(pivot, title, pal):
    fig = px.imshow(pivot, text_auto=".2f", aspect="auto",
                    color_continuous_scale=["#2F2160", pal[3], pal[0]], title=title)
    return style_fig(fig)


# --------------------------------------------------------------------------
# HTML building blocks
# --------------------------------------------------------------------------
def kpi(label, value, sub="", accent="#B9A9E0"):
    return (f'<div class="kpi" style="border-top-color:{accent}"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div><div class="kpi-sub">{sub}</div></div>')


def section_header(title, subtitle=""):
    st.markdown(f'<div class="sec-title">{title}</div><div class="sec-sub">{subtitle}</div>',
                unsafe_allow_html=True)


def card(title, text):
    return (f'<div class="card"><div class="card-title">{title}</div>'
            f'<div class="card-text">{text}</div></div>')


def insights_box(title, bullets):
    items = "".join(f"<li>{b}</li>" for b in bullets)
    st.markdown(f'<div class="insight"><div class="insight-title">💡 {title}</div><ul>{items}</ul></div>',
                unsafe_allow_html=True)


def rec_card(num, title, text):
    accent = PALETTE[(num - 1) % len(PALETTE)] if isinstance(num, int) else PALETTE[5]
    return (f'<div class="rec" style="border-left-color:{accent}"><div class="rec-num">RECOMMENDATION {num}</div>'
            f'<div class="rec-title">{title}</div><div class="rec-text">{text}</div></div>')


# --------------------------------------------------------------------------
# Insight builders (all numbers come from the filtered data)
# --------------------------------------------------------------------------
def best_worst(df, dim, metric="Engagement Rate %"):
    g = summarize(df, dim).dropna(subset=[metric])
    if len(g) < 2:
        return None
    hi = g.loc[g[metric].idxmax()]
    lo = g.loc[g[metric].idxmin()]
    gap = (hi[metric] - lo[metric]) / lo[metric] * 100 if lo[metric] else np.nan
    return str(hi[dim]), float(hi[metric]), str(lo[dim]), float(lo[metric]), float(gap)


def bw_text(label, r, unit="%"):
    if r is None:
        return f"<b>{label}:</b> select more than one segment to compare."
    return (f"<b>{label}:</b> {r[0]} leads at {r[1]:.2f}{unit}, {r[2]} trails at "
            f"{r[3]:.2f}{unit} (gap {r[4]:.1f}%).")


def verdict(*gaps):
    gaps = [g for g in gaps if g is not None and not np.isnan(g)]
    if not gaps:
        return "Not enough data to compare segments."
    if max(gaps) < 5:
        return ("All gaps are small (under 5%), so no segment is a clear winner. "
                "Treat these as ideas to A/B test, not firm conclusions.")
    return "At least one gap is above 5%, which is worth acting on."


def tags_frame(df):
    tags = df.assign(Hashtag=df["Hashtags"].fillna("").str.split(",")).explode("Hashtag")
    tags["Hashtag"] = tags["Hashtag"].str.strip()
    return tags[tags["Hashtag"] != ""]


def quartiles(df):
    if len(df) < 40:
        return None
    q = df.copy()
    q["Reach Quartile"] = pd.qcut(
        q["Reach"].rank(method="first"), 4,
        labels=["Q1 (lowest reach)", "Q2", "Q3", "Q4 (highest reach)"],
    )
    qs = summarize(q, "Reach Quartile")
    qs["Avg Follows per Post"] = safe_div(qs["Follows"], qs["Posts"])
    return qs


def ranking_text(df, dim):
    g = summarize(df, dim).dropna(subset=["Engagement Rate %"])
    g = g.sort_values("Engagement Rate %", ascending=False)
    return "<b>Ranking:</b> " + ", ".join(
        f"{r[dim]} {r['Engagement Rate %']:.2f}%" for _, r in g.iterrows()
    )


# ----- charts: one function per dashboard, signature (df, tot, pal) -----
def month_labels(m):
    m = m.copy()
    m["Label"] = m["Month"].dt.strftime("%b %Y")
    return m


def fig_monthly_reach(df, tot, pal):
    m = month_labels(summarize(df, "Month"))
    fig = px.bar(m, x="Label", y="Reach", color="Label", title="Monthly reach",
                 color_discrete_sequence=list(pal) * 4,
                 category_orders={"Label": list(m["Label"])})
    fig.update_layout(showlegend=False, xaxis_title="Month")
    return style_fig(fig)


def fig_monthly_er(df, tot, pal):
    m = month_labels(summarize(df, "Month"))
    fig = px.line(m, x="Label", y="Engagement Rate %", markers=True,
                  title="Monthly engagement rate (%)",
                  category_orders={"Label": list(m["Label"])})
    fig.update_traces(line_color=pal[0], line_width=3,
                      marker=dict(size=12, color=(list(pal) * 4)[:len(m)]))
    fig.update_yaxes(rangemode="tozero")
    fig.update_layout(xaxis_title="Month")
    return style_fig(fig)


def fig_mix(df, tot, pal):
    mix = pd.DataFrame({
        "Type": ["Likes", "Comments", "Shares", "Saves"],
        "Count": [tot["Likes"], tot["Comments"], tot["Shares"], tot["Saves"]],
    })
    fig = px.pie(mix, names="Type", values="Count", hole=0.5,
                 title="Engagement mix", color_discrete_sequence=list(pal))
    return style_fig(fig)


def make_dim_fig(dim, title, keep_order=False):
    def fn(df, tot, pal):
        return bar_chart(summarize(df, dim), dim, "Engagement Rate %", title, pal, keep_order)
    return fn


def fig_hashtag(df, tot, pal):
    tags = tags_frame(df)
    if tags.empty:
        return None
    return bar_chart(summarize(tags, "Hashtag"), "Hashtag", "Engagement Rate %",
                     "Engagement rate % by hashtag", pal)


def fig_heat(df, tot, pal):
    pivot = summarize(df, ["Post Type", "Campaign Type"]).pivot(
        index="Post Type", columns="Campaign Type", values="Engagement Rate %")
    return heatmap(pivot, "Engagement rate %: post type x campaign", pal)


def fig_funnel(df, tot, pal):
    funnel = pd.DataFrame({
        "Stage": ["Impressions", "Reach", "Engagements", "Profile Visits", "Follows"],
        "Count": [tot["Impressions"], tot["Reach"], tot["Engagements"],
                  tot["ProfileVisits"], tot["Follows"]],
    })
    fig = px.funnel(funnel, x="Count", y="Stage", color="Stage", title="Conversion funnel",
                    color_discrete_sequence=list(pal))
    fig.update_layout(showlegend=False)
    return style_fig(fig)


def fig_scatter(df, tot, pal):
    sample = df.sample(min(3000, len(df)), random_state=42)
    fig = px.scatter(sample, x="Reach", y="Follows", color="Post Type", opacity=0.75,
                     title="Reach vs follows (sample of up to 3,000 posts)",
                     color_discrete_sequence=list(pal))
    return style_fig(fig)


def fig_quartile(df, tot, pal):
    qs = quartiles(df)
    if qs is None:
        return None
    return bar_chart(qs, "Reach Quartile", "Avg Follows per Post",
                     "Average follows per post by reach quartile", pal, keep_order=True)


# ----- insights: one function per dashboard, signature (df, tot) -----
def ins_monthly_reach(df, tot):
    m = summarize(df, "Month")
    full = m.iloc[1:-1] if len(m) > 2 else m
    hi = m.loc[m["Reach"].idxmax()]
    lo = m.loc[m["Reach"].idxmin()]
    swing = (full["Reach"].max() - full["Reach"].min()) / full["Reach"].mean() * 100
    out = [
        f"<b>Average full month:</b> {fmt_num(full['Reach'].mean())} reach.",
        f"<b>Peak:</b> {hi['Month']:%b %Y} ({fmt_num(hi['Reach'])}). <b>Lowest:</b> {lo['Month']:%b %Y} "
        f"({fmt_num(lo['Reach'])}); the first and last months can be partial.",
        f"<b>Month-to-month swing</b> between full months is {swing:.0f}% of the average.",
    ]
    if len(m) > 3:
        out.append(f"<b>Link to volume:</b> monthly reach moves with the number of posts "
                   f"(correlation {m['Reach'].corr(m['Posts']):.2f}).")
    return out


def ins_monthly_er(df, tot):
    m = summarize(df, "Month")
    return [
        f"<b>Overall engagement rate:</b> {tot['Engagement Rate %']:.2f}% of reach.",
        f"<b>Monthly range:</b> {m['Engagement Rate %'].min():.2f}% to {m['Engagement Rate %'].max():.2f}%, "
        f"a spread of only {m['Engagement Rate %'].max() - m['Engagement Rate %'].min():.2f} points.",
        "A flat line means audience response is stable over time, with no strong seasonal effect.",
    ]


def ins_weekday(df, tot):
    wk = df["Weekday"].isin(["Saturday", "Sunday"])
    out = [bw_text("Best weekday", best_worst(df, "Weekday")), ranking_text(df, "Weekday")]
    if wk.any() and (~wk).any():
        a = summarize(df[wk].assign(_g="x"), "_g").iloc[0]["Engagement Rate %"]
        b = summarize(df[~wk].assign(_g="x"), "_g").iloc[0]["Engagement Rate %"]
        out.append(f"<b>Weekend vs weekday:</b> {a:.2f}% vs {b:.2f}%.")
    return out


def ins_mix(df, tot):
    e = tot["Engagements"]
    sh = {k: safe_div(tot[k], e) * 100 for k in ("Likes", "Comments", "Saves", "Shares")}
    return [
        f"<b>Likes:</b> {sh['Likes']:.0f}% of all engagement.",
        f"<b>Comments:</b> {sh['Comments']:.0f}%, <b>Saves:</b> {sh['Saves']:.1f}%, <b>Shares:</b> {sh['Shares']:.1f}%.",
        f"<b>High-intent actions</b> (saves + shares) are only {sh['Saves'] + sh['Shares']:.1f}% of engagement, "
        "the biggest room to improve.",
    ]


def make_dim_ins(dim, label):
    def fn(df, tot):
        r = best_worst(df, dim)
        out = [bw_text(label, r)]
        if r is not None:
            out.append(ranking_text(df, dim))
        out.append(verdict(r[4] if r else None))
        return out
    return fn


def ins_source(df, tot):
    out = make_dim_ins("Engagement Source", "Engagement source")(df, tot)
    paid = df[df["Engagement Source"] == "Paid"]
    organic = df[df["Engagement Source"] == "Organic"]
    if len(paid) and len(organic):
        p, o = paid["Reach"].mean(), organic["Reach"].mean()
        out.insert(2, f"<b>Paid vs organic reach:</b> {p:,.0f} per paid post vs {o:,.0f} per organic post "
                      f"({(p / o - 1) * 100:+.1f}%), so paid is not buying extra reach.")
    return out


def ins_hashtag(df, tot):
    tags = tags_frame(df)
    if tags.empty:
        return ["No hashtags in the selected posts."]
    r = best_worst(tags, "Hashtag")
    return [bw_text("Hashtag", r), ranking_text(tags, "Hashtag"), verdict(r[4] if r else None)]


def ins_heat(df, tot):
    combo = summarize(df, ["Post Type", "Campaign Type"]).dropna(subset=["Engagement Rate %"])
    if len(combo) < 2:
        return ["Select more than one post type or campaign to compare combinations."]
    hi = combo.loc[combo["Engagement Rate %"].idxmax()]
    lo = combo.loc[combo["Engagement Rate %"].idxmin()]
    gap = (hi["Engagement Rate %"] - lo["Engagement Rate %"]) / lo["Engagement Rate %"] * 100
    return [
        f"<b>Best combination:</b> {hi['Post Type']} + {hi['Campaign Type']} at {hi['Engagement Rate %']:.2f}% "
        f"({int(hi['Posts']):,} posts).",
        f"<b>Weakest:</b> {lo['Post Type']} + {lo['Campaign Type']} at {lo['Engagement Rate %']:.2f}% "
        f"({int(lo['Posts']):,} posts).",
        f"<b>Gap:</b> {gap:.1f}%. " + verdict(gap),
    ]


def ins_funnel(df, tot):
    return [
        f"<b>Impressions to reach:</b> {fmt_num(tot['Impressions'])} impressions reached {fmt_num(tot['Reach'])} "
        f"accounts ({safe_div(tot['Reach'], tot['Impressions']) * 100:.0f}%).",
        f"<b>Engagement:</b> {fmt_num(tot['Engagements'])} actions, {tot['Engagement Rate %']:.1f}% of reach.",
        f"<b>Profile visits:</b> {tot['Profile Visit Rate %']:.1f}% of reached accounts.",
        f"<b>Follows:</b> {tot['Follow Conversion %']:.0f}% of visitors follow, which is "
        f"{tot['Follows per 1K Reach']:.1f} new followers per 1,000 reached.",
    ]


def ins_scatter(df, tot):
    corr_rf = df["Reach"].corr(df["Follows"]) if len(df) > 2 else np.nan
    corr_re = df["Reach"].corr(df["Engagements"] / df["Reach"]) if len(df) > 2 else np.nan
    return [
        f"<b>Reach vs follows:</b> correlation {corr_rf:.2f}, so posts that reach more people gain more followers.",
        f"<b>Reach vs engagement rate:</b> correlation {corr_re:.2f}, so bigger posts do not engage better.",
        "Growth therefore comes from reaching more people, not from changing the content type.",
    ]


def ins_quartile(df, tot):
    qs = quartiles(df)
    if qs is None:
        return ["Not enough posts for a quartile comparison."]
    f1 = qs["Avg Follows per Post"].iloc[0]
    f4 = qs["Avg Follows per Post"].iloc[-1]
    rate = ", ".join(f"{v:.1f}" for v in qs["Follows per 1K Reach"])
    return [
        f"<b>Lowest-reach posts</b> earn about {f1:,.0f} follows each; <b>top-reach posts</b> earn about {f4:,.0f} "
        f"({f4 / f1:.1f}x more).",
        f"<b>Follows per 1K reach</b> from lowest to highest quartile: {rate}.",
        "The follow rate is almost the same in every quartile, so more reach translates directly into more followers.",
    ]


DASHBOARDS = [
    ("Monthly reach", "How much reach the account gets each month", fig_monthly_reach, ins_monthly_reach),
    ("Monthly engagement rate", "How audience response changes over time", fig_monthly_er, ins_monthly_er),
    ("Engagement by weekday", "Which day of the week performs best", make_dim_fig("Weekday", "Engagement rate % by weekday", True), ins_weekday),
    ("Engagement mix", "What kinds of engagement the audience gives", fig_mix, ins_mix),
    ("Post type", "Reel, Story, Video or Image", make_dim_fig("Post Type", "Engagement rate % by post type"), make_dim_ins("Post Type", "Post type")),
    ("Campaign type", "Which campaign themes work best", make_dim_fig("Campaign Type", "Engagement rate % by campaign type"), make_dim_ins("Campaign Type", "Campaign")),
    ("Post type x campaign", "Best and weakest content combinations", fig_heat, ins_heat),
    ("Number of hashtags", "One, two or three hashtags", make_dim_fig("Hashtags Used", "Engagement rate % by number of hashtags"), make_dim_ins("Hashtags Used", "Hashtag count")),
    ("Audience emotion", "How the audience feels when engaging", make_dim_fig("Audience Emotion", "Engagement rate % by audience emotion"), make_dim_ins("Audience Emotion", "Audience emotion")),
    ("Engagement source", "Organic, paid, influencer or collab", make_dim_fig("Engagement Source", "Engagement rate % by engagement source"), ins_source),
    ("Individual hashtags", "Which hashtags go with higher engagement", fig_hashtag, ins_hashtag),
    ("Conversion funnel", "From impressions to followers", fig_funnel, ins_funnel),
    ("Reach vs follows", "Does more reach bring more followers?", fig_scatter, ins_scatter),
    ("Reach quartiles", "Follower gain for low to high reach posts", fig_quartile, ins_quartile),
]


# --------------------------------------------------------------------------
# App
# --------------------------------------------------------------------------
def main():
    st.markdown(CSS, unsafe_allow_html=True)

    if not DATA_FILE.exists():
        st.error(
            f"Data file not found: {DATA_FILE}\n\n"
            "Place 'sugar_cosmetics_instagram_data.csv' in the same folder as app.py."
        )
        st.stop()

    df = load_data(str(DATA_FILE))
    tot = summarize(df.assign(_all="All"), "_all").iloc[0]

    # ---------------- Slide navigation (left sidebar) ----------------
    titles = (
        ["🏠 Title and project overview"]
        + [f"📊 Dashboard {i}: {d[0]}" for i, d in enumerate(DASHBOARDS, start=1)]
        + ["✅ Business recommendations", "🗂 Data explorer"]
    )
    total = len(titles)
    if "slide" not in st.session_state:
        st.session_state["slide"] = 0
    if "jump_to" not in st.session_state:
        st.session_state["jump_to"] = titles[0]

    def go(step):
        st.session_state["slide"] = max(0, min(total - 1, st.session_state["slide"] + step))
        st.session_state["jump_to"] = titles[st.session_state["slide"]]

    def jump():
        st.session_state["slide"] = titles.index(st.session_state["jump_to"])

    slide = st.session_state["slide"]
    st.sidebar.markdown('<div class="nav-title">📑 Slides</div>', unsafe_allow_html=True)
    b1, b2 = st.sidebar.columns(2)
    b1.button("◀ Prev", on_click=go, args=(-1,), disabled=(slide == 0), key="prev_btn")
    b2.button("Next ▶", on_click=go, args=(1,), disabled=(slide == total - 1), key="next_btn")
    st.sidebar.radio("Go to slide", titles, key="jump_to", on_change=jump, label_visibility="collapsed")
    st.caption(f"Slide {slide + 1} of {total}")

    # ---------------- Slide 1: title + overview ----------------
    if slide == 0:
        st.markdown(
            '<div class="hero"><div class="hero-tag">SOCIAL MEDIA ANALYTICS PROJECT</div>'
            '<div class="hero-title">📊 Sugar Cosmetics: Instagram Performance Analysis</div>'
            '<div class="hero-sub">Interactive dashboard on reach, engagement and follower growth</div></div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(3) + st.columns(3)
        cards = [
            ("Posts", f"{int(tot['Posts']):,}", "analysed"),
            ("Impressions", fmt_num(tot["Impressions"]), "total views"),
            ("Reach", fmt_num(tot["Reach"]), "unique accounts"),
            ("Engagement rate", f"{tot['Engagement Rate %']:.2f}%", "of reach"),
            ("New follows", fmt_num(tot["Follows"]), "gained"),
            ("Follows / 1K reach", f"{tot['Follows per 1K Reach']:.2f}", "efficiency"),
        ]
        for col, (label, value, sub), accent in zip(cols, cards, PALETTE):
            col.markdown(kpi(label, value, sub, accent), unsafe_allow_html=True)
        st.write("")
        section_header("Project overview", "What this project is about and how it was built")
        c1, c2, c3 = st.columns(3)
        c1.markdown(card("🎯 Objective",
                         "Understand what drives reach, engagement and follower growth on Sugar Cosmetics’ "
                         "Instagram, and turn the findings into clear business actions."), unsafe_allow_html=True)
        c2.markdown(card("📦 Dataset",
                         f"{len(df):,} Instagram posts from {df['Post Date'].min():%d %b %Y} to "
                         f"{df['Post Date'].max():%d %b %Y}, with post type, campaign, hashtags, audience emotion, "
                         "engagement source, reach, likes, comments, shares, saves, profile visits and follows."),
                    unsafe_allow_html=True)
        c3.markdown(card("🛠 How to use it",
                         f"{len(DASHBOARDS)} dashboards, one per slide, each with its own insights. "
                         "Use the slide menu or the Prev and Next buttons on the left."),
                    unsafe_allow_html=True)
        st.write("")
        m1, m2, m3 = st.columns(3)
        m1.markdown(card("Engagement rate",
                         "(Likes + Comments + Shares + Saves) ÷ Reach. Shows how well content resonates."),
                    unsafe_allow_html=True)
        m2.markdown(card("Follows per 1K reach",
                         "New followers gained for every 1,000 accounts reached. Shows growth efficiency."),
                    unsafe_allow_html=True)
        m3.markdown(card("Follow conversion",
                         "Follows ÷ profile visits. Shows how many visitors become followers."),
                    unsafe_allow_html=True)

    # ---------------- Slides 2..: one dashboard per slide ----------------
    elif 1 <= slide <= len(DASHBOARDS):
        name, sub, fig_fn, ins_fn = DASHBOARDS[slide - 1]
        section_header(f"Dashboard {slide} of {len(DASHBOARDS)}: {name}", sub)
        left, right = st.columns([3, 2])
        fig = fig_fn(df, tot, slide_palette(slide))
        if fig is None:
            left.info("Not enough data for this chart.")
        else:
            left.plotly_chart(fig)
        with right:
            insights_box(f"Insights: {name}", ins_fn(df, tot))

    # ---------------- Business recommendations ----------------
    elif slide == total - 2:
        section_header("Business recommendations", "Five actions based on the dashboards")
        like_share = safe_div(tot["Likes"], tot["Engagements"]) * 100
        left, right = st.columns(2)
        left.markdown(
            rec_card(1, "Scale reach, not small tweaks",
                     "Follows rise with reach while engagement rate stays flat. Invest in distribution: influencer "
                     "collaborations, creator partnerships, consistent posting and boosting the best-reaching posts.")
            + rec_card(2, "Increase saves and shares",
                       f"Likes are about {like_share:.0f}% of engagement. Add save and share prompts "
                       "(tutorial checklists, giveaway share mechanics) to build higher-intent engagement.")
            + rec_card(3, "Convert more profile visitors",
                       f"Only {tot['Follow Conversion %']:.0f}% of profile visitors follow. Improve the bio, "
                       "highlights and pinned posts to lift follows without needing more reach."),
            unsafe_allow_html=True,
        )
        right.markdown(
            rec_card(4, "Test before you commit",
                     "Gaps between post types, campaigns, hashtag counts and weekdays are only around 1%. "
                     "Run controlled A/B tests before shifting budget or content mix.")
            + rec_card(5, "Audit paid spend",
                       "Paid posts do not deliver more reach or a higher engagement rate than organic posts. "
                       "Review targeting and creative before increasing paid budgets.")
            + rec_card("★", "Where Sugar Cosmetics can win",
                       "Combine influencer-led content with strong save and share hooks, and measure success on "
                       "follows per 1,000 reach, not just likes."),
            unsafe_allow_html=True,
        )
        st.caption("Note: segment differences in this dataset are small, so treat them as hypotheses to test.")

    # ---------------- Data ----------------
    else:
        section_header("Data explorer", f"Showing the first 1,000 of {len(df):,} rows")
        cols_out = [
            "Post Date", "Post Type", "Campaign Type", "Hashtags", "Audience Emotion",
            "Engagement Source", "Impressions", "Reach", "Likes", "Comments", "Shares",
            "Saves", "Profile Visits", "Follows", "Engagements",
        ]
        st.dataframe(df[cols_out].head(1000))
        st.download_button(
            "⬇️ Download data (CSV)",
            data=df[cols_out].to_csv(index=False).encode("utf-8"),
            file_name="sugar_cosmetics_data.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
