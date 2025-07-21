import streamlit as st
import pandas as pd
import json
import requests

# ------------------ Configuration ------------------
LEO_PREFIX = "LEO"  # keep any Job Title that begins with this text (case‑insensitive)

# -------------- Utilities --------------
@st.cache_data
def load_buildings():
    """Return dict mapping building codes → full names/addresses (for Dearborn)."""
    url = "https://raw.githubusercontent.com/umsi-amadaman/LEOcourseschedules/main/UMICHbuildings_dict.json"
    return json.loads(requests.get(url).text)


@st.cache_data
def load_monthly():
    """July 2025 monthly payroll / dues file covering all three campuses."""
    url = "https://github.com/umsi-amadaman/LEOcourseschedules/raw/main/Summer25/MonthlyJuly25.csv"
    df = pd.read_csv(url, dtype=str)
    # normalise ID & helpful flags
    df["UM ID"] = pd.to_numeric(df["UM ID"], errors="coerce")
    df["Pays LEO Dues"] = df["Deduction"].str.contains("LEO", na=False)
    return df.dropna(subset=["UM ID"])


def merge_and_filter(schedule_df: pd.DataFrame, id_col: str) -> pd.DataFrame:
    """Helper: merge schedule with monthly, keep only rows whose Job Title starts with LEO."""
    monthly = load_monthly()

    # id columns as numeric to ensure reliable join
    schedule_df[id_col] = pd.to_numeric(schedule_df[id_col], errors="coerce")
    schedule_df = schedule_df.dropna(subset=[id_col])

    merged = schedule_df.merge(monthly, left_on=id_col, right_on="UM ID", how="left")

    # filter for lecturers (Job Title beginning with LEO, case‑insensitive)
    merged = merged[merged["Job Title"].str.startswith(LEO_PREFIX, na=False, case=False)]
    return merged


# -------------- Campus‑specific views --------------

def show_ann_arbor():
    st.header("Ann Arbor Schedule by Day and Subject")
    df = pd.read_csv("AASchedSum25.csv", dtype=str)

    merged_df = merge_and_filter(df, "Class Instr ID")

    # --- Select / drop columns ---
    drop_cols = [
        "Class Instr ID", "Facility ID", "Employee Last Name", "Employee First Name",
        "UM ID", "Rec #", "Class Indc", "Job Code", "Hire Begin Date",
        "Appointment Start Date", "Appointment End Date", "Comp Frequency",
        "Appointment Period", "Appointment Period Descr", "Comp Rate",
        # "Deduction",  ← keep for dues
        "Home Address 1", "Home Address 2", "Home Address 3", "Home City", "Home State",
        "Home Postal", "Home County", "Home Country", "Home Phone", "UM Address 1",
        "UM Address 2", "UM Address 3", "UM City", "UM State", "UM Postal", "UM County",
        "UM Country", "UM Phone", "Employee Status", "Employeee Status Descr", "uniqname",
        "Class Mtg Nbr"
    ]
    merged_df = merged_df.drop(columns=[c for c in drop_cols if c in merged_df.columns])

    # Build friendly classroom location string
    if set(["Facility Descr", "Room"]).issubset(merged_df.columns):
        merged_df["Location"] = merged_df["Facility Descr"].fillna("") + " " + merged_df["Room"].fillna("")

    # --- Interactive filters ---
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    dow_map = {"Monday": "Mon", "Tuesday": "Tues", "Wednesday": "Wed", "Thursday": "Thurs", "Friday": "Fri"}

    sel_day = st.selectbox("Select Day", days, key="aa_day_select")
    day_df = merged_df[merged_df[dow_map[sel_day]] == "Y"]

    subj_opts = sorted(day_df["Subject"].dropna().unique())
    sel_subj = st.selectbox("Select Subject", ["All"] + subj_opts, key="aa_subj_select")
    if sel_subj != "All":
        day_df = day_df[day_df["Subject"] == sel_subj]

    st.dataframe(day_df)
    st.write(f"Total LEO classes: {len(day_df)}")


def show_dearborn():
    st.header("Dearborn Schedule by Day and Subject")
    df = pd.read_csv("DBSchedSum25.csv", skiprows=3, dtype=str)

    # tidy col names
    df.columns = [
        "Term Code", "Term Desc", "Subject", "Course Number", "Seq Number", "Instructor ID", "Last", "First",
        "Room", "Bldg", "Instr Method", "Pattern", "Begin", "End", "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday", "Instr Mode"
    ]

    merged = merge_and_filter(df, "Instructor ID")

    # human‑readable building names
    bdict = load_buildings()
    if set(["Bldg", "Room"]).issubset(merged.columns):
        merged["Location"] = merged["Bldg"].map(bdict).fillna(merged["Bldg"]) + " " + merged["Room"].fillna("")

    # Filters
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    sel_day = st.selectbox("Select Day", days, key="db_day_select")
    df_day = merged[merged[sel_day].isin(["M", "T", "W", "R", "F", "X"])]

    subj_opts = sorted(df_day["Subject"].dropna().unique())
    sel_subj = st.selectbox("Select Subject", ["All"] + subj_opts, key="db_subj_select")
    if sel_subj != "All":
        df_day = df_day[df_day["Subject"] == sel_subj]

    st.dataframe(df_day)
    st.write(f"Total LEO classes: {len(df_day)}")


def show_flint():
    st.header("Flint Schedule by Day and Subject")
    df = pd.read_csv("Flint_S25.csv", dtype=str)

    # guess ID column – adjust if your CSV uses another label
    possible_ids = ["Class Instr ID", "Instructor ID", "UM ID"]
    id_col = next((c for c in possible_ids if c in df.columns), None)
    if id_col is None:
        st.error("Could not find an instructor ID column in Flint_S25.csv – please rename appropriately.")
        return

    merged = merge_and_filter(df, id_col)

    # interactive Filters
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    dow_map = {"Monday": "Mon", "Tuesday": "Tues", "Wednesday": "Wed", "Thursday": "Thurs", "Friday": "Fri"}

    sel_day = st.selectbox("Select Day", days, key="fl_day_select")
    df_day = merged[merged[dow_map[sel_day]] == "X"]

    subj_opts = sorted(df_day["Subject"].dropna().unique())
    sel_subj = st.selectbox("Select Subject", ["All"] + subj_opts, key="fl_subj_select")
    if sel_subj != "All":
        df_day = df_day[df_day["Subject"] == sel_subj]

    st.dataframe(df_day)
    st.write(f"Total LEO classes: {len(df_day)}")


# -------------- Main ------------------
st.title("UM Schedule Explorer")
option = st.selectbox("Select a Campus", ["Ann Arbor", "Dearborn", "Flint"])

if option == "Ann Arbor":
    show_ann_arbor()
elif option == "Dearborn":
    show_dearborn()
else:
    show_flint()
