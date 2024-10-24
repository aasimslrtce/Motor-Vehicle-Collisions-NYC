import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.express as px

DATA_URL = ("C:/Users/shaik.000/Downloads/rospl/Motor_Vehicle_Collisions_-_Crashes.csv")

st.title("Motor Vehicle Collisions Analysis in New York City")
st.markdown(
    "An interactive dashboard for exploring collision data in NYC. "
    "Use the filters to analyze trends in injuries and collisions throughout the city."
)

@st.cache_data(persist=True)
def load_data(nrows):
    data = pd.read_csv(DATA_URL, nrows=nrows, parse_dates=[['CRASH_DATE', 'CRASH_TIME']])
    data.dropna(subset=['LATITUDE', 'LONGITUDE'], inplace=True)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis="columns", inplace=True)
    data.rename(columns={"crash_date_crash_time": "date/time"}, inplace=True)
    return data

data = load_data(100000)
original_data = data.copy()

tab1, tab2 = st.tabs(["Motor Vehicle Collisions in NYC", "Enhanced Visualizations"])

with tab1:
    st.header("Where are the most people injured in NYC?")
    injured_people = st.slider("Adjust the slider to view locations where a specified number of individuals were injured in vehicle collisions", 0, 19)
    st.map(data.query("injured_persons >= @injured_people")[["latitude", "longitude"]].dropna(how="any"))

    st.header("How many collisions occur during a given time of day?")
    hour = st.slider("Select an hour to examine the frequency of collisions during that specific time", 0, 23)
    data = original_data[original_data['date/time'].dt.hour == hour]

    st.markdown("Vehicle collisions between %i:00 and %i:00" % (hour, (hour + 1) % 24))
    midpoint = (np.average(data["latitude"]), np.average(data["longitude"]))

    st.write(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state={
            "latitude": midpoint[0],
            "longitude": midpoint[1],
            "zoom": 11,
            "pitch": 50,
        },
        layers=[
            pdk.Layer(
                "HexagonLayer",
                data=data[['date/time', 'latitude', 'longitude']],
                get_position=["longitude", "latitude"],
                auto_highlight=True,
                radius=100,
                extruded=True,
                pickable=True,
                elevation_scale=4,
                elevation_range=[0, 1000],
            ),
        ],
    ))

    st.subheader("Collision Frequency by Minute Between %i:00 and %i:00" % (hour, (hour + 1) % 24))
    filtered = data[(data['date/time'].dt.hour >= hour) & (data['date/time'].dt.hour < (hour + 1))]
    hist = np.histogram(filtered['date/time'].dt.minute, bins=60, range=(0, 60))[0]
    chart_data = pd.DataFrame({"minute": range(60), "crashes": hist})
    fig = px.bar(chart_data, x='minute', y='crashes', hover_data=['minute', 'crashes'], height=400)
    st.write(fig)

    st.header("Most Dangerous Streets by Affected Class")
    select = st.selectbox('Select the class of individuals affected in collisions', ['Pedestrians', 'Cyclists', 'Motorists'])

    if select == 'Pedestrians':
        st.write(original_data.query("injured_pedestrians >= 1")[["on_street_name", "injured_pedestrians"]].sort_values(by=['injured_pedestrians'], ascending=False).dropna(how="any")[:5])
    elif select == 'Cyclists':
        st.write(original_data.query("injured_cyclists >= 1")[["on_street_name", "injured_cyclists"]].sort_values(by=['injured_cyclists'], ascending=False).dropna(how="any")[:5])
    else:
        st.write(original_data.query("injured_motorists >= 1")[["on_street_name", "injured_motorists"]].sort_values(by=['injured_motorists'], ascending=False).dropna(how="any")[:5])

    if st.checkbox("Show Raw Data Table", False):
        st.subheader('Raw Data')
        st.write(data)

with tab2:
    
    st.header("Monthly Trends in Collisions")
    original_data['month'] = original_data['date/time'].dt.to_period('M').dt.to_timestamp()
    monthly_trends = original_data.groupby('month').size().reset_index(name='Number of Collisions')
    fig_monthly = px.line(
        monthly_trends, 
        x='month', 
        y='Number of Collisions', 
        title='Monthly Collision Trends in NYC', 
        labels={'month': 'Month', 'Number of Collisions': 'Collisions'}
    )
    st.write(fig_monthly)

    st.header("Correlation Analysis")
    corr_columns = ['injured_persons', 'killed_persons', 'injured_pedestrians', 'injured_cyclists', 'injured_motorists']
    correlation_matrix = original_data[corr_columns].corr()
    fig_corr = px.imshow(correlation_matrix, text_auto=True, title="Correlation Matrix of Injuries and Fatalities")
    st.write(fig_corr)

    st.header("Severity Analysis")
    original_data['severity'] = original_data['injured_persons'] + 2 * original_data['killed_persons']
    severity_distribution = original_data['severity'].value_counts().reset_index(name='Counts')
    fig_severity = px.bar(severity_distribution, x='severity', y='Counts', title='Collision Severity Distribution', labels={'index': 'Severity Level', 'Counts': 'Number of Collisions'})
    st.write(fig_severity)

    st.header("Heatmap of Collision Density in NYC")
    st.map(original_data[['latitude', 'longitude']].dropna(how="any"))

    st.header("Most Common Vehicle Types Involved in Collisions")

    # Count the occurrences of vehicle_type_1 involved in collisions
    vehicle_type_counts = original_data['vehicle_type_1'].value_counts().reset_index()
    vehicle_type_counts.columns = ['Vehicle Type', 'Number of Collisions']

# Create a bar chart to show the most common vehicle types involved in collisions
    fig_vehicle_type = px.bar(
        vehicle_type_counts.head(10),  # Display the top 10 most common vehicle types
        x='Vehicle Type', 
        y='Number of Collisions', 
        title='Top 10 Vehicle Types Involved in Collisions',
        labels={'Vehicle Type': 'Vehicle Type', 'Number of Collisions': 'Number of Collisions'},
        height=400
    )

# Display the bar chart in the Streamlit app
    st.write(fig_vehicle_type)

