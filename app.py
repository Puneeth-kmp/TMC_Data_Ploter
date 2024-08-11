import io
import re
from collections import defaultdict
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

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
                    # Convert value to float if possible
                    value = float(value.replace('A', '').replace('rpm', '').replace('deg', '').replace('Nm', ''))
                except ValueError:
                    pass  # Keep the original string if it's not a number
                data[current_id][key].append(value)

    except Exception as e:
        st.error(f"Error reading the file: {e}")
    return data

def plot_data(selected_id, selected_measurements, data):
    colors = px.colors.qualitative.Plotly  # Use Plotly's qualitative color set
    color_count = len(colors)

    for index, measurement in enumerate(selected_measurements):
        values = data[selected_id][measurement]
        if values:
            fig = go.Figure()

            # Determine if values are numeric or not
            is_numeric = all(isinstance(val, (int, float)) for val in values)

            if is_numeric:
                # Plot data with enhanced styling for numeric values
                fig.add_trace(go.Scatter(
                    x=list(range(len(values))), 
                    y=values, 
                    mode='lines+markers', 
                    name=measurement,
                    line=dict(width=2, color=colors[index % color_count]), 
                    marker=dict(size=8),
                    text=[f"{val:.2f}" for val in values], 
                    textposition='top center'
                ))
            else:
                # Plot data without formatting for non-numeric values
                fig.add_trace(go.Scatter(
                    x=list(range(len(values))), 
                    y=[0]*len(values), 
                    mode='markers', 
                    name=measurement,
                    marker=dict(size=8, color=colors[index % color_count]),
                    text=values, 
                    textposition='top center'
                ))

            fig.update_layout(
                title=f'{selected_id} - {measurement}',
                xaxis_title='Index',
                yaxis_title=measurement,
                template='plotly_dark',  # Use a dark theme for better aesthetics
                xaxis=dict(showline=True, showgrid=False),
                yaxis=dict(showline=True, showgrid=True),
                margin=dict(l=40, r=40, t=40, b=40),
                legend=dict(x=0, y=1, traceorder='normal', orientation='h'),
                width=1000  # Set the width of the plot
            )

            st.plotly_chart(fig, use_container_width=False, width=1000)

def main():
    st.title('Enhanced CAN Bus Data Plotter')

    # Upload the file
    uploaded_file = st.file_uploader("Upload a CAN bus data file", type="txt")

    if uploaded_file is not None:
        # Extract data from the file
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
