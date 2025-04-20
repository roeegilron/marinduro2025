import streamlit as st
import pandas as pd
import pdfplumber
import re

# Function to extract text from an uploaded PDF file
def extract_text_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text()
    return text

# Function to parse the extracted text
def parse_race_results(text):
    pattern = r"(\d+)\s+([\w\s]+)\s+\((\d+)\)\s+(\d+)\s+M\s+Time\s+(\d+:\d+)\s+(\d+:\d+)\s+(\d+:\d+)\s+(\d+:\d+)\s+(\d+:\d+)\s+(\d+:\d+)\s+(\d+:\d+\.\d+)"
    matches = re.findall(pattern, text)
    columns = ['Rank', 'Name', 'Bib', 'Age', 'Stage1', 'Stage2', 'Stage3', 'Stage4', 'Stage5', 'Stage6', 'Total']
    df = pd.DataFrame(matches, columns=columns)
    
    # Clean the 'Name' column
    df['Name'] = df['Name'].apply(lambda x: re.sub(r"mph\s*\d*\s*", "", x).strip())
    
    # Filter out any rows where 'Name' contains unwanted text
    df = df[df['Name'].apply(lambda x: not any(keyword in x for keyword in ['Stage', 'Total', 'Pro Men Open']))]
    
    return df

# Streamlit app
st.title("Race Results Comparison")

# File uploader
uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

if uploaded_file is not None:
    # Extract and parse the PDF
    text = extract_text_from_pdf(uploaded_file)
    df = parse_race_results(text)

    # Select primary user
    primary_user = st.selectbox("Select Primary User", df['Name'].unique())

    # Select other users to compare
    other_users = st.multiselect("Select Users to Compare", df['Name'].unique(), max_selections=10)

    # Toggle for time difference or percentage difference
    difference_type = st.radio("Difference Type", ('Time Difference', 'Percentage Difference'))

    # Display comparison
    if primary_user and other_users:
        primary_results = df[df['Name'] == primary_user]
        comparison_results = df[df['Name'].isin(other_users)]

        # Prepare data for display
        comparison_data = []

        # Add primary user data without color formatting
        primary_row_data = {'Name': primary_user}
        for col in ['Stage1', 'Stage2', 'Stage3', 'Stage4', 'Stage5', 'Stage6']:
            primary_time = primary_results[col].values[0]
            primary_row_data[col] = primary_time

        # Calculate overall time for primary user
        primary_total_seconds = sum(int(primary_results[col].values[0].split(':')[0]) * 60 + int(primary_results[col].values[0].split(':')[1]) for col in ['Stage1', 'Stage2', 'Stage3', 'Stage4', 'Stage5', 'Stage6'])
        primary_row_data['Overall Difference'] = "0.00%"  # No difference for the primary user

        comparison_data.append(primary_row_data)

        # Add comparison data for other users
        for _, row in comparison_results.iterrows():
            row_data = {'Name': row['Name']}
            total_time_diff = 0  # Initialize total time difference
            for col in ['Stage1', 'Stage2', 'Stage3', 'Stage4', 'Stage5', 'Stage6']:
                primary_time = primary_results[col].values[0]
                user_time = row[col]
                primary_seconds = int(primary_time.split(':')[0]) * 60 + int(primary_time.split(':')[1])
                user_seconds = int(user_time.split(':')[0]) * 60 + int(user_time.split(':')[1])
                time_diff = user_seconds - primary_seconds
                total_time_diff += time_diff  # Accumulate time difference

                if difference_type == 'Time Difference':
                    diff_display = f"{time_diff} sec"
                else:
                    percentage_diff = (time_diff / primary_seconds) * 100
                    diff_display = f"{percentage_diff:.2f}%"

                # Color coding
                if time_diff > 0:
                    row_data[col] = f"<span style='color:red'>{user_time} ({diff_display})</span>"
                else:
                    row_data[col] = f"<span style='color:green'>{user_time} ({diff_display})</span>"

            # Calculate overall difference
            if difference_type == 'Time Difference':
                overall_diff_display = f"{total_time_diff} sec"
            else:
                overall_percentage_diff = (total_time_diff / primary_total_seconds) * 100
                overall_diff_display = f"{overall_percentage_diff:.2f}%"

            # Color coding for overall difference
            if total_time_diff > 0:
                row_data['Overall Difference'] = f"<span style='color:red'>{overall_diff_display}</span>"
            else:
                row_data['Overall Difference'] = f"<span style='color:green'>{overall_diff_display}</span>"

            comparison_data.append(row_data)

        # Convert to DataFrame for display
        comparison_df = pd.DataFrame(comparison_data)

        # Display the table
        st.markdown(comparison_df.to_html(escape=False, index=False), unsafe_allow_html=True) 