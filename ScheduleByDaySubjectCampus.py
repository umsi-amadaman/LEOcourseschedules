import json 
import requests
import streamlit as st
import pandas as pd


url = "https://raw.githubusercontent.com/umsi-amadaman/LEOcourseschedules/main/UMICHbuildings_dict.json"
response = requests.get(url)
my_dict = json.loads(response.text)



DATA = 'https://github.com/umsi-amadaman/LEOcourseschedules/raw/main/LEOAug24Schedule.csv'

sched = pd.read_csv(DATA)

# Title of the app
st.title('Schedule Viewer by Day - Campus - Building')

# Create a dropdown for days of the week
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
selected_day = st.selectbox('Select a day of the week:', days)

DaysOfWeek = {'Monday':'Mon', 'Tuesday':'Tues', 'Wednesday':'Wed', 'Thursday':'Thurs', 'Friday':'Fri', 'Saturday':'Sat', 'Sunday':'Sun'}

selDay = DaysOfWeek[selected_day]

# Filter the DataFrame based on the selected day
# Assuming you have a 'Day' column in your DataFrame
day_filtered_df = sched[sched[selDay] == 'Y']







# Create a dropdown for subjects
subject_counts = day_filtered_df['Subject'].value_counts().to_dict()
subject_options = [f"{subject} ({count})" for subject, count in subject_counts.items()]
selected_subject_option = st.selectbox('Select a subject:', subject_options)

# Extract the subject name from the selected option
selected_subject = selected_subject_option.split(' (')[0]

# Filter the DataFrame based on the selected subject
subject_filtered_df = day_filtered_df[day_filtered_df['Subject'] == selected_subject]

# Create a dropdown for campuses
campus_counts = subject_filtered_df['CampusPrediction'].value_counts().to_dict()
campus_options = [f"{campus} ({count})" for campus, count in campus_counts.items()]
selected_campus_option = st.selectbox('Select a campus:', campus_options)

# Extract the campus name from the selected option
selected_campus = selected_campus_option.split(' (')[0]

# Filter the DataFrame based on the selected campus
final_df = subject_filtered_df[subject_filtered_df['CampusPrediction'] == selected_campus]

# Sort the final_df by BldgPrediction
final_df = final_df.sort_values(by='BldgPrediction')

# Display the final filtered DataFrame
st.write(f"Showing schedule for {selected_subject} on {selected_campus} campus for {selected_day}:")
st.dataframe(final_df)

# Optional: Display unique buildings for this selection
unique_buildings = final_df['BldgPrediction'].unique()
st.write(f"Buildings used: {', '.join(unique_buildings)}")