import os, zipfile, textwrap, shutil
import pandas as pd
base = "/mnt/data/sugar_cosmetics_dashboard" os.makedirs(base, exist_ok=True)
app_code = r'''import streamlit as st import pandas as pd import plotly.express as px import plotly.graph_objects as go from pathlib import Path
st.set_page_config( page_title="Sugar Cosmetics | Instagram Performance", page_icon="💄", layout="wide", initial_sidebar_state="expanded", )
---------- Styling ----------
st.markdown("""
.stApp { background-color: #100d1d; color: #f7f4ff; } [data-testid="stSidebar"] { background-color: #1b1530; } h1, h2, h3 { color: #f4d9ff !important; } div[data-testid="stMetric"] { background: #211936; border: 1px solid #49346b; padding: 15px; border-radius: 12px; } div[data-testid="stMetricLabel"] { color: #d7c8f2; } div[data-testid="stMetricValue"] { color: #ffffff; } .small-note { color: #d2c6e8; font-size: 0.92rem; } 
""", unsafe_allow_html=True)
DATA_FILE = Path(file).with_name("sugar_cosmetics_instagram_data.csv")
NUMERIC_COLS = [ "Impressions", "Reach", "Likes", "Comments", "Shares", "Saves", "Profile Visits", "Follows" ] CATEGORY_COLS = [ "Post Type", "Campaign Type", "Hashtags", "Audience Emotion", "Engagement Source" ] REQUIRED_COLS = ["Post Date"] + CATEGORY_COLS + NUMERIC_COLS
@st.cache_data(show_spinner="Loading Instagram data...") def load_data(path_string): path = Path(path_string) if not path.exists(): raise FileNotFoundError( f"Dataset not found: {path.name}. Put the CSV file in the same folder as app.py." ) # Read first, then normalize headers: this avoids parse_dates column-name errors. df = pd.read_csv(path) df.columns = df.columns.astype(str).str.strip()
# Match columns regardless of capitalization or extra spaces.
normalized = {c.lower().strip(): c for c in df.columns}
rename = {}
for required in REQUIRED_COLS:
    key = required.lower()
    if key not in normalized:
        raise ValueError(
            f"Required column '{required}' is missing. Columns found: {df.columns.tolist()}"
        )
    actual = normalized[key]
    if actual != required:
        rename[actual] = required
if rename:
    df = df.rename(columns=rename)

df["Post Date"] = pd.to_datetime(df["Post Date"], errors="coerce")
for col in NUMERIC_COLS:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Clean values safely.
for col in CATEGORY_COLS:
    df[col] = df[col].astype("string").str.strip()
    df[col] = df[col].replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
for col in NUMERIC_COLS:
    df[col] = df[col].fillna(0)
df = df.dropna(subset=["Post Date"]).copy()
df = df.drop_duplicates().copy()
for col in CATEGORY_COLS:
    df[col] = df[col].fillna("Unknown")

df["Engagement"] = df[["Likes", "Comments", "Shares", "Saves"]].sum(axis=1)
df["Engagement Rate (%)"] = (
    df["Engagement"].div(df["Reach"].replace(0, pd.NA)).fillna(0) * 100
)
df["Month"] = df["Post Date"].dt.to_period("M").astype(str)
df["Weekday"] = df["Post Date"].dt.day_name()
df["Weekday"] = pd.Categorical(
    df["Weekday"],
    categories=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    ordered=True,
)
df["Hashtag Count"] = df["Hashtags"].apply(
    lambda value: sum(1 for item in str(value).split(",") if item.strip())
    if str(value).strip() and str(value).lower() != "unknown" else 0
)
return df
def fmt_num(value): return f"{value:,.0f}"
def bar_chart(data, x, y, title, color=None, labels=None, horizontal=False): if data.empty: st.info("No rows match the current filters.") return if horizontal: fig = px.bar(data, x=y, y=x, orientation="h", title=title, color=color, labels=labels) else: fig = px.bar(data, x=x, y=y, title=title, color=color, labels=labels) fig.update_layout( template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.02, margin=dict(l=15, r=15, t=60, b=15), height=380 ) st.plotly_chart(fig, use_container_width=True)
---------- Load data ----------
st.title("💄 Sugar Cosmetics — Instagram Performance Dashboard") st.caption("Explore post performance, campaign results, audience response, and follower conversion.")
try: original_df = load_data(str(DATA_FILE)) except Exception as error: st.error(f"Could not load the dataset: {error}") st.info("Keep app.py and sugar_cosmetics_instagram_data.csv in the same folder, then run: python -m streamlit run app.py") st.stop()
Sidebar filters
st.sidebar.title("🎛️ Dashboard Filters") min_date = original_df["Post Date"].min().date() max_date = original_df["Post Date"].max().date() date_range = st.sidebar.date_input( "Post date range", value=(min_date, max_date), min_value=min_date, max_value=max_date ) if isinstance(date_range, (tuple, list)) and len(date_range) == 2: start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]) else: start_date, end_date = pd.to_datetime(min_date), pd.to_datetime(max_date)
def multi_filter(label, column): choices = sorted(original_df[column].dropna().astype(str).unique().tolist()) return st.sidebar.multiselect(label, choices, default=choices)
post_types = multi_filter("Post type", "Post Type") campaign_types = multi_filter("Campaign type", "Campaign Type") sources = multi_filter("Engagement source", "Engagement Source") emotions = multi_filter("Audience emotion", "Audience Emotion")
df = original_df[ original_df["Post Date"].between(start_date, end_date) & original_df["Post Type"].astype(str).isin(post_types) & original_df["Campaign Type"].astype(str).isin(campaign_types) & original_df["Engagement Source"].astype(str).isin(sources) & original_df["Audience Emotion"].astype(str).isin(emotions) ].copy()
if df.empty: st.warning("No data matches these filters. Change the selections in the sidebar.") st.stop()
---------- KPIs ----------
total_posts = len(df) total_reach = int(df["Reach"].sum()) total_engagement = int(df["Engagement"].sum()) total_follows = int(df["Follows"].sum()) overall_rate = (total_engagement / total_reach * 100) if total_reach else 0 avg_reach = df["Reach"].mean()
k1, k2, k3, k4, k5 = st.columns(5) k1.metric("Posts analysed", fmt_num(total_posts)) k2.metric("Total reach", fmt_num(total_reach)) k3.metric("Total engagement", fmt_num(total_engagement)) k4.metric("Engagement rate", f"{overall_rate:.2f}%") k5.metric("Follows gained", fmt_num(total_follows))
st.markdown( 'Engagement = Likes + Comments + Shares + Saves. ' 'Engagement rate = total engagement ÷ total reach × 100. ' 'Metrics update when sidebar filters change.', unsafe_allow_html=True, )
---------- Quick insights ----------
st.header("📌 Key Insights") post_type_perf = df.groupby("Post Type", observed=False).agg( Posts=("Post Type", "size"), Reach=("Reach", "sum"), Engagement=("Engagement", "sum"), Follows=("Follows", "sum") ).reset_index() post_type_perf["Engagement Rate (%)"] = ( post_type_perf["Engagement"] / post_type_perf["Reach"].replace(0, pd.NA) * 100 ).fillna(0) best_reach_type = post_type_perf.sort_values("Reach", ascending=False).head(1) best_rate_type = post_type_perf.sort_values("Engagement Rate (%)", ascending=False).head(1) best_campaign = df.groupby("Campaign Type", observed=False)["Engagement"].sum().sort_values(ascending=False) best_source = df.groupby("Engagement Source", observed=False)["Follows"].sum().sort_values(ascending=False)
ins1, ins2, ins3 = st.columns(3) with ins1: if not best_reach_type.empty: st.info(f"Highest total reach: {best_reach_type.iloc[0]['Post Type']} " f"({fmt_num(best_reach_type.iloc[0]['Reach'])} reach)") with ins2: if not best_rate_type.empty: st.info(f"Highest engagement rate: {best_rate_type.iloc[0]['Post Type']} " f"({best_rate_type.iloc[0]['Engagement Rate (%)']:.2f}%)") with ins3: if not best_campaign.empty: st.info(f"Most engagement by campaign: {best_campaign.index[0]} " f"({fmt_num(best_campaign.iloc[0])} interactions)")
---------- Charts: 13 views ----------
st.header("📊 Performance Analysis")
monthly = df.groupby("Month", as_index=False).agg( Reach=("Reach", "sum"), Engagement=("Engagement", "sum"), Follows=("Follows", "sum"), Posts=("Post Date", "size") ).sort_values("Month") monthly["Engagement Rate (%)"] = ( monthly["Engagement"] / monthly["Reach"].replace(0, pd.NA) * 100 ).fillna(0)
c1, c2 = st.columns(2) with c1: fig = px.line(monthly, x="Month", y="Reach", markers=True, title="
import os, zipfile, textwrap, shutil import pandas as pd
base = "/mnt/data/sugar_cosmetics_dashboard" os.makedirs(base, exist_ok=True)
app_code = r'''import streamlit as st import pandas as pd import plotly.express as px from pathlib import Path
st.set_page_config( page_title="Sugar Cosmetics | Instagram Dashboard", page_icon="💄", layout="wide", initial_sidebar_state="expanded", )
st.markdown("""
.stApp { background-color: #100d1d; color: #f7f4ff; } [data-testid="stSidebar"] { background-color: #1b1530; } h1, h2, h3 { color: #f4d9ff !important; } [data-testid="stMetric"] { background: #211936; border: 1px solid #49346b; padding: 13px; border-radius: 12px; } [data-testid="stMetricLabel"] { color: #d7c8f2; } [data-testid="stMetricValue"] { color: #ffffff; } 
""", unsafe_allow_html=True)
DATA_FILE = Path(file).with_name("sugar_cosmetics_instagram_data.csv")
NUMERIC_COLS = [ "Impressions", "Reach", "Likes", "Comments", "Shares", "Saves", "Profile Visits", "Follows" ] CATEGORY_COLS = [ "Post Type", "Campaign Type", "Hashtags", "Audience Emotion", "Engagement Source" ] REQUIRED_COLS = ["Post Date"] + CATEGORY_COLS + NUMERIC_COLS
@st.cache_data(show_spinner="Loading Instagram data...") def load_data(path_string): path = Path(path_string) if not path.exists(): raise FileNotFoundError( "Dataset not found. Keep sugar_cosmetics_instagram_data.csv in the same folder as app.py." )
# Read normally first, then clean column headers. This avoids parse_dates errors.
df = pd.read_csv(path)
df.columns = df.columns.astype(str).str.strip()

# Match required names even if capitalization differs.
actual_by_lower = {column.lower(): column for column in df.columns}
rename_columns = {}
for required in REQUIRED_COLS:
    actual = actual_by_lower.get(required.lower())
    if actual is None:
        raise ValueError(
            f"Required column '{required}' is missing. Columns found: {df.columns.tolist()}"
        )
    if actual != required:
        rename_columns[actual] = required
if rename_columns:
    df = df.rename(columns=rename_columns)

df["Post Date"] = pd.to_datetime(df["Post Date"], errors="coerce")
for column in NUMERIC_COLS:
    df[column] = pd.to_numeric(df[column], errors="coerce")

# Clean data carefully.
rows_before = len(df)
duplicate_rows = int(df.duplicated().sum())
missing_before = int(df.isna().sum().sum())
df = df.drop_duplicates().copy()
df = df.dropna(subset=["Post Date"]).copy()

for column in NUMERIC_COLS:
    df[column] = df[column].fillna(0)
for column in CATEGORY_COLS:
    df[column] = df[column].astype("string").str.strip()
    df[column] = df[column].replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    df[column] = df[column].fillna("Unknown").astype(str)

df["Engagement"] = df[["Likes", "Comments", "Shares", "Saves"]].sum(axis=1)
df["Engagement Rate (%)"] = (
    df["Engagement"] / df["Reach"].replace(0, pd.NA) * 100
).fillna(0)
df["Month"] = df["Post Date"].dt.to_period("M").astype(str)
df["Weekday"] = df["Post Date"].dt.day_name()
df["Weekday"] = pd.Categorical(
    df["Weekday"],
    categories=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    ordered=True,
)
df["Hashtag Count"] = df["Hashtags"].apply(
    lambda value: sum(1 for item in str(value).split(",") if item.strip())
    if str(value).strip() and str(value).lower() != "unknown" else 0
)
cleaning_info = {
    "rows_before": rows_before,
    "duplicates_removed": duplicate_rows,
    "missing_cells_before": missing_before,
    "rows_after": len(df),
    "rows_removed_total": rows_before - len(df),
}
return df, cleaning_info
def fmt(value): return f"{value:,.0f}"
def style_fig(fig, height=370): fig.update_layout( template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.02, margin=dict(l=15, r=15, t=60, b=15), height=height, legend_title_text="", ) return fig
st.title("💄 Sugar Cosmetics — Instagram Performance Dashboard") st.caption("A data-driven view of post reach, engagement, campaigns, audience response and follower conversion.")
try: original_df, cleaning_info = load_data(str(DATA_FILE)) except Exception as error: st.error(f"Could not load the dataset: {error}") st.info("Place sugar_cosmetics_instagram_data.csv in the same folder as app.py, then run: python -m streamlit run app.py") st.stop()
if original_df.empty: st.error("No valid rows remain after cleaning. Check the dataset.") st.stop()
Sidebar filters
st.sidebar.title("🎛️ Dashboard Filters") min_date = original_df["Post Date"].min().date() max_date = original_df["Post Date"].max().date() date_range = st.sidebar.date_input( "Post date range", value=(min_date, max_date), min_value=min_date, max_value=max_date ) if isinstance(date_range, (tuple, list)) and len(date_range) == 2: start_date, end_date = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]) else: start_date, end_date = pd.Timestamp(min_date), pd.Timestamp(max_date)
def filter_options(label, column): choices = sorted(original_df[column].astype(str).unique().tolist()) return st.sidebar.multiselect(label, choices, default=choices)
post_types = filter_options("Post type", "Post Type") campaign_types = filter_options("Campaign type", "Campaign Type") sources = filter_options("Engagement source", "Engagement Source") emotions = filter_options("Audience emotion", "Audience Emotion")
df = original_df[ original_df["Post Date"].between(start_date, end_date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)) & original_df["Post Type"].isin(post_types) & original_df["Campaign Type"].isin(campaign_types) & original_df["Engagement Source"].isin(sources) & original_df["Audience Emotion"].isin(emotions) ].copy()
if df.empty: st.warning("No rows match the selected filters. Change the selections in the sidebar.") st.stop()
KPI row
total_posts = len(df) total_reach = int(df["Reach"].sum()) total_impressions = int(df["Impressions"].sum()) total_engagement = int(df["Engagement"].sum()) total_follows = int(df["Follows"].sum()) engagement_rate = (total_engagement / total_reach * 100) if total_reach else 0 follow_conversion = (total_follows / df["Profile Visits"].sum() * 100) if df["Profile Visits"].sum() else 0
st.header("📌 Performance Summary") k1, k2, k3, k4, k5 = st.columns(5) k1.metric("Posts analysed", fmt(total_posts)) k2.metric("Total reach", fmt(total_reach)) k3.metric("Impressions", fmt(total_impressions)) k4.metric("Total engagement", fmt(total_engagement)) k5.metric("Engagement rate", f"{engagement_rate:.2f}%") k6, k7, k8 = st.columns(3) k6.metric("Follows gained", fmt(total_follows)) k7.metric("Profile visits", fmt(df["Profile Visits"].sum())) k8.metric("Avg. reach per post", fmt(df["Reach"].mean()))
st.caption("Engagement = Likes + Comments + Shares + Saves. Engagement rate = total engagement ÷ total reach × 100. All KPIs respond to the filters.")
Aggregate tables for insight generation
post_perf = df.groupby("Post Type", observed=True).agg( Posts=("Post Type", "size"), Reach=("Reach", "sum"), Engagement=("Engagement", "sum"), Follows=("Follows", "sum") ).reset_index() post_perf["Engagement Rate (%)"] = ( post_perf["Engagement"] / post_perf["Reach"].replace(0, pd.NA) * 100 ).fillna(0)
campaign_perf = df.groupby("Campaign Type", observed=True).agg( Posts=("Campaign Type", "size"), Reach=("Reach", "sum"), Engagement=("Engagement", "sum"), Follows=("Follows", "sum") ).reset_index() campaign_perf["Engagement Rate (%)"] = ( campaign_perf["Engagement"] / campaign_perf["Reach"].replace(0, pd.NA) * 100 ).fillna(0)
source_perf = df.groupby("Engagement Source", observed=True).agg( Posts=("Engagement Source", "size"), Engagement=("Engagement", "sum"), Follows=("Follows", "sum"), Profile_Visits=("Profile Visits", "sum") ).reset_index()
st.header("💡 Key Insights") ins1, ins2, ins3 = st.columns(3) if not post_perf.empty: best_reach = post_perf.sort_values("Reach", ascending=False).iloc[0] best_rate = post_perf.sort_values("Engagement Rate (%)", ascending=False).iloc[0] ins1.info(f"Highest total reach: {best_reach['Post Type']} posts ({fmt(best_reach['Reach'])} reach).") ins2.info(f"Highest engagement rate: {best_rate['Post Type']} ({best_rate['Engagement Rate (%)']:.2f}%).") if not campaign_perf.empty: best_campaign = campaign_perf.sort_values("Engagement", ascending=False).iloc[0] ins3.info(f"Most engagement: {best_campaign['Campaign Type']} campaign ({fmt(best_campaign['Engagement'])} interactions).")
Charts
st.header("📊 Explore the Data") tab1, tab2, tab3, tab4 = st.tabs(["Trends", "Content & Campaigns", "Audience & Conversion", "Data Quality"])
with tab1: monthly = df.groupby("Month", as_index=False).agg( Reach=("Reach", "sum"), Impressions=("Impressions", "sum"), Engagement=("Engagement", "sum"), Follows=("Follows", "sum"), Posts=("Post Date", "size") ).sort_values("Month") monthly["Engagement Rate (%)"] = ( monthly["Engagement"] / monthly["Reach"].replace(0, pd.NA) * 100 ).fillna(0)
a, b = st.columns(2)
with a:
    st.plotly_chart(style_fig(px.line(monthly, x="Month", y="Reach", markers=True, title="1. Monthly Reach")), use_container_width=True)
with b:
    st.plotly_chart(style_fig(px.line(monthly, x="Month", y="Engagement", markers=True, title="2. Monthly Engagement")), use_container_width=True)
c, d = st.columns(2)
with c:
    st.plotly_chart(style_fig(px.bar(monthly, x="Month", y="Posts", title="3. Number of Posts by Month")), use_container_width=True)
with d:
    st.plotly_chart(style_fig(px.line(monthly, x="Month", y="Engagement Rate (%)", markers=True, title="4. Monthly Engagement Rate (%)")), use_container_width=True)
with tab2: a, b = st.columns(2) with a: st.plotly_chart(style_fig(px.bar(post_perf.sort_values("Reach", ascending=False), x="Post Type", y="Reach", title="5. Reach by Post Type")), use_container_width=True) with b: st.plotly_chart(style_fig(px.bar(post_perf.sort_values("Engagement", ascending=False), x="Post Type", y="Engagement", title="6. Engagement by Post Type")), use_container_width=True) c, d = st.columns(2) with c: st.plotly_chart(style_fig(px.bar(campaign_perf.sort_values("Engagement", ascending=False), x="Campaign Type", y="Engagement", title="7. Engagement by Campaign Type")), use_container_width=True) with d: st.plotly_chart(style_fig(px.bar(campaign_perf.sort_values("Follows", ascending=False), x="Campaign Type", y="Follows", title="8. Follows by Campaign Type")), use_container_width=True) e, f = st.columns(2) with e: st.plotly_chart(style_fig(px.bar(post_perf, x="Post Type", y="Engagement Rate (%)", title="9. Engagement Rate by Post Type (%)")), use_container_width=True) with f
import os, zipfile, textwrap, shutil import pandas as pd
source_csv = "/mnt/data/sugar_cosmetics_instagram_data.csv" project_dir = "/mnt/data/Sugar_Cosmetics_Streamlit_Dashboard" os.makedirs(project_dir, exist_ok=True)
app_code = r'''import streamlit as st import pandas as pd import plotly.express as px from pathlib import Path
st.set_page_config(page_title="Sugar Cosmetics Instagram Dashboard", page_icon="💄", layout="wide")
st.markdown("""
.stApp {background:#100d1d;color:#f7f4ff} [data-testid="stSidebar"] {background:#1b1530} h1,h2,h3 {color:#f4d9ff !important} [data-testid="stMetric"] {background:#211936;border:1px solid #49346b;padding:12px;border-radius:12px} [data-testid="stMetricLabel"] {color:#d7c8f2} [data-testid="stMetricValue"] {color:#ffffff} 
""", unsafe_allow_html=True)
DATA_FILE = Path(file).with_name("sugar_cosmetics_instagram_data.csv") NUMERIC_COLS = ["Impressions", "Reach", "Likes", "Comments", "Shares", "Saves", "Profile Visits", "Follows"] CATEGORY_COLS = ["Post Type", "Campaign Type", "Hashtags", "Audience Emotion", "Engagement Source"] REQUIRED_COLS = ["Post Date"] + CATEGORY_COLS + NUMERIC_COLS
@st.cache_data def load_data(path): data = pd.read_csv(path)  # Do not use parse_dates before confirming headers data.columns = data.columns.astype(str).str.strip()
lookup = {column.lower().strip(): column for column in data.columns}
missing = [column for column in REQUIRED_COLS if column.lower() not in lookup]
if missing:
    raise ValueError(
        "These required columns are missing: " + ", ".join(missing) +
        ". Columns found: " + ", ".join(data.columns.astype(str))
    )
rename = {lookup[column.lower()]: column for column in REQUIRED_COLS
          if lookup[column.lower()] != column}
data = data.rename(columns=rename)

quality = {
    "Rows before cleaning": len(data),
    "Duplicate rows removed": int(data.duplicated().sum()),
    "Missing cells before cleaning": int(data.isna().sum().sum()),
}
data = data.drop_duplicates().copy()
data["Post Date"] = pd.to_datetime(data["Post Date"], errors="coerce")
data = data.dropna(subset=["Post Date"]).copy()

for col in NUMERIC_COLS:
    data[col] = pd.to_numeric(data[col], errors="coerce").fillna(0)
for col in CATEGORY_COLS:
    data[col] = data[col].astype("string").str.strip()
    data[col] = data[col].replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    data[col] = data[col].fillna("Unknown").astype(str)

data["Engagement"] = data[["Likes", "Comments", "Shares", "Saves"]].sum(axis=1)
data["Engagement Rate (%)"] = (
    data["Engagement"] / data["Reach"].replace(0, pd.NA) * 100
).fillna(0)
data["Month"] = data["Post Date"].dt.to_period("M").astype(str)
data["Weekday"] = data["Post Date"].dt.day_name()
data["Weekday"] = pd.Categorical(
    data["Weekday"],
    categories=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    ordered=True,
)
data["Hashtag Count"] = data["Hashtags"].apply(
    lambda value: sum(1 for tag in str(value).split(",") if tag.strip())
    if str(value).strip().lower() != "unknown" else 0
)
quality["Rows after cleaning"] = len(data)
quality["Rows removed total"] = quality["Rows before cleaning"] - len(data)
quality["Missing cells after cleaning"] = int(data.isna().sum().sum())
return data, quality
def chart_style(fig, height=360): fig.update_layout( template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.02, margin=dict(l=15, r=15, t=55, b=15), height=height, legend_title_text="", ) return fig
def number(value): return f"{value:,.0f}"
st.title("💄 Sugar Cosmetics — Instagram Performance Dashboard") st.caption("Explore Instagram reach, engagement, campaign performance and follower conversion.")
if not DATA_FILE.exists(): st.error("Dataset not found. Keep sugar_cosmetics_instagram_data.csv in the same folder as app.py.") st.stop()
try: raw_df, cleaning = load_data(str(DATA_FILE)) except Exception as error: st.error(f"Unable to load data: {error}") st.stop()
if raw_df.empty: st.error("No valid rows are available after cleaning.") st.stop()
Sidebar filters
st.sidebar.title("Dashboard Filters") min_date = raw_df["Post Date"].min().date() max_date = raw_df["Post Date"].max().date() date_selection = st.sidebar.date_input( "Post date range", value=(min_date, max_date), min_value=min_date, max_value=max_date ) if isinstance(date_selection, (tuple, list)) and len(date_selection) == 2: start_date, end_date = pd.Timestamp(date_selection[0]), pd.Timestamp(date_selection[1]) else: start_date, end_date = pd.Timestamp(min_date), pd.Timestamp(max_date)
def choose_values(label, column): options = sorted(raw_df[column].astype(str).unique().tolist()) return st.sidebar.multiselect(label, options, default=options)
post_types = choose_values("Post type", "Post Type") campaign_types = choose_values("Campaign type", "Campaign Type") audience_emotions = choose_values("Audience emotion", "Audience Emotion") engagement_sources = choose_values("Engagement source", "Engagement Source")
df = raw_df[ raw_df["Post Date"].between(start_date, end_date + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)) & raw_df["Post Type"].isin(post_types) & raw_df["Campaign Type"].isin(campaign_types) & raw_df["Audience Emotion"].isin(audience_emotions) & raw_df["Engagement Source"].isin(engagement_sources) ].copy()
if df.empty: st.warning("No data matches the filters. Change your selections in the sidebar.") st.stop()
Main KPI cards
posts = len(df) reach = int(df["Reach"].sum()) impressions = int(df["Impressions"].sum()) engagement = int(df["Engagement"].sum()) follows = int(df["Follows"].sum()) profile_visits = int(df["Profile Visits"].sum()) rate = engagement / reach * 100 if reach else 0 follow_conversion = follows / profile_visits * 100 if profile_visits else 0
st.header("Performance Summary") a, b, c, d, e = st.columns(5) a.metric("Posts analysed", number(posts)) b.metric("Total reach", number(reach)) c.metric("Impressions", number(impressions)) d.metric("Total engagement", number(engagement)) e.metric("Engagement rate", f"{rate:.2f}%") f, g, h = st.columns(3) f.metric("Follows gained", number(follows)) g.metric("Profile visits", number(profile_visits)) h.metric("Average reach per post", number(df["Reach"].mean())) st.caption("Engagement = Likes + Comments + Shares + Saves. Engagement rate = total engagement ÷ total reach × 100.")
Aggregations used by charts and insights
post_perf = df.groupby("Post Type", observed=True).agg( Posts=("Post Type", "size"), Reach=("Reach", "sum"), Engagement=("Engagement", "sum"), Follows=("Follows", "sum") ).reset_index() post_perf["Engagement Rate (%)"] = ( post_perf["Engagement"] / post_perf["Reach"].replace(0, pd.NA) * 100 ).fillna(0)
campaign_perf = df.groupby("Campaign Type", observed=True).agg( Posts=("Campaign Type", "size"), Reach=("Reach", "sum"), Engagement=("Engagement", "sum"), Follows=("Follows", "sum") ).reset_index() campaign_perf["Engagement Rate (%)"] = ( campaign_perf["Engagement"] / campaign_perf["Reach"].replace(0, pd.NA) * 100 ).fillna(0)
st.header("Key Insights") i1, i2, i3 = st.columns(3) if not post_perf.empty: best_reach = post_perf.loc[post_perf["Reach"].idxmax()] best_rate = post_perf.loc[post_perf["Engagement Rate (%)"].idxmax()] i1.info(f"Highest total reach: {best_reach['Post Type']} ({number(best_reach['Reach'])} reach).") i2.info(f"Highest engagement rate: {best_rate['Post Type']} ({best_rate['Engagement Rate (%)']:.2f}%).") if not campaign_perf.empty: best_campaign = campaign_perf.loc[campaign_perf["Engagement"].idxmax()] i3.info(f"Most total engagement: {best_campaign['Campaign Type']} ({number(best_campaign['Engagement'])} interactions).")
tab1, tab2, tab3, tab4, tab5 = st.tabs([ "Trends", "Content & Campaigns", "Audience", "Data Quality", "Data Table" ])
with tab1: st.subheader("Monthly performance") monthly = df.groupby("Month", as_index=False).agg( Reach=("Reach", "sum"), Impressions=("Impressions", "sum"), Engagement=("Engagement", "sum"), Follows=("Follows", "sum"), Posts=("Post Date", "size") ).sort_values("Month") monthly["Engagement Rate (%)"] = ( monthly["Engagement"] / monthly["Reach"].replace(0, pd.NA) * 100 ).fillna(0) c1, c2 = st.columns(2) c1.plotly_chart(chart_style(px.line(monthly, x="Month", y="Reach", markers=True, title="1. Monthly Reach")), use_container_width=True) c2.plotly_chart(chart_style(px.line(monthly, x="Month", y="Engagement", markers=True, title="2. Monthly Engagement")), use_container_width=True) c3, c4 = st.columns(2) c3.plotly_chart(chart_style(px.bar(monthly, x="Month", y="Posts", title="3. Posts Published per Month")), use_container_width=True) c4.plotly_chart(chart_style(px.line(monthly, x="Month", y="Engagement Rate (%)", markers=True, title="4. Monthly Engagement Rate")), use_container_width=True) c5, c6 = st.columns(2) c5.plotly_chart(chart_style(px.line(monthly, x="Month", y="Impressions", markers=True, title="5. Monthly Impressions")), use_container_width=True) c6.plotly_chart(chart_style(px.line(monthly, x="Month", y="Follows", markers=True, title="6. Monthly Follows")), use_container_width=True) if len(monthly) > 0: top_month = monthly.loc[monthly["Engagement"].idxmax()] st.success(f"Insight: {top_month['Month']} has the highest total engagement in the selected period ({number(top_month['Engagement'])}).")
with tab2: st.subheader("Which content and campaigns perform best?") c1, c2 = st.columns(2) c1.plotly_chart(chart_style(px.bar(post_perf.sort_values("Reach", ascending=False), x="Post Type", y="Reach", title="7. Reach by Post Type")), use_container_width=True) c2.plotly_chart(chart_style(px.bar(post_perf.sort_values("Engagement", ascending=False), x="Post Type", y="Engagement", title="8. Engagement by Post Type")), use_container_width=True) c3, c4 = st.columns(2) c3.plotly_chart(chart_style(px.bar(campaign_perf.sort_values("Engagement", ascending=False), x="Campaign Type", y="Engagement", title="9. Engagement by Campaign")), use_container_width=True) c4.plotly_chart(chart_style(px.bar(campaign_perf.sort_values("Follows", ascending=False), x="Campaign Type", y="Follows", title="10. Follows by Campaign")), use_container_width=True) c5, c6 = st.columns(2) c5.plotly_chart(chart_style(px.bar(post_perf.sort_values("Engagement Rate (%)", ascending=False), x="Post Type", y="Engagement Rate (%)", title="11. Engagement Rate by Post Type (%)")), use_container_width=True) c6.plotly_chart(chart_style(px.bar(campaign_perf.sort_values("Reach", ascending=False), x="Campaign Type", y="Reach", title="12. Reach by Campaign")), use_container_width=True) st.dataframe(post_perf.sort_values("Engagement", ascending=False), use_container_width=True) st.dataframe(campaign_perf.sort_values("Engagement", ascending=False), use_container_width=True)
with tab3: st.subheader("Audience response and conversion") emotion_perf = df.groupby("Audience Emotion", as_index=False).agg( Engagement=("Engagement", "sum"), Reach=("Reach", "sum"), Follows=("Follows", "sum") ) source_perf = df.groupby("Engagement Source", as_index=False).agg( Engagement=("Engagement", "sum"), Follows=("Follows", "sum"), Profile_Visits=("Profile Visits", "sum") ) weekday_perf = df.groupby("Weekday", observed=True, as_index=False).agg( Engagement=("Engagement", "sum"), Reach=("Reach", "sum"), Posts=("Post Date", "size") ) hashtag_perf = df.groupby("Hashtag Count", as_index=False).agg( Engagement=("Engagement", "mean"), Reach=("Reach", "mean"), Posts=("Hashtag Count", "size") ) c1, c2 = st.columns(2) c1.plotly_chart(chart_style(px.bar(emotion_perf.sort_values("Engagement", ascending=False), x="Audience Emotion", y="Engagement", title="13. Engagement by Audience Emotion")), use_container_width=True) c2.plotly_chart(chart_style(px.bar(source_perf.sort_values("Follows", ascending=False), x="Engagement Source", y="Follows", title="14. Follows by Engagement Source")), use_container_width=True) c3, c4 = st.columns(2) c3.plotly_chart(chart_style(px.bar(weekday_perf, x="Weekday", y="Engagement", title="15. Engagement by Weekday")), use_container_width=True) c4.plotly_chart(chart_style(px.scatter(df, x="Reach", y="Engagement", color="Post Type", title="16. Reach vs Engagement")), use_container_width=True) c5, c6 = st.columns(2) c5.plotly_chart(chart_style(px.bar(hashtag_perf, x="Hashtag Count", y="Engagement", title="17. Average Engagement by Hashtag Count")), use_container_width=True) c6.plotly_chart(chart_style(px.bar(source_perf.sort_values("Engagement", ascending=False), x="Engagement Source", y="Engagement", title="18. Engagement by Source")), use_container_width=True) st.metric("Follows per 100 profile visits", f"{follow_conversion:.2f}") st.caption("This conversion indicator is calculated as follows ÷ profile visits × 100; it is descriptive, not proof that visits caused follows.")
with tab4: st.subheader("Data cleaning summary") q1, q2, q3 = st.columns(3) q1.metric("Rows before cleaning", number(cleaning["Rows before cleaning"])) q2.metric("Duplicate rows removed", number(cleaning["Duplicate rows removed"])) q3.metric("Rows after cleaning", number(cleaning["Rows after cleaning"])) q4, q5, q6 = st.columns(3) q4.metric("Rows removed total", number(cleaning["Rows removed total"])) q5.metric("Missing cells before", number(cleaning["Missing cells before cleaning"])) q6.metric("Missing cells after", number(cleaning["Missing cells after cleaning"])) st.markdown(""" Cleaning decisions - Removed exact duplicate rows to avoid counting the same record twice. - Converted Post Date to a date; rows with invalid/missing dates are excluded from time analysis. - Converted metric columns to numeric; missing metric values are filled with zero for dashboard calculations. - Filled missing category labels with Unknown rather than guessing their values. - Engagement is derived by adding likes, comments, shares and saves.
**Limitation:** filling missing numeric values with zero can lower totals if a blank means “not recorded” rather than a true zero. Confirm this assumption before using the results for business decisions.
""")
missing_table = pd.DataFrame({
    "Column": raw_df.columns,
    "Missing values": [int(raw_df[col].isna().sum()) for col in raw_df.columns]
})
st.dataframe(missing_table, use_container_width=True, hide_index=True)
with tab5: st.subheader("Filtered dataset") st.write(f"Showing {len(df):,} records after filters.") st.dataframe(df, use_container_width=True, hide_index=True) st.download_button( "Download filtered data as CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="sugar_cosmetics_filtered_data.csv", mime="text/csv", ) st.download_button( "Download post-type summary", data=post_perf.to_csv(index=False).encode("utf-8"), file_name="sugar_cosmetics_post_type_summary.csv", mime="text/csv", )
st.divider() st.subheader("Business Recommendations") st.markdown("""
Prioritise content formats using both reach and engagement rate. A format with the most reach may not have the strongest engagement rate, so compare both before shifting the content mix.
Repeat successful campaigns carefully. Use campaign-level engagement and follow counts to identify formats worth testing again.
Use audience response to guide creative choices. Compare engagement across audience-emotion categories; treat this as an association, not proof of sentiment causing engagement.
Review the monthly trend. Investigate months with drops in reach or engagement and compare posting volume, campaign mix and content type.
Improve conversion. Track profile visits and follows together; test clear calls to action and measure whether the follow-to-visit ratio improves.
Run controlled experiments. Test hashtags, formats and posting days one variable at a time, and compare results across similar periods.
Keep data quality checks. Validate dates, duplicates and missing metrics before refreshing the dashboard. """) st.caption("Created by - challapalli Mamatha | Built with Python, Pandas, Plotly and Streamlit") '''
Validate dataset columns and save exact supplied dataset alongside app
data = pd.read_csv(source_csv) expected = ["Post Date","Post Type","Campaign Type","Hashtags","Audience Emotion","Engagement Source", "Impressions","Reach","Likes","Comments","Shares","Saves","Profile Visits","Follows"] missing = [c for c in expected if c not in data.columns] if missing: raise ValueError(f"Uploaded dataset does not contain expected columns: {missing}")
with open(os.path.join(project_dir, "app.py"), "w", encoding="utf-8") as f: f.write(app_code) shutil.copy2(source_csv, os.path.join(project_dir, "sugar_cosmetics_instagram_data.csv"))
requirements = """streamlit>=1.35 pandas>=2.0 plotly>=5.20 """ with open(os.path.join(project_dir, "requirements.txt"), "w", encoding="utf-8") as f: f.write(requirements)
