import streamlit as st
import pandas as pd
import plotly.express as px
import leafmap.foliumap as leafmap  # Using folium-based Leafmap for Streamlit

# Set the page configuration to wide mode
st.set_page_config(page_title="South Africa's Seabirds Dashboard", layout="wide")

# Custom CSS for improved visuals
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
        background-color: #f0f2f6;
    }
    .stApp {
        background-color: #f0f2f6;
    }
    h1 {
        color: #2E4053;
        text-align: center;
        font-weight: bold;
    }
    h2 {
        color: #1F618D;
    }
    .title-sidebar {
        background-color: #AED6F1;
        padding: 15px;
        margin-bottom: 15px;
        margin-top: -25px;
        text-align: center;
    }
    .chart-title {
        text-align: center;
        font-weight: bold;
        font-size: 1.2rem;
        margin-top: 30px;
        margin-bottom: 20px;
    }
    
    [data-testid=stHeader] {background-color:  #f0f2f6;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar - Project Description and Image
st.sidebar.markdown(
    '<div class="title-sidebar"><h1>South Africa\'s Seabirds Species 🐧🦩🦜</h1></div>',
    unsafe_allow_html=True,
)
st.sidebar.image(r"images/africanpenguins_chadwick.jpg", use_column_width=True)

# Load the default seabird data from the CSV file
file_path = "data/seabird_atlas.csv"  # Replace with the actual file path

# Function to load the default data using the new cache method
@st.cache_data
def load_data():
    return pd.read_csv(file_path, delimiter=";")

# Load the default data
df = load_data()

# Convert 'Date' column to datetime
df["Date"] = pd.to_datetime(df["Date"])

# Calculate the total counts for each species by summing "Flying" and "Sitting"
df["Total Count"] = df["Flying"] + df["Sitting"]

# Initialize session states if they don't exist
if "selected_species" not in st.session_state:
    st.session_state.selected_species = [df["Common Name"].unique()[0]]
if "start_date" not in st.session_state:
    st.session_state.start_date = df["Date"].min()
if "end_date" not in st.session_state:
    st.session_state.end_date = df["Date"].max()
if "group_by" not in st.session_state:
    st.session_state.group_by = "Month"

# Sidebar for data filters
st.sidebar.header("Filter Data")

# Species multiselect with session state
selected_species = st.sidebar.multiselect(
    "Select Species",
    df["Common Name"].unique(),
    default=st.session_state.selected_species,
    key="selected_species"
)

# Date range input with session state
start_date, end_date = st.sidebar.date_input(
    "Select Date Range",
    [st.session_state.start_date, st.session_state.end_date],
    min_value=df["Date"].min(),
    max_value=df["Date"].max(),
    key="date_range"
)
st.session_state.start_date, st.session_state.end_date = start_date, end_date

# Apply filters to the dataset for time series and behavior plots
df_filtered = df[
    (df["Common Name"].isin(st.session_state.selected_species))
    & (df["Date"] >= pd.to_datetime(st.session_state.start_date))
    & (df["Date"] <= pd.to_datetime(st.session_state.end_date))
]

# **Total counts per species (not affected by filter)**
species_totals_all = df.groupby("Common Name")[["Total Count"]].sum().reset_index()

# Bar graph for total counts per species based on "Flying" + "Sitting" for the entire dataset
st.markdown(
    '<div class="chart-title">Total Counts per Species (Flying + Sitting) - Entire Dataset</div>',
    unsafe_allow_html=True,
)
fig_species_counts = px.bar(
    species_totals_all,
    x="Common Name",
    y="Total Count",
    color="Common Name",
    title="",
    labels={"Total Count": "Total Observations"},
    color_discrete_sequence=px.colors.qualitative.Vivid,
)
fig_species_counts.update_layout(showlegend=False)
st.plotly_chart(fig_species_counts, use_container_width=True)

# Divider
st.markdown("---")

# Create two columns for data table and map
col1, col2 = st.columns(2)

# Column 1: Data table
with col1:
    st.subheader("Filtered Data")
    st.dataframe(df_filtered, height=400)

# Column 2: Map with seabird sightings using Leafmap
with col2:
    st.subheader("Map of Seabird Sightings")

    # Create a map centered around South Africa using Leafmap
    m = leafmap.Map(center=[-30, 22], zoom=5)  # Centered on South Africa

    # Add basemaps as layers
    m.add_basemap("Esri.WorldImagery")  # Satellite Imagery layer
    m.add_basemap("Esri.WorldTopoMap")  # Topographic map layer
    m.add_basemap("OpenStreetMap")  # Default OpenStreetMap layer

    # Display the Leafmap map with layers in Streamlit
    m.to_streamlit(height=400)

# Divider
st.markdown("---")

# Time series grouping option with session state
st.markdown(
    '<div class="chart-title">Time Series of Seabird Observations (Using Total Count)</div>',
    unsafe_allow_html=True,
)

# Check session state before creating the widget to avoid modification errors
if "group_by" not in st.session_state:
    st.session_state.group_by = "Month"

group_by = st.selectbox(
    "Group By", ["Day", "Month", "Year"],
    index=["Day", "Month", "Year"].index(st.session_state.group_by),
    key="group_by"
)

# Grouping by day, month, or year and converting the Period to string
if st.session_state.group_by == "Day":
    df_filtered["Period"] = df_filtered["Date"].dt.date
elif st.session_state.group_by == "Month":
    df_filtered["Period"] = df_filtered["Date"].dt.to_period("M").astype(str)
elif st.session_state.group_by == "Year":
    df_filtered["Period"] = df_filtered["Date"].dt.to_period("Y").astype(str)

# Group the filtered data by species, period, and "Total Count"
time_series = (
    df_filtered.groupby(["Period", "Common Name"])[["Total Count"]].sum().reset_index()
)

# Plot the time series bar chart with different species as grouped bars, using "Total Count"
fig_time = px.bar(
    time_series,
    x="Period",
    y="Total Count",
    color="Common Name",
    barmode="group",
    labels={"Total Count": "Total Count", "Period": f"{group_by}"},
    color_discrete_sequence=px.colors.qualitative.Pastel1,
)
fig_time.update_layout(
    title=f"Seabird Observations Grouped by {group_by} (Using Total Count)",
    legend_title_text="Species",
)
st.plotly_chart(fig_time, use_container_width=True)

# Divider
st.markdown("---")

# Behavior analysis (Flying vs Sitting) for the filtered data
st.markdown(
    '<div class="chart-title">Behavior Analysis (Flying vs Sitting)</div>',
    unsafe_allow_html=True,
)

behavior = df_filtered.groupby("Common Name")[["Flying", "Sitting"]].sum().reset_index()

# Plot the behavior analysis with different species as grouped bars
fig_behavior = px.bar(
    behavior,
    x="Common Name",
    y=["Flying", "Sitting"],
    barmode="group",
    labels={"value": "Count", "variable": "Behavior"},
    title="",
    color_discrete_sequence=px.colors.qualitative.Safe,
)
fig_behavior.update_layout(
    title="Flying vs Sitting Behavior (Filtered)", legend_title_text="Behavior"
)
st.plotly_chart(fig_behavior, use_container_width=True)

# Data Source Section at the bottom of the sidebar
st.sidebar.markdown("### Data Source")
st.sidebar.markdown(
    """
**The Atlas of Seabirds at Sea (AS@S)**
"""
)
st.sidebar.markdown(
    """
[The Atlas of Seabirds at Sea (AS@S)](http://seabirds.saeon.ac.za/)
"""
)
