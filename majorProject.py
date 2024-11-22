import math
import datetime
import pandas as pd
from geopy.distance import geodesic
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import streamlit as st
import folium
import streamlit.components.v1 as components


# Helper Functions
def calculate_speed(coord1, coord2, time1, time2):
    distance = geodesic(coord1, coord2).meters  # meters
    time_diff = (time2 - time1).total_seconds()  # seconds
    return (distance / time_diff) * 3.6 if time_diff > 0 else 0  # Speed in km/h


def calculate_heading(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(
        dlon
    )
    initial_bearing = math.atan2(x, y)
    return (math.degrees(initial_bearing) + 360) % 360  # Normalize to 0-360 degrees


def calculate_turning_angle(heading1, heading2):
    turning_angle = heading2 - heading1
    return abs(
        (turning_angle + 180) % 360 - 180
    )  # Absolute turning angle between 0 and 180 degrees


def process_gnss_points(gnss_points):
    """Process GNSS points to extract features like speed, distance, and turning angle."""
    speeds, distances, headings, turning_angles = [], [], [], []
    for i in range(1, len(gnss_points)):
        coord1, coord2 = gnss_points[i - 1][:2], gnss_points[i][:2]
        time1, time2 = gnss_points[i - 1][2], gnss_points[i][2]
        speed = calculate_speed(coord1, coord2, time1, time2)

        # Validate calculated speed
        if speed < 0 or speed > 200:
            speed = 0  # Mark as invalid

        speeds.append(speed)
        distances.append(geodesic(coord1, coord2).meters)
        heading = calculate_heading(coord1, coord2)
        headings.append(heading)
        if i > 1:
            turning_angles.append(calculate_turning_angle(headings[-2], heading))
        else:
            turning_angles.append(0)
    return speeds, distances, headings, turning_angles


# Training Data (Add more realistic data points)
data = {
    "speed": [45, 80, 30, 100, 50, 120, 20, 85, 55, 95, 25, 70],
    "distance": [2.0, 5.0, 1.5, 8.0, 3.5, 10.0, 1.2, 7.5, 3.0, 9.0, 2.5, 6.0],
    "turning_angle": [5, 0, 45, 0, 30, 0, 60, 10, 25, 0, 50, 5],
    "road_type": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],  # 0 = Service Road, 1 = Highway
}
df = pd.DataFrame(data)

# Train the Model
X = df[["speed", "distance", "turning_angle"]]
y = df["road_type"]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X_scaled, y)

# Streamlit UI
st.set_page_config(page_title="Enhanced GNSS Predictor", layout="wide")
st.title("GNSS Road Type Prediction with Validation ")

# Sidebar Input
with st.sidebar:
    st.header("🔍 Input GNSS Points")
    st.write("Enter the latitude, longitude, and timestamps for multiple GNSS points:")
    num_points = st.number_input("Number of GNSS Points", min_value=2, value=3)
    gnss_points = []
    for i in range(num_points):
        st.markdown(f"**Point {i + 1}**")
        # Normalize latitudes and longitudes using abs() to treat negative values as positive
        lat = st.number_input(
            f"Latitude {i + 1}", value=abs(18.4879 + i * 0.0005), format="%.4f"
        )
        lon = st.number_input(
            f"Longitude {i + 1}", value=abs(74.0234 + i * 0.0005), format="%.4f"
        )
        timestamp_str = st.text_input(
            f"Timestamp {i + 1}", f"2024-10-10 10:{i * 5:02d}:00"
        )
        timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        gnss_points.append([lat, lon, timestamp])

# Process GNSS Points
speeds, distances, headings, turning_angles = process_gnss_points(gnss_points)

# Prepare Features and Make Predictions
features = pd.DataFrame(
    {
        "speed": speeds,
        "distance": distances,
        "turning_angle": turning_angles,
    }
)
features_scaled = scaler.transform(features)
predictions = model.predict(features_scaled)

# Results Table
st.subheader("📋 Prediction Results")
results_table = pd.DataFrame(
    {
        "Speed (km/h)": speeds,
        "Distance (m)": distances,
        "Turning Angle (°)": turning_angles,
        "Predicted Road Type": [
            "Highway" if p == 1 else "Service Road" for p in predictions
        ],
    }
)
st.dataframe(results_table)

# Map Visualization
st.subheader("🗺 Route Map with Predictions")
map_ = folium.Map(location=[gnss_points[0][0], gnss_points[0][1]], zoom_start=14)

for i in range(len(gnss_points) - 1):
    line_color = "yellow" if predictions[i] == 1 else "blue"
    road_label = "Highway" if predictions[i] == 1 else "Service Road"
    folium.Marker(
        [gnss_points[i][0], gnss_points[i][1]],
        popup=f"Point {i + 1}: {road_label} | Speed: {speeds[i]:.2f} km/h",
        icon=folium.Icon(
            color="green" if predictions[i] == 1 else "red", icon="info-sign"
        ),
    ).add_to(map_)
    folium.PolyLine(
        [
            (gnss_points[i][0], gnss_points[i][1]),
            (gnss_points[i + 1][0], gnss_points[i + 1][1]),
        ],
        color=line_color,
        weight=5,
        opacity=0.7,
    ).add_to(map_)

folium.Marker(
    [gnss_points[-1][0], gnss_points[-1][1]], popup=f"Point {num_points}"
).add_to(map_)
map_.save("validated_route_map.html")
components.html(open("validated_route_map.html", "r").read(), height=500)
