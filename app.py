import html
import json
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd
import pdfplumber
import streamlit as st


EVENT_ID = "395892"
RESULTS_PAGE = "results"
RESULTS_LIST_ID = "933E75"
RESULTS_LIST_NAME = "Online|Pro Race"
CONFIG_URL = f"https://my.raceresult.com/{EVENT_ID}/{RESULTS_PAGE}/config"
LIST_URL = f"https://my.raceresult.com/{EVENT_ID}/{RESULTS_PAGE}/list"
SOURCE_URL = f"https://my.raceresult.com/{EVENT_ID}/results#0_{RESULTS_LIST_ID}"
STAGE_COLUMNS = [f"Stage{i}" for i in range(1, 7)]


# Function to extract text from an uploaded PDF file
def extract_text_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        text = ""
        for page in pdf.pages:
            text += "\n" + (page.extract_text() or "")
    return text


def parse_time_to_seconds(value):
    if value is None or pd.isna(value):
        return None

    match = re.search(r"([+-]?\d+(?::\d+){1,2}(?:\.\d+)?)", str(value))
    if not match:
        return None

    raw = match.group(1)
    sign = -1 if raw.startswith("-") else 1
    parts = raw.lstrip("+-").split(":")
    seconds = float(parts[-1])
    minutes = int(parts[-2])
    hours = int(parts[-3]) if len(parts) == 3 else 0
    return sign * (hours * 3600 + minutes * 60 + seconds)


def format_duration(seconds):
    if seconds is None or pd.isna(seconds):
        return "n/a"

    seconds = abs(float(seconds))
    whole_seconds = int(seconds)
    hundredths = round((seconds - whole_seconds) * 100)
    if hundredths == 100:
        whole_seconds += 1
        hundredths = 0

    hours, remainder = divmod(whole_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    suffix = f".{hundredths:02d}" if hundredths else ""
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}{suffix}"
    return f"{minutes}:{secs:02d}{suffix}"


def format_delta(delta_seconds, difference_type, baseline_seconds):
    if delta_seconds is None or baseline_seconds in (None, 0) or pd.isna(delta_seconds):
        return "n/a"

    sign = "+" if delta_seconds > 0 else "-" if delta_seconds < 0 else ""
    if difference_type == "Percentage Difference":
        return f"{sign}{abs(delta_seconds) / baseline_seconds * 100:.2f}%"
    return f"{sign}{format_duration(delta_seconds)}"


def normalize_dataframe(df):
    if df.empty:
        return df

    for col in STAGE_COLUMNS + ["Total"]:
        if col in df.columns:
            df[f"{col}Seconds"] = df[col].apply(parse_time_to_seconds)

    stage_second_cols = [f"{col}Seconds" for col in STAGE_COLUMNS if f"{col}Seconds" in df.columns]
    df["OverallSeconds"] = df.get("TotalSeconds")
    if stage_second_cols:
        df["OverallSeconds"] = df["OverallSeconds"].fillna(df[stage_second_cols].sum(axis=1, min_count=1))

    df["Bib"] = df["Bib"].astype(str)
    df["Category"] = df.get("Category", "Results").fillna("Results")
    df["DisplayName"] = df.apply(
        lambda row: f"{row['Name']} ({row['Bib']}) - {row['Category']}", axis=1
    )
    return df


def parse_name_bib(name_bib):
    match = re.match(r"^(.*?)\s+\(([^()]*)\)\s*$", str(name_bib).strip())
    if not match:
        return str(name_bib).strip(), ""
    return match.group(1).strip(), match.group(2).strip()


def clean_group_name(group_name):
    return re.sub(r"^#\d+_", "", str(group_name)).strip() or "Results"


def parse_raceresult_payload(payload):
    fields = payload.get("DataFields", [])
    field_index = {field: index for index, field in enumerate(fields)}
    rows = []

    def value(row, field):
        index = field_index.get(field)
        if index is None or index >= len(row):
            return ""
        return row[index]

    def walk(data, category="Results"):
        if isinstance(data, dict):
            for group, child in data.items():
                walk(child, clean_group_name(group))
            return

        if not isinstance(data, list):
            return

        for item in data:
            if not isinstance(item, list):
                walk(item, category)
                continue

            name, bib = parse_name_bib(value(item, "NameBib"))
            age_gender = str(value(item, "AgeSex")).split()
            row = {
                "Rank": value(item, 'If([CategoryRank]>0;[CategoryRank];"")'),
                "Name": name,
                "Bib": bib or value(item, "BIB"),
                "Age": age_gender[0] if age_gender else "",
                "Gender": age_gender[1] if len(age_gender) > 1 else "",
                "Category": category,
                "Stage1": value(item, "RATimeStage1"),
                "Stage2": value(item, "RATimeStage2"),
                "Stage3": value(item, "RATimeStage3"),
                "Stage4": value(item, "RATimeStage4"),
                "Stage5": value(item, "RATimeStage5"),
                "Stage6": value(item, "RATimeStage6"),
                "Total": value(item, "WithStatus([FinishTime])"),
                "City": value(item, "CityState"),
                "Club": value(item, "CLUB"),
            }
            if row["Name"]:
                rows.append(row)

    walk(payload.get("data", []))
    return normalize_dataframe(pd.DataFrame(rows))


def fetch_json(url, params=None):
    if params:
        url = f"{url}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "MarinduroResults/1.0"})
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


@st.cache_data(ttl=300, show_spinner=False)
def fetch_current_results():
    config = fetch_json(CONFIG_URL)
    result_list = next(
        (
            item
            for item in config["TabConfig"]["Lists"]
            if item.get("ID") == RESULTS_LIST_ID or item.get("Name") == RESULTS_LIST_NAME
        ),
        None,
    )
    if result_list is None:
        raise ValueError("Could not find the 2026 Pro Race result list.")

    payload = fetch_json(
        LIST_URL,
        {
            "key": config["key"],
            "listname": result_list["Name"],
            "page": RESULTS_PAGE,
            "contest": result_list.get("Contest", "0"),
            "r": "all",
            "l": result_list.get("Leader", 0),
            "openedGroups": "{}",
        },
    )
    return parse_raceresult_payload(payload)


# Function to parse the extracted text
def parse_race_results(text):
    time = r"((?:\d+:)?\d+:\d+(?:\.\d+)?)"
    pattern = re.compile(
        rf"(\d+)\s+(.+?)\s+\((\d+)\)\s+(\d+)\s+([A-Z])\s+Time\s+"
        rf"{time}\s+{time}\s+{time}\s+{time}\s+{time}\s+{time}\s+{time}"
    )
    rows = []
    for match in pattern.finditer(text):
        rows.append(
            {
                "Rank": match.group(1),
                "Name": re.sub(r"\s+", " ", match.group(2)).strip(),
                "Bib": match.group(3),
                "Age": match.group(4),
                "Gender": match.group(5),
                "Category": "PDF Upload",
                "Stage1": match.group(6),
                "Stage2": match.group(7),
                "Stage3": match.group(8),
                "Stage4": match.group(9),
                "Stage5": match.group(10),
                "Stage6": match.group(11),
                "Total": match.group(12),
                "City": "",
                "Club": "",
            }
        )

    return normalize_dataframe(pd.DataFrame(rows))


def colorized(value, delta_seconds):
    color = "#0b7a30" if delta_seconds <= 0 else "#b42318"
    return f"<span style='color:{color}'>{html.escape(value)}</span>"


def build_comparison_table(df, primary_index, comparison_indexes, difference_type):
    stage_columns = [col for col in STAGE_COLUMNS if f"{col}Seconds" in df.columns]
    primary = df.loc[primary_index]
    table_rows = [
        {
            "Name": html.escape(primary["DisplayName"]),
            **{col: html.escape(str(primary[col])) for col in stage_columns},
            "Overall Difference": "baseline",
        }
    ]

    for index in comparison_indexes:
        row = df.loc[index]
        table_row = {"Name": html.escape(row["DisplayName"])}
        for col in stage_columns:
            primary_seconds = primary.get(f"{col}Seconds")
            row_seconds = row.get(f"{col}Seconds")
            delta = None if pd.isna(primary_seconds) or pd.isna(row_seconds) else row_seconds - primary_seconds
            diff = format_delta(delta, difference_type, primary_seconds)
            table_row[col] = colorized(f"{row[col]} ({diff})", delta or 0)

        primary_total = primary.get("OverallSeconds")
        row_total = row.get("OverallSeconds")
        total_delta = None if pd.isna(primary_total) or pd.isna(row_total) else row_total - primary_total
        table_row["Overall Difference"] = colorized(
            format_delta(total_delta, difference_type, primary_total),
            total_delta or 0,
        )
        table_rows.append(table_row)

    return pd.DataFrame(table_rows)


st.set_page_config(page_title="Marinduro Results Comparison", layout="wide")
st.title("Marinduro Results Comparison")

source = st.radio(
    "Results source",
    ("2026 live results", "Upload PDF"),
    horizontal=True,
)

df = pd.DataFrame()
if source == "2026 live results":
    try:
        with st.spinner("Loading 2026 Pro and Expert results..."):
            df = fetch_current_results()
        st.caption(f"Loaded from {SOURCE_URL}")
    except Exception as exc:
        st.error(f"Could not load live results: {exc}")
else:
    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
    if uploaded_file is not None:
        text = extract_text_from_pdf(uploaded_file)
        df = parse_race_results(text)

if df.empty:
    st.info("Load live 2026 results or upload a race result PDF to start comparing riders.")
    st.stop()

categories = ["All categories"] + sorted(df["Category"].dropna().unique().tolist())
category = st.selectbox("Category", categories)
filtered_df = df if category == "All categories" else df[df["Category"] == category]

if filtered_df.empty:
    st.warning("No results found for that category.")
    st.stop()

labels_by_index = filtered_df["DisplayName"].to_dict()
primary_label = st.selectbox("Select Primary Rider", labels_by_index.values())
primary_index = next(index for index, label in labels_by_index.items() if label == primary_label)

comparison_options = {
    index: label for index, label in labels_by_index.items() if index != primary_index
}
comparison_labels = st.multiselect(
    "Select Riders to Compare",
    comparison_options.values(),
    max_selections=10,
)
comparison_indexes = [
    index for index, label in comparison_options.items() if label in comparison_labels
]

difference_type = st.radio(
    "Difference Type",
    ("Time Difference", "Percentage Difference"),
    horizontal=True,
)

if comparison_indexes:
    comparison_df = build_comparison_table(
        filtered_df,
        primary_index,
        comparison_indexes,
        difference_type,
    )
    st.markdown(comparison_df.to_html(escape=False, index=False), unsafe_allow_html=True)
else:
    st.info("Choose at least one rider to compare.")