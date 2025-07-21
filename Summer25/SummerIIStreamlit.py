import streamlit as st
import pandas as pd
import json
import requests
from pathlib import Path

# ------------------ Paths / Constants ------------------
BASE_DIR = Path(__file__).resolve().parent
AA_FILE      = BASE_DIR / "AASchedSum25.csv"
DB_FILE      = BASE_DIR / "DBSchedSum25.csv"
FLINT_FILE   = BASE_DIR / "Flint_S25.csv"
MONTHLY_FILE = BASE_DIR / "MonthlyJuly25.csv"
LEO_PREFIX   = "leo"  # case‑insensitive prefix for lecturers

# ------------------ Helpers ------------------
@st.cache_data
def load_buildings():
    url = "https://raw.githubusercontent.com/umsi-amadaman/LEOcourseschedules/main/UMICHbuildings_dict.json"
    return requests.get(url).json()

@st.cache_data
def load_monthly():
    return pd.read_csv(MONTHLY_FILE, dtype=str)

def merge_monthly(df: pd.DataFrame, id_col: str) -> pd.DataFrame:
    """Merge schedule with Monthly and retain only rows whose Job Title begins with LEO."""
    monthly = load_monthly()
    # numeric‑safe IDs for robust merge
    df[id_col] = pd.to_numeric(df[id_col], errors="coerce")
    monthly["UM ID"] = pd.to_numeric(monthly["UM ID"], errors="coerce")
    merged = df.merge(monthly, left_on=id_col, right_on="UM ID", how="left")

    # keep lecturers (case‑insensitive) and non‑blank titles
    mask = merged["Job Title"].fillna("").str.lower().str.startswith(LEO_PREFIX)
    merged = merged[mask & merged["Job Title"].str.strip().ne("")]
    return merged

# ------------------ Ann Arbor ------------------

def show_ann_arbor():
    st.header("Ann Arbor Schedule by Day and Subject")
    raw = pd.read_csv(AA_FILE, dtype=str)
    merged = merge_monthly(raw, "Class Instr ID")

    # original big drop list (minus "Deduction") plus the four extra columns the user asked for
    aa_drop = [
        "Class Instr ID", "Facility ID", "Facility Descr", "Employee Last Name", "Employee First Name",
        "UM ID", "Rec #", "Class Indc", "Job Code", "Hire Begin Date", "Appointment Start Date",
        "Appointment End Date", "Comp Frequency", "Appointment Period", "Appointment Period Descr",
        "Comp Rate", "Home Address 1", "Home Address 2", "Home Address 3", "Home City", "Home State",
        "Home Postal", "Home County", "Home Country", "Home Phone", "UM Address 1", "UM Address 2",
        "UM Address 3", "UM City", "UM State", "UM Postal", "UM County", "UM Country", "UM Phone",
        "Employee Status", "Employeee Status Descr", "uniqname", "Class Mtg Nbr",
        # newly requested removals
        "Term", "Class Nbr", "Department ID", "Employee Status Descr"
    ]
    merged.drop(columns=[c for c in aa_drop if c in merged.columns], inplace=True)

    # Day / Subject filters
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    day_map = {"Monday": "Mon", "Tuesday": "Tues", "Wednesday": "Wed", "Thursday": "Thurs", "Friday": "Fri"}
    sel_day = st.selectbox("Select Day", days, key="aa_day")
    day_df = merged[merged[day_map[sel_day]].eq("Y")]

    subj_opts = sorted(day_df["Subject"].dropna().unique())
    sel_subj = st.selectbox("Select Subject", ["All"] + subj_opts, key="aa_subj")
    if sel_subj != "All":
        day_df = day_df[day_df["Subject"] == sel_subj]

    st.dataframe(day_df)
    st.write(f"Total classes: {len(day_df)}")

# ------------------ Dearborn ------------------

def show_dearborn():
    st.header("Dearborn Schedule by Day and Subject")

    raw = pd.read_csv(DB_FILE, dtype=str).dropna(axis=1, how="all")
    raw.columns = [c.strip() for c in raw.columns]

    rename_map = {
        "Subject Code": "Subject",
        "SEQ Number": "Seq Number",
        "Primary Instructor ID": "Instructor ID",
        "Primary Instructor Last Name": "Last",
        "Primary Instructor First Name": "First",
        "Room Code": "Room",
        "Building Code": "Bldg",
        "Monday Indicator": "Monday",
        "Tuesday Indicator": "Tuesday",
        "Wednesday Indicator": "Wednesday",
        "Thursday Indicator": "Thursday",
        "Friday Indicator": "Friday",
        "Saturday Indicator": "Saturday",
        "Sunday Indicator": "Sunday",
    }
    raw.rename(columns=rename_map, inplace=True)

    merged = merge_monthly(raw, "Instructor ID")

    db_drop = ["Term Code", "Seq Number", "Instructor ID"]
    merged.drop(columns=[c for c in db_drop if c in merged.columns], inplace=True)

    bdict = load_buildings()
    merged["Location"] = merged["Bldg"].map(bdict).fillna(merged["Bldg"]) + " " + merged["Room"].fillna("")

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    sel_day = st.selectbox("Select Day", days, key="db_day")
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
    raw = pd.read_csv(FLINT_FILE, dtype=str)
    merged = merge_monthly(raw, "Instructor ID")

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    dow_map = {"Monday": "Mon", "Tuesday": "Tues", "Wednesday": "Wed", "Thursday": "Thurs", "Friday": "Fri"}
    sel_day = st.selectbox("Select Day", days, key="fl_day")
    day_df = merged[merged[dow_map[sel_day]].eq("X")]

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
