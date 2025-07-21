import streamlit as st
import pandas as pd
import json
import requests
from pathlib import Path

# ------------------ Paths / Constants ------------------
BASE_DIR = Path(__file__).resolve().parent  # directory where this script lives

AA_FILE       = BASE_DIR / "AASchedSum25.csv"
DB_FILE       = BASE_DIR / "DBSchedSum25.csv"
FLINT_FILE    = BASE_DIR / "Flint_S25.csv"
MONTHLY_FILE  = BASE_DIR / "MonthlyJuly25.csv"
LEO_PREFIX    = "LEO"   # keep any Job Title that begins with this text (case‑insensitive)

# ------------------ Utilities ------------------
@st.cache_data(show_spinner=False)
def load_buildings():
    url = "https://raw.githubusercontent.com/umsi-amadaman/LEOcourseschedules/main/UMICHbuildings_dict.json"
    return json.loads(requests.get(url).text)

@st.cache_data(show_spinner=False)
def load_monthly():
    """Read the monthly file once (local path) and prep a boolean dues column."""
    monthly = pd.read_csv(MONTHLY_FILE, dtype=str)
    # numeric ID for safe merging
    monthly["UM ID"] = pd.to_numeric(monthly["UM ID"], errors="coerce")
    # simple dues flag – adjust pattern if needed
    monthly["Pays LEO Dues"] = monthly["Deduction"].str.contains("LEO", case=False, na=False)
    return monthly


def merge_monthly(df: pd.DataFrame, id_col_sched: str) -> pd.DataFrame:
    """Helper to merge a schedule df with monthly & keep only rows whose Job Title starts with LEO."""
    monthly = load_monthly()
    df[id_col_sched] = pd.to_numeric(df[id_col_sched], errors="coerce")

    merged = (
        df.dropna(subset=[id_col_sched])
          .merge(monthly, left_on=id_col_sched, right_on="UM ID", how="left")
    )
    # filter by Job Title prefix (case‑insensitive)
    is_leo = merged["Job Title"].str.startswith(LEO_PREFIX, na=False, case=False)
    return merged[is_leo]

# ------------------ Campus‑specific views ------------------

def show_ann_arbor():
    st.header("Ann Arbor Schedule by Day and Subject")
    df = pd.read_csv(AA_FILE, dtype=str)

    merged_df = merge_monthly(df, "Class Instr ID")

    # build classroom location
    merged_df["Location"] = (
        merged_df["Facility Descr"].fillna("") + " " + merged_df["Room"].fillna("")
    ).str.strip()

    # Filter by Day & Subject
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    day_map = {"Monday": "Mon", "Tuesday": "Tues", "Wednesday": "Wed", "Thursday": "Thurs", "Friday": "Fri"}
    sel_day = st.selectbox("Select Day", days, key="aa_day_select")
    day_df = merged_df[merged_df[day_map[sel_day]] == "Y"]

    subject_opts = sorted(day_df["Subject"].dropna().unique())
    sel_subj = st.selectbox("Select Subject", ["All"] + subject_opts, key="aa_subj_select")

    if sel_subj != "All":
        day_df = day_df[day_df["Subject"] == sel_subj]

    st.dataframe(day_df)
    st.write(f"Total LEO classes: {len(day_df)}")


def show_dearborn():
    st.header("Dearborn Schedule by Day and Subject")
    df = pd.read_csv(DB_FILE, skiprows=3, dtype=str)
    df.columns = [
        "Term Code", "Term Desc", "Subject", "Course", "Section", "UM ID", "Last", "First",
        "Room", "Bldg", "Instr Method", "Pattern", "Begin", "End", "Monday", "Tuesday",
        "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Instr Mode"
    ]

    merged_df = merge_monthly(df, "UM ID")
    bdict = load_buildings()
    merged_df["Location"] = (merged_df["Bldg"].map(bdict).fillna(merged_df["Bldg"]) + " " + merged_df["Room"]).str.strip()

    # Day/Subject filters
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    sel_day = st.selectbox("Select Day", days, key="db_day_select")
    df_day = merged_df[merged_df[sel_day].isin(["M", "T", "W", "R", "F", "X"])]

    subject_opts = sorted(df_day["Subject"].dropna().unique())
    sel_subj = st.selectbox("Select Subject", ["All"] + subject_opts, key="db_subj_select")

    if sel_subj != "All":
        df_day = df_day[df_day["Subject"] == sel_subj]

    st.dataframe(df_day)
    st.write(f"Total LEO classes: {len(df_day)}")


def show_flint():
    st.header("Flint Schedule by Day and Subject")
    df = pd.read_csv(FLINT_FILE, dtype=str)

    merged_df = merge_monthly(df, "Instructor ID")

    # Day/Subject filters
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    dow_map = {"Monday": "Mon", "Tuesday": "Tues", "Wednesday": "Wed", "Thursday": "Thurs", "Friday": "Fri"}
    sel_day = st.selectbox("Select Day", days, key="fl_day_select")
    df_day = merged_df[merged_df[dow_map[sel_day]] == "X"]

    subject_opts = sorted(df_day["Subject"].dropna().unique())
    sel_subj = st.selectbox("Select Subject", ["All"] + subject_opts, key="fl_subj_select")

    if sel_subj != "All":
        df_day = df_day[df_day["Subject"] == sel_subj]

    st.dataframe(df_day)
    st.write(f"Total LEO classes: {len(df_day)}")

# ------------------ Main App ------------------
st.set_page_config(page_title="UM Schedule Explorer", layout="wide")
st.title("UM Schedule Explorer")

campus = st.selectbox("Select a Campus", ["Ann Arbor", "Dearborn", "Flint"])
if campus == "Ann Arbor":
    show_ann_arbor()
elif campus == "Dearborn":
    show_dearborn()
else:
    show_flint()
