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
filtered_df = sched[sched[selDay] == 'Y']

# Create a dropdown for campuses
campus_counts = filtered_df['CampusPrediction'].value_counts().to_dict()
campus_options = [f"{campus} ({count})" for campus, count in campus_counts.items()]
selected_campus_option = st.selectbox('Select a campus:', campus_options)

# Extract the campus name from the selected option
selected_campus = selected_campus_option.split(' (')[0]

# Filter the DataFrame based on the selected campus
campus_filtered_df = filtered_df[filtered_df['CampusPrediction'] == selected_campus]

# Create a dictionary of buildings and their counts for the selected campus
building_counts = campus_filtered_df['BldgPrediction'].value_counts().to_dict()
building_options = [f"{building} ({count})" for building, count in building_counts.items()]

# Create a dropdown for buildings
selected_building_option = st.selectbox('Select a building:', building_options)

# Extract the building name from the selected option
selected_building = selected_building_option.split(' (')[0]

# Filter the DataFrame based on the selected building
final_df = campus_filtered_df[campus_filtered_df['BldgPrediction'] == selected_building]

# Display the final filtered DataFrame
st.write(f"Showing schedule for {selected_building} on {selected_campus} campus for {selected_day}:")
st.dataframe(final_df)
