import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from collections import defaultdict
import io
import re

# Function to extract data from the uploaded file
def extract_data(file):
    data = defaultdict(lambda: defaultdict(list))
    try:
        buffer = io.StringIO(file.read().decode('utf-8'))
        lines = buffer.readlines()

        can_id_pattern = re.compile(r'ID:\s*(0x[0-9A-Fa-f]+)')
        data_bytes_pattern = re.compile(r'Data Bytes:\s*(.*)')
        measurement_pattern = re.compile(r'(\w+):\s*(.*)')

        current_id = None
        for line in lines:
            id_match = can_id_pattern.search(line)
            if id_match:
                current_id = id_match.group(1)
                continue

            bytes_match = data_bytes_pattern.search(line)
            if bytes_match and current_id:
                data_bytes = bytes_match.group(1)
                values = [int(b, 16) for b in data_bytes.split()]
                data[current_id]['Data Bytes'].append(values)
                continue

            measurement_match = measurement_pattern.search(line)
            if measurement_match and current_id:
                key, value = measurement_match.groups()
                try:
                    value = float(value.replace('A', '').replace('rpm', '').replace('deg', '').replace('Nm', ''))
                except ValueError:
                    pass
                data[current_id][key].append(value)

    except Exception as e:
        st.error(f"Error reading the file: {e}")
    return data

# Function to plot data using Altair
def plot_data(selected_id, selected_measurements, data):
    if not selected_measurements:
        st.write("No measurements selected for plotting.")
        return

    # Define a list of colors for different plots
    color_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
    color_map = {measurement: color_palette[i % len(color_palette)] for i, measurement in enumerate(selected_measurements)}

    charts = []
    for measurement in selected_measurements:
        values = data[selected_id][measurement]
        if values:
            df = pd.DataFrame({
                'Index': list(range(len(values))),
                'Value': values,
                'color': [color_map[measurement]] * len(values)  # Use measurement name for color
            })
            
            # Create a line chart for each measurement
            chart = alt.Chart(df).mark_line(point=True).encode(
                x='Index:O',
                y='Value:Q',
                color=alt.Color('color:N', scale=alt.Scale(domain=list(color_map.values()), range=list(color_map.values()))),
                tooltip=['Index', 'Value']
            ).properties(
                title=f"Plot for {measurement}",
                width=700,
                height=400
            ).interactive()

            charts.append(chart)

    # Display all charts in a vertical layout
    st.altair_chart(alt.vconcat(*charts), use_container_width=True)

# Main function to handle the Streamlit app logic
def main():
    st.set_page_config(layout="centered", page_icon="📈", page_title="CAN Bus Data Plotter")
    st.title("CAN Bus Data Plotter")

    uploaded_file = st.file_uploader("Upload a CAN bus data file", type="txt")

    if uploaded_file is not None:
        data = extract_data(uploaded_file)

        if data:
            unique_ids = list(data.keys())
            st.write("Unique CAN IDs:")
            st.write(sorted(unique_ids))

            selected_id = st.selectbox("Select CAN ID to plot", unique_ids)
            if selected_id:
                measurements = data[selected_id]
                measurement_names = [key for key in measurements.keys() if key != 'Data Bytes']
                
                st.write("Select measurements to plot:")
                selected_measurements = [key for key in measurement_names if st.checkbox(key, key=key)]

                if selected_measurements:
                    plot_data(selected_id, selected_measurements, data)
                else:
                    st.write("Select measurements to plot.")
        else:
            st.write("No data found or file is empty.")

if __name__ == "__main__":
    main()
