import streamlit as st
import pandas as pd
import altair as alt
from streamlit_gsheets import GSheetsConnection


def get_data():
    # Create a connection object.
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Load data
    df = conn.read()
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    return df


source = get_data()

# Melt the source data for altair plotting
source_melted = source.reset_index(drop=True).melt(
    "Timestamp", var_name="Measurements", value_name="temp"
)

target_temp = pd.read_csv(
    "Penland_Woodfiring_Temp_2024.csv",
    usecols=["Time", "Target Temperature"],
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

# Melt the target temperature data for altair plotting
target_temp_melted = target_temp.melt(
    "Timestamp", var_name="Measurements", value_name="temp"
)

# Combine the data
combined_data = pd.concat([source_melted, target_temp_melted])

# Create a selection that chooses the nearest point & selects based on x-value
nearest = alt.selection_point(
    nearest=True, on="mouseover", fields=["Timestamp"], empty=False
)

# The basic line
line = (
    alt.Chart(combined_data)
    .mark_line(interpolate="basis")
    .encode(
        x=alt.X("yearmonthdatehoursminutes(Timestamp):T", title="Time"),
        y=alt.Y("temp:Q", title="Temperature (F)"),
        color="Measurements:N",
    )
)

# Transparent selectors across the chart. This is what tells us
# the x-value of the cursor
selectors = (
    alt.Chart(combined_data)
    .mark_point()
    .encode(
        x=alt.X("yearmonthdatehoursminutes(Timestamp):T", title="Time"),
        opacity=alt.value(0),
    )
    .add_params(nearest)
)

# Draw points on the line, and highlight based on selection
points = line.mark_point().encode(
    opacity=alt.condition(nearest, alt.value(1), alt.value(0))
)

# Draw a rule at the location of the selection
rules = (
    alt.Chart(combined_data)
    .mark_rule(color="gray")
    .encode(
        x=alt.X("yearmonthdatehoursminutes(Timestamp):T", title="Time"),
    )
    .transform_filter(nearest)
)

# Tooltip showing the temperature values for each measurement
tooltip = (
    alt.Chart(combined_data)
    .mark_text(align="left", dx=5, dy=-5)
    .encode(
        text=alt.condition(nearest, alt.Text("temp:Q", format=".2f"), alt.value(" ")),
        color=alt.Color("Measurements:N"),
    )
    .transform_filter(nearest)
)

# Combine all layers into one chart
data_layer = alt.layer(line, selectors, points, rules, tooltip).properties(
    width=800, height=400
)

st.altair_chart(data_layer, use_container_width=True)
