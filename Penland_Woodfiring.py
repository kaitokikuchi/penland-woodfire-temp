import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection


@st.cache_data
def get_data():
    # Create a connection object.
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Load data
    df = conn.read()
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    return df


source = get_data()

# Read target temperature data
target_temp = pd.read_csv(
    "Penland_Woodfiring_Temp_2024.csv",
    usecols=["Time", "Target"],
)

# Rename "Time" column to "Timestamp" and convert to datetime
target_temp.rename(columns={"Time": "Timestamp"}, inplace=True)
target_temp["Timestamp"] = pd.to_datetime(target_temp["Timestamp"])

# Resample target_temp to align with source data
target_temp.set_index("Timestamp", inplace=True)
target_temp = target_temp.resample(
    "T"
).interpolate()  # Resample to minute intervals and interpolate
target_temp = target_temp.reset_index()

# Merge source data and target temperature data
combined_data = source.merge(target_temp, on="Timestamp", how="outer")

# Sort data by datetime
combined_data = combined_data.sort_values(by="Timestamp")

# Fill missing values
combined_data = combined_data.fillna(method="bfill")

# Melt the data frame for Plotly Express
melted_data = combined_data.melt(
    id_vars=["Timestamp"],
    value_vars=["Front", "Middle", "Back", "Target"],
    var_name="Measurement",
    value_name="Temperature",
)

# Create the plotly figure using plotly express
fig = px.line(
    melted_data,
    x="Timestamp",
    y="Temperature",
    color="Measurement",
    labels={"Temperature": "Temperature (F)", "Measurement": "Measurement"},
    title="Temperature Measurements",
)

# Update layout for hover mode and axis titles
fig.update_layout(
    hovermode="x unified",
    xaxis_title="Time",
    yaxis_title="Temperature (F)",
)

# Display the plotly chart in Streamlit
st.plotly_chart(fig, use_container_width=True)
