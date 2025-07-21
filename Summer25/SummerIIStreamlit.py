import streamlit as st
import pandas as pd
import json
import requests
from pathlib import Path

# ------------------ Paths / Constants ------------------
BASE_DIR = Path(__file__).resolve().parent  # folder that holds this script

AA_FILE      = BASE_DIR / "AASchedSum25.csv"
DB_FILE      = BASE_DIR / "DBSchedSum25.csv"
FLINT_FILE   = BASE_DIR / "Flint_S25.csv"
MONTHLY_FILE = BASE_DIR / "MonthlyJuly25.csv"

LEO_PREFIX = "leo"  # case‑insensitive match on Job Title

# ------------------ Helpers ------------------
@st.cache_data
def load_buildings() -> dict:
    """Return dict mapping Dearborn building codes → full names/addresses."""
    url = (
        "https://raw.githubusercontent.com/umsi-amadaman/LEOcourseschedules/main/UMICHbuildings_dict.json"
    )
    return requests.get(url).json()

@st.cache_data
def load_monthly() -> pd.DataFrame:
    """Load Monthly payroll file, add dues flag, return dataframe."""
    m = pd.read_csv(MONTHLY_FILE, dtype=str)
    m["UM ID"] = pd.to_numeric(m["UM ID"], errors="coerce")
    m["Pays LEO Dues"] = (
        ~m["Deduction"].isna() & m["Deduction"].str.contains("LEO", na=False)
    )
    return m

def merge_monthly(df: pd.DataFrame, id_col: str) -> pd.DataFrame:
    """Join schedule DF with Monthly on numeric ID & keep LEO job titles."""
    monthly = load_monthly()

    df[id_col] = pd.to_numeric(df[id_col], errors="coerce")
    df = df.dropna(subset=[id_col])

    merged = df.merge(monthly, left_on=id_col, right_on="UM ID", how="left")

    # keep rows where Job Title begins with LEO (case‑insensitive)
    title_series = merged["Job Title"].fillna("").str.lower()
    merged = merged[title_series.str.startswith(LEO_PREFIX)]
    return merged

# ------------------ Ann Arbor ------------------

def show_ann_arbor():
    st.header("Ann Arbor Schedule by Day and Subject")

    df = pd.read_csv(AA_FILE, dtype=str)
    merged = merge_monthly(df, "Class Instr ID")

    # remove rows with blank Job Title (extra safety)
    merged = merged[merged["Job Title"].fillna("").str.strip().ne("")]

    # columns to drop (user‑requested + legacy noise)
    ann_drop = [
        "Class Instr ID",
        "Facility ID",
        "Facility Descr",
        "Employee Last Name",
        "Employee First Name",
        "UM ID",
        "Rec #",
        "Class Indc",
        "Job Code",
        "Hire Begin Date",
        "Appointment Start Date",
        "Appointment End Date",
        "Comp Frequency",
        "Appointment Period",
        "Appointment Period Descr",
        "Comp Rate",
        "Home Address 1",
        "Home Address 2",
        "Home Address 3",
        "Home City",
        "Home State",
        "Home Postal",
        "Home County",
        "Home Country",
        "Home Phone",
        "UM Address 1",
        "UM Address 2",
        "UM Address 3",
        "UM City",
        "UM State",
        "UM Postal",
        "UM County",
        "UM Country",
        "UM Phone",
        "Employee Status",
        "Employeee Status Descr",
        "uniqname",
        "Class Mtg Nbr",
        # user‑requested extra drops
        "Term",
        "Class Nbr",
        "Department ID",
        "Employee Status Descr",
    ]
    merged = merged.drop(columns=[c for c in ann_drop if c in merged.columns])

    # ---------------- filters ----------------
    day_map = {
        "Monday": "Mon",
        "Tuesday": "Tues",
        "Wednesday": "Wed",
        "Thursday": "Thurs",
        "Friday": "Fri",
    }
    sel_day = st.selectbox("Select Day", list(day_map.keys()), key="aa_day")
    day_df = merged[merged[day_map[sel_day]] == "Y"]

    subj_opts = sorted(day_df["Subject"].dropna().unique())
    sel_subj = st.selectbox("Select Subject", ["All"] + subj_opts, key="aa_subj")
    if sel_subj != "All":
        day_df = day_df[day_df["Subject"] == sel_subj]

    st.dataframe(day_df)
    st.write(f"Total classes: {len(day_df)}")

# ------------------ Dearborn ------------------

def show_dearborn():
    st.header("Dearborn Schedule by Day and Subject")

    # schedule has 3 title rows → skiprows=3
    raw = pd.read_csv(DB_FILE, dtype=str)

    merged = merge_monthly(raw, "Instructor ID")

    # human‑readable building + room
    bdict = load_buildings()
    merged["Location"] = (
        merged["Building Code"].map(bdict).fillna(merged["Building Code"]) +
        " " + merged["Room Code"].fillna("")
    )

    # drop requested / noise cols
    db_drop = [
        "Term Code",
        "Seq Number",
        "Instructor ID",
        "UM ID",
        "Room Code",
        "Building Code",
    ]
    merged = merged.drop(columns=[c for c in db_drop if c in merged.columns])

    sel_day = st.selectbox("Select Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], key="db_day")
    day_df = merged[merged[sel_day].isin(["M", "T", "W", "R", "F", "X"])]

    subj_opts = sorted(day_df["Subject"].dropna().unique())
    sel_subj = st.selectbox("Select Subject", ["All"] + subj_opts, key="db_subj")
    if sel_subj != "All":
        day_df = day_df[day_df["Subject"] == sel_subj]

    st.dataframe(day_df)
    st.write(f"Total classes: {len(day_df)}")

# ------------------ Flint ------------------

def show_flint():
    st.header("Flint Schedule by Day and Subject")

    df = pd.read_csv(FLINT_FILE, dtype=str)
    merged = merge_monthly(df, "UM ID") if "UM ID" in df.columns else df

    dow_map = {
        "Monday": "Mon",
        "Tuesday": "Tues",
        "Wednesday": "Wed",
        "Thursday": "Thurs",
        "Friday": "Fri",
    }
    sel_day = st.selectbox("Select Day", list(dow_map.keys()), key="fl_day")
    day_df = merged[merged[dow_map[sel_day]] == "X"]

    subj_opts = sorted(day_df["Subject"].dropna().unique())
    sel_subj = st.selectbox("Select Subject", ["All"] + subj_opts, key="fl_subj")
    if sel_subj != "All":
        day_df = day_df[day_df["Subject"] == sel_subj]

    st.dataframe(day_df)
    st.write(f"Total classes: {len(day_df)}")

# ------------------ Main ------------------

st.title("UM Schedule Explorer")

campus = st.selectbox("Select a Campus", ["Ann Arbor", "Dearborn", "Flint"])

if campus == "Ann Arbor":
    show_ann_arbor()
elif campus == "Dearborn":
    show_dearborn()
else:
    show_flint()
