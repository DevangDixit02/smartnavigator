import datetime
from geopy.distance import geodesic
import folium
import streamlit as st
import streamlit.components.v1 as components


# Helper function for speed calculation
def calculate_speed(coord1, coord2, time1, time2):
    """Calculate speed between two GNSS points."""
    distance = geodesic(coord1, coord2).meters  # meters
    time_diff = (time2 - time1).total_seconds()  # seconds
    return (distance / time_diff) * 3.6  # Speed in km/h


# Helper function for calculating distance
def calculate_distance(coord1, coord2):
    """Calculate the distance between two GNSS coordinates."""
    return geodesic(coord1, coord2).kilometers  # return distance in km


# Streamlit UI Configuration
st.set_page_config(
    page_title="GNSS Road Type Predictor",
    page_icon="🚗",
    layout="centered",
)

# Sidebar for input
with st.sidebar:
    st.title("GNSS Coordinate Input")
    st.write("### Enter two GNSS points:")

    # Inputs for the first coordinate and timestamp
    st.markdown("**Start Point**")
    lat1 = st.number_input("Latitude (Start)", value=18.4879, format="%.4f")
    lon1 = st.number_input("Longitude (Start)", value=74.0234, format="%.4f")
    timestamp1_str = st.text_input(
        "Timestamp (Start) [YYYY-MM-DD HH:MM:SS]", "2024-10-10 10:00:00"
    )
    timestamp1 = datetime.datetime.strptime(timestamp1_str, "%Y-%m-%d %H:%M:%S")

    # Inputs for the second coordinate and timestamp
    st.markdown("**End Point**")
    lat2 = st.number_input("Latitude (End)", value=18.4885, format="%.4f")
    lon2 = st.number_input("Longitude (End)", value=74.0240, format="%.4f")
    timestamp2_str = st.text_input(
        "Timestamp (End) [YYYY-MM-DD HH:MM:SS]", "2024-10-10 10:10:00"
    )
    timestamp2 = datetime.datetime.strptime(timestamp2_str, "%Y-%m-%d %H:%M:%S")

    st.write("### Instructions")
    st.write(
        "Enter the latitude, longitude, and timestamps for two GNSS points. "
        # "The app will calculate the speed and distance and predict the road type."
    )
    st.markdown("---")

# Main Content
st.title("GNSS Road Type Prediction ")
# st.write("A simple app to predict road type based on GNSS coordinates and speed.")

# Calculate speed
speed = calculate_speed((lat1, lon1), (lat2, lon2), timestamp1, timestamp2)

# Calculate distance between the two points
distance = calculate_distance((lat1, lon1), (lat2, lon2))

# Predict road type based on speed
road_type = "Highway" if speed > 60 else "Service Road"

# Results Section
st.markdown("## Results")
col1, col2 = st.columns(2)
with col1:
    st.metric(label="Calculated Speed", value=f"{speed:.2f} km/h")
with col2:
    st.metric(label="Distance", value=f"{distance:.2f} km")

st.write(f"### Predicted Road Type: **{road_type}**")

# Create a Folium map and plot the route
st.markdown("## Map")
map_ = folium.Map(location=[(lat1 + lat2) / 2, (lon1 + lon2) / 2], zoom_start=14)

# Define polyline color based on road type
line_color = "yellow" if road_type == "Highway" else "blue"

# Plot the start and end markers with custom icons
folium.Marker(
    [lat1, lon1], popup="Start Point", icon=folium.Icon(color="green", icon="play")
).add_to(map_)
folium.Marker(
    [lat2, lon2], popup="End Point", icon=folium.Icon(color="red", icon="stop")
).add_to(map_)

# Draw the polyline with the appropriate color
folium.PolyLine(
    [(lat1, lon1), (lat2, lon2)], color=line_color, weight=4, opacity=0.7
).add_to(map_)

# Add a label for speed and distance at the midpoint
mid_lat = (lat1 + lat2) / 2
mid_lon = (lon1 + lon2) / 2
folium.Marker(
    [mid_lat, mid_lon],
    popup=f"Speed: {speed:.2f} km/h\nDistance: {distance:.2f} km",
    icon=folium.Icon(color="blue", icon="info-sign"),
).add_to(map_)

# Save map and display it
map_.save("route_map_with_distance.html")
components.html(open("route_map_with_distance.html", "r").read(), height=600)


