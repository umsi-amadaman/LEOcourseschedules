import json 
import requests
import streamlit as st
import pandas as pd


url = "https://raw.githubusercontent.com/umsi-amadaman/LEOcourseschedules/main/UMICHbuildings_dict.json"
response = requests.get(url)
new_Bldgs = json.loads(response.text)



DATA = 'https://github.com/umsi-amadaman/LEOcourseschedules/raw/main/LEOAug24Schedule.csv'

sched = pd.read_csv(DATA)

def find_longest_match(string, key_list):
    matches = [key for key in key_list if string in key or key in string]
    return max(matches, key=len, default=None)

# Create new columns with default values
sched['RoomPrediction'] = ''
sched['BldgPrediction'] = ''
sched['CampusPrediction'] = ''

# Iterate through unique Facility IDs
for x in sched['Facility ID'].unique():
    if isinstance(x, str):
        match = find_longest_match(x, new_Bldgs.keys())
        if match:
            # Remove the matched part from the original string
            remaining = x.replace(match, '').strip()
            
            # Update the DataFrame for all rows with this Facility ID
            mask = sched['Facility ID'] == x
            sched.loc[mask, 'RoomPrediction'] = remaining
            sched.loc[mask, 'BldgPrediction'] = match
            sched.loc[mask, 'CampusPrediction'] = new_Bldgs[match][-1]
        else:
            # If no match, set only RoomPrediction to the original string
            mask = sched['Facility ID'] == x
            sched.loc[mask, 'BldgPrediction'] = x

# After the loop, fill NaN values if any
sched['RoomPrediction'] = sched['RoomPrediction'].fillna('')
sched['BldgPrediction'] = sched['BldgPrediction'].fillna('')
sched['CampusPrediction'] = sched['CampusPrediction'].fillna('')

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

# Add "ALL" option at the beginning of the list
all_count = campus_filtered_df['BldgPrediction'].count()
building_options.insert(0, f"ALL ({all_count})")

# Create a dropdown for buildings
selected_building_option = st.selectbox('Select a building:', building_options)

# Extract the building name from the selected option
selected_building = selected_building_option.split(' (')[0]

# Filter the DataFrame based on the selected building
if selected_building == "ALL":
    final_df = campus_filtered_df
else:
    final_df = campus_filtered_df[campus_filtered_df['BldgPrediction'] == selected_building]

# Display the final filtered DataFrame
if selected_building == "ALL":
    st.write(f"Showing schedule for ALL buildings on {selected_campus} campus for {selected_day}:")
else:
    st.write(f"Showing schedule for {selected_building} on {selected_campus} campus for {selected_day}:")

final_df = final_df.drop(columns=['Term', 'Term Descrshort', 'Class Nbr', 'Class Instr ID'])

final_df = final_df[['Meeting Time Start', 'Meeting Time End','RoomPrediction', 'BldgPrediction', 'Crse Descr', 'Subject',
       'Catalog Nbr', 'Class Section', 'Class Instr Name',
       'Class Mtg Nbr', 'Facility ID', 'Facility Descr',
       'Instruction Mode Descrshort', 'Meeting Start Dt', 'Meeting End Dt',
       'Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat', 'Sun', 'CampusPrediction']]

st.dataframe(final_df)

# Optional: Display some statistics
if selected_building == "ALL":
    st.write(f"Total classes on {selected_campus} campus for {selected_day}: {len(final_df)}")
else:
    st.write(f"Total classes in {selected_building} on {selected_campus} campus for {selected_day}: {len(final_df)}")
