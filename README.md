# Race Results Comparison App

This Streamlit app allows users to compare race results from a PDF file. Users can select a primary participant and compare their performance against other participants across multiple stages. The app provides both time and percentage differences, with color-coded results for easy interpretation.

## Features

- **PDF Parsing:** Extracts race results from a PDF file.
- **Data Cleaning:** Cleans and structures the data for analysis.
- **User Selection:** Allows selection of a primary user and up to 10 other users for comparison.
- **Comparison Metrics:** Provides both time and percentage differences.
- **Color-Coded Results:** Highlights better and worse performances with green and red colors, respectively.
- **Overall Difference:** Displays an overall performance difference for each participant.

## How It Works

1. **PDF Extraction:** The app uses `pdfplumber` to extract text from a PDF file containing race results.
2. **Data Parsing:** A regular expression is used to parse the extracted text into a structured DataFrame.
3. **Data Cleaning:** The app cleans the participant names and filters out any unwanted text.
4. **User Interface:** Streamlit provides a user-friendly interface for selecting participants and viewing results.
5. **Comparison Display:** The app calculates and displays stage-by-stage and overall differences in a table format.

## How to Deploy

### Prerequisites

- Python 3.7 or higher
- Streamlit
- Pandas
- pdfplumber

### Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/race-results-comparison.git
   cd race-results-comparison
   ```

2. **Install Dependencies:**

   Use `pip` to install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

   Ensure your `requirements.txt` includes:
   ```
   streamlit
   pandas
   pdfplumber
   ```

3. **Run the App Locally:**

   Start the Streamlit app by running:

   ```bash
   streamlit run app.py
   ```

   Open your web browser and go to `http://localhost:8501` to view the app.

### Deployment

To deploy the app, you can use Streamlit Cloud or any other hosting service that supports Python web applications.

#### Deploying on Streamlit Cloud

1. **Create a Streamlit Cloud Account:**

   Sign up at [Streamlit Cloud](https://streamlit.io/cloud).

2. **Connect Your GitHub Repository:**

   Link your GitHub repository containing the app to Streamlit Cloud.

3. **Deploy the App:**

   Follow the instructions on Streamlit Cloud to deploy your app. You may need to specify the main file (`app.py`) and ensure all dependencies are listed in `requirements.txt`.

4. **Access Your App:**

   Once deployed, you will receive a URL to access your app online.

## Troubleshooting

- **PDF Parsing Issues:** Ensure the PDF file is formatted consistently with the expected structure.
- **Dependency Errors:** Verify that all required packages are installed and listed in `requirements.txt`.
- **App Crashes:** Check the terminal for error messages and debug accordingly.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License.
