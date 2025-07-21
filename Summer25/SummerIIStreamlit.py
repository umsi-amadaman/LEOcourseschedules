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

LEO_PREFIX = "LEO"  # keep rows whose Job Title begins with this text (case‑insensitive)

# ------------------ Shared helpers ------------------
@st.cache_data
def load_buildings():
    """Return dict mapping Dearborn building codes → full names/addresses."""
    url = "https://raw.githubusercontent.com/umsi-amadaman/LEOcourseschedules/main/UMICHbuildings_dict.json"
    return requests.get(url).json()

@st.cache_data
def load_monthly() -> pd.DataFrame:
    """Return Monthly payroll / dues file as dataframe with clean ID column + dues bool."""
    monthly = pd.read_csv(MONTHLY_FILE, dtype=str)
    # numeric ID for join
    monthly["UM ID"] = pd.to_numeric(monthly["UM ID"], errors="coerce")
    # dues flag
    monthly["Pays LEO Dues"] = (~monthly["Deduction"].isna()) & monthly["Deduction"].str.contains("LEO", na=False)
    return monthly


def merge_monthly(df: pd.DataFrame, sched_id_col: str) -> pd.DataFrame:
    """Merge schedule DF with Monthly on ID and filter to LEO job titles."""
    monthly = load_monthly()

    df[sched_id_col] = pd.to_numeric(df[sched_id_col], errors="coerce")
    df = df.dropna(subset=[sched_id_col])

    merged = df.merge(monthly, left_on=sched_id_col, right_on="UM ID", how="left")

    # keep rows whose Job Title starts with LEO (case‑insensitive)
    merged = merged[merged["Job Title"].str.startswith(LEO_PREFIX, na=False, case=False)]
    return merged

# ------------------ Ann Arbor ------------------
def show_ann_arbor():
    st.header("Ann Arbor Schedule by Day and Subject")

    df = pd.read_csv(AA_FILE, dtype=str)
    merged_df = merge_monthly(df, "Class Instr ID")

    # remove rows where Monthly gave no Job Title (just in case)
    merged_df = merged_df[merged_df["Job Title"].notna() & merged_df["Job Title"].str.strip().ne("")]

    # Drop Ann Arbor‑specific noise columns (plus new ones requested)
    ann_drop = [
        "Class Instr ID", "Facility ID", "Facility Descr", "Employee Last Name",
        "Employee First Name", "UM ID", "Rec #", "Class Indc", "Job Code",
        "Hire Begin Date", "Appointment Start Date", "Appointment End Date",
        "Comp Frequency", "Appointment Period", "Appointment Period Descr",
        "Comp Rate", "Home Address 1", "Home Address 2", "Home Address 3",
        "Home City", "Home State", "Home Postal", "Home County", "Home Country",
        "Home Phone", "UM Address 1", "UM Address 2", "UM Address 3", "UM City",
        "UM State", "UM Postal", "UM County", "UM Country", "UM Phone",
        "Employee Status", "Employeee Status Descr", "uniqname", "Class Mtg Nbr",
        # --- new drops per user ---
        "Term", "Class Nbr", "Department ID", "Employee Status Descr",
    ]
    merged_df = merged_df.drop(columns=[c for c in ann_drop if c in merged_df.columns])

    # -------------- interactive filters --------------
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    day_map = {"Monday": "Mon", "Tuesday": "Tues", "Wednesday": "Wed",
               "Thursday": "Thurs", "Friday": "Fri"}

    sel_day = st.selectbox("Select Day", days, key="aa_day_select")
    day_df = merged_df[merged_df[day_map[sel_day]] == "Y"]

    subj_opts = sorted(day_df["Subject"].dropna().unique())
    sel_subj = st.selectbox("Select Subject", ["All"] + subj_opts, key="aa_subj_select")
    if sel_subj != "All":
        day_df = day_df[day_df["Subject"] == sel_subj]

    st.dataframe(day_df)
    st.write(f"Total classes: {len(day_df)}")

# ------------------ Dearborn ------------------
def show_dearborn():
    st.header("Dearborn Schedule by Day and Subject")

    # Dearborn schedule has three header rows → skiprows=3, then clean header
    raw = pd.read_csv(DB_FILE, skiprows=3, header=None, dtype=str)

    # Fix mis‑shifted header names
    raw.columns = [
        "Term Code", "Term Desc", "Subject", "Course Number", "Seq Number",
        "Instructor ID", "Instructor Last Name", "Instructor First Name",
        "Room Code", "Building Code", "Term Start Date", "Term End Date",
        "Instructional Method", "Meeting Pattern", "Begin Time", "End Time",
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
        "Sunday", "Instructional Mode"
    ]

    # merge payroll / dues
    merged = merge_monthly(raw, "Instructor ID")

    # human‑readable building name
    bdict = load_buildings()
    merged["Location"] = merged["Building Code"].map(bdict).fillna(merged["Building Code"]) + " " + merged["Room Code"].fillna("")

    # drop Dearborn‑specific noise columns (plus user‑requested)
    db_drop = [
        "Term Code", "Seq Number", "Instructor ID",  # user request
        "UM ID", "Room Code", "Building Code"
    ]
    merged = merged.drop(columns=[c for c in db_drop if c in merged.columns])

    # -------------- interactive filters --------------
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    sel_day = st.selectbox("Select Day", days, key="db_day_select")
    day_df = merged[merged[sel_day].isin(["M", "T", "W", "R", "F", "X"])]

    subj_opts = sorted(day_df["Subject"].dropna().unique())
    sel_subj = st.selectbox("Select Subject", ["All"] + subj_opts, key="db_subj_select")
    if sel_subj != "All":
        day_df = day_df[day_df["Subject"] == sel_subj]

    st.dataframe(day_df)
    st.write(f"Total classes: {len(day_df)}")

# ------------------ Flint ------------------
def show_flint():
    st.header("Flint Schedule by Day and Subject")

    df = pd.read_csv(FLINT_FILE, dtype=str)

    merged = merge_monthly(df, "UM ID") if "UM ID" in df.columns else df

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    dow_map = {"Monday": "Mon", "Tuesday": "Tues", "Wednesday": "Wed",
               "Thursday": "Thurs", "Friday": "Fri"}

    sel_day = st.selectbox("Select Day", days, key="fl_day_select")
    day_df = merged[merged[dow_map[sel_day]] == "X"]

    subj_opts = sorted(day_df["Subject"].dropna().unique())
    sel_subj = st.selectbox("Select Subject", ["All"] + subj_opts, key="fl_subj_select")
    if sel_subj != "All":
        day_df = day_df[day_df["Subject"] == sel_subj]

    st.dataframe(day_df)
    st.write(f"Total classes: {len(day_df)}")

# ------------------ Main App ------------------
st.title("UM Schedule Explorer")

campus = st.selectbox("Select a Campus", ["Ann Arbor", "Dearborn", "Flint"])

if campus == "Ann Arbor":
    show_ann_arbor()
elif campus == "Dearborn":
    show_dearborn()
else:
    show_flint()
