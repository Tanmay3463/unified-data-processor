# --- Configuration for Backend Excel Files ---
# IMPORTANT: Place your Excel files containing 'indicatorIds' column at these paths.
MASTER_ATHENA_INDICATORS_PATH = "/content/master_query2.xlsx"
MASTER_DHS_INDICATORS_PATH = "/content/master_query.xlsx"

# --- Function to load indicators from a specific Excel file ---
def load_indicators_from_file(file_path, column_name='indicatorIds'):
    if not os.path.exists(file_path):
        print(f"Warning: Indicator file not found at {file_path}")
        return []
    try:
        df = pd.read_excel(file_path)
        if column_name not in df.columns:
            print(f"Warning: '{file_path}' must contain an '{column_name}' column.")
            return []
        # Convert to string to avoid issues with mixed types, then get unique, then sort
        return sorted(df[column_name].astype(str).unique().tolist())
    except Exception as e:
        print(f"An error occurred while loading indicators from {file_path}: {e}")
        return []

# Load all potential indicators for both APIs globally when the script starts
ALL_ATHENA_INDICATORS = load_indicators_from_file(MASTER_ATHENA_INDICATORS_PATH)
ALL_DHS_INDICATORS = load_indicators_from_file(MASTER_DHS_INDICATORS_PATH)

if not ALL_ATHENA_INDICATORS:
    print("Warning: No Athena indicators loaded. Please check athena_indicators.xlsx.")
if not ALL_DHS_INDICATORS:
    print("Warning: No DHS indicators loaded. Please check dhs_indicators.xlsx.")

# --- API Processing Functions (Modified to accept selected_indicator_ids) ---

def process_athena_data(selected_indicator_ids, progress=gr.Progress()):
    if not selected_indicator_ids:
        return None, "Error: No Athena indicators selected. Please choose at least one indicator."

    # Combine selected indicator IDs into a single string
    all_indicator_ids = ",".join(selected_indicator_ids)

    try:
        # WHO Athena API base URL
        api_url = "http://apps.who.int/gho/athena/api/GHO"

        # Parameters for the API request
        params = {
            "format": "json",
            "profile": "simple",  # For human-readable values
        }

        # Build the complete API URL with all indicator IDs
        request_url = f"{api_url}/{all_indicator_ids}"

        # Generate filename based on the current date
        current_date = datetime.now().strftime("%Y-%m-%d")
        workbook_name = f"WHO_Athena_Combined_{current_date}.xlsx"

        progress(0.1, desc="Fetching data from WHO Athena API...")
        # Make the API request
        response = requests.get(request_url, params=params)

        if response.status_code == 200:
            data = response.json()

            # Extract data from 'fact'
            if 'fact' in data:
                df = pd.json_normalize(data['fact'])

                # Clean the column names
                df.columns = [col.replace('dim.', '') for col in df.columns]

                # Output file path
                output_dir = "/content/WHO_Athena"
                os.makedirs(output_dir, exist_ok=True)
                output_file_combined = os.path.join(output_dir, workbook_name)

                progress(0.3, desc="Saving initial combined data...")
                # Save the combined data to a new Excel file
                with pd.ExcelWriter(output_file_combined, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='CombinedData')

                # Code to clean Value column of the file generated
                input_file_clean = output_file_combined
                output_file_cleaned = f"/content/WHO_Athena/WHO_Athena_Combined_{current_date}_Cleaned.xlsx"

                progress(0.5, desc="Cleaning 'Value' column...")
                # Load the Excel file for cleaning
                df_clean = pd.read_excel(input_file_clean)

                # Check if 'Value' column exists
                if 'Value' in df_clean.columns:
                    # Remove brackets and contents from 'Value' column
                    df_clean['Value'] = df_clean['Value'].astype(str).str.replace(r"\s*\[.*\]", "", regex=True).str.strip()
                else:
                    print("Warning: No 'Value' column found in the Excel file for cleaning.")

                # Save cleaned DataFrame back to Excel
                df_clean.to_excel(output_file_cleaned, index=False)

                # Add country id and indicator id
                main_file = output_file_cleaned
                df_main = pd.read_excel(main_file)

                # 2. Load your lookup files (assuming they exist in /content/)
                lookup_file_country = "/content/GHO-CountryName-ISO-Matching_16April25.xlsx"
                lookup_file_indicator = "/content/GHO-Indicator-list.xlsx"

                progress(0.7, desc="Merging with lookup data...")
                # Check if lookup files exist
                if not os.path.exists(lookup_file_country):
                    return None, f"Error: Country lookup file not found at {lookup_file_country}. Please upload it to /content/."
                if not os.path.exists(lookup_file_indicator):
                    return None, f"Error: Indicator lookup file not found at {lookup_file_indicator}. Please upload it to /content/."

                df_lookup_country = pd.read_excel(lookup_file_country)
                df_lookup_indicator = pd.read_excel(lookup_file_indicator)

                # 3. Merge ISO_Code from country lookup
                df_merged = pd.merge(
                    df_main,
                    df_lookup_country[['COUNTRY', 'ISO_Code']],
                    on='COUNTRY',
                    how='left'
                )

                # 4. Merge IndicatorCode from indicator lookup into the same DataFrame
                df_merged = pd.merge(
                    df_merged,
                    df_lookup_indicator[['GHO', 'IndicatorCode']],
                    on='GHO',
                    how='left'
                )

                # 5. Reorder columns to put ISO_Code just after COUNTRY
                cols = list(df_merged.columns)
                if 'COUNTRY' in cols and 'ISO_Code' in cols:
                    country_idx = cols.index('COUNTRY')
                    if 'ISO_Code' in cols: cols.remove('ISO_Code') # Remove if already exists at wrong place
                    cols.insert(country_idx + 1, 'ISO_Code')

                # Put IndicatorCode just after GHO
                if 'GHO' in cols and 'IndicatorCode' in cols:
                    gho_idx = cols.index('GHO')
                    if 'IndicatorCode' in cols: cols.remove('IndicatorCode') # Remove if already exists at wrong place
                    cols.insert(gho_idx + 1, 'IndicatorCode')

                df_merged = df_merged[cols]

                # 6. Save the final merged DataFrame
                output_file_final = f"/content/WHO_Athena/GHO_Athena_Cleaned_{current_date}.xlsx"
                df_merged.to_excel(output_file_final, index=False)

                progress(1.0, desc="Processing complete!")
                # Return the file path for download and a success message
                return output_file_final, f"Processing complete. Final data saved to: {output_file_final}"

            else:
                return None, "Error: No 'fact' data found in the API response for selected indicators. Check if indicators are valid or data exists."
        else:
            return None, f"Error: API request failed with status code {response.status_code}
Response: {response.text}"

    except Exception as e:
        return None, f"An unexpected error occurred: {e}"


def process_dhs_data(selected_indicator_ids, progress=gr.Progress()):
    if not selected_indicator_ids:
        return None, "Error: No DHS indicators selected. Please choose at least one indicator."

    # Combine selected indicator IDs into a comma-separated string
    all_indicator_ids = ",".join(selected_indicator_ids)

    try:
        # DHS Program API base URL
        api_url = "http://api.dhsprogram.com/rest/dhs/data"

        # Parameters for the API request
        params = {
            "indicatorIds": all_indicator_ids,
            "format": "json"
        }

        # Generate filename based on the current date
        current_date = datetime.now().strftime("%Y-%m-%d")
        workbook_name = f"DHS_Program_Combined_{current_date}.xlsx"

        progress(0.1, desc="Fetching data from DHS Program API...")
        # Make the API request
        response = requests.get(api_url, params=params)

        if response.status_code == 200:
            data = response.json()

            # Extract data from the 'Data' field
            if 'Data' in data and data['Data']:
                df = pd.DataFrame(data['Data'])

                # Output file path
                output_dir = "/content/DHS_Program"
                os.makedirs(output_dir, exist_ok=True)
                output_file_combined = os.path.join(output_dir, workbook_name)

                progress(0.7, desc="Saving combined data...")
                # Save the combined data to a new Excel file
                with pd.ExcelWriter(output_file_combined, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='CombinedData')

                progress(1.0, desc="Processing complete!")
                # Return the file path for download and a success message
                return output_file_combined, f"Processing complete. Final data saved to: {output_file_combined}"

            elif 'Data' in data and not data['Data']:
                return None, "Warning: API response contains no data for the provided indicator IDs."
            else:
                return None, "Error: No 'Data' field found in the API response or the field is empty. Check if indicators are valid or data exists."
        else:
            return None, f"Error: API request failed with status code {response.status_code}
Response: {response.text}"

    except Exception as e:
        return None, f"An unexpected error occurred: {e}"


def unified_data_processor(api_choice, selected_indicator_ids, progress=gr.Progress()):
    if api_choice == "WHO Athena":
        return process_athena_data(selected_indicator_ids, progress)
    elif api_choice == "DHS Program":
        return process_dhs_data(selected_indicator_ids, progress)
    else:
        return None, "Invalid API selection."


# --- Gradio Blocks Interface ---
# Function to dynamically update the indicator dropdown choices
def update_indicator_dropdown(api_choice):
    if api_choice == "WHO Athena":
        # Reset value to empty list when changing API type
        return gr.Dropdown(choices=ALL_ATHENA_INDICATORS, value=[], interactive=True)
    elif api_choice == "DHS Program":
        # Reset value to empty list when changing API type
        return gr.Dropdown(choices=ALL_DHS_INDICATORS, value=[], interactive=True)
    return gr.Dropdown(choices=[], value=[], interactive=False) # Should not be reached


with gr.Blocks(title="Unified Data Processor (Dynamic Indicators)") as demo:
    gr.Markdown("# Unified Data Processor (WHO Athena & DHS Program)")
    gr.Markdown("Select an API, and the indicator list will dynamically update. Then choose indicators to fetch and process.")
    gr.Markdown("Rename the file after downloading to avoid confusion.")

    with gr.Row():
        api_dropdown = gr.Dropdown(
            choices=["WHO Athena", "DHS Program"],
            label="Select API",
            value="WHO Athena",
            scale=1
        )
        indicator_dropdown = gr.Dropdown(
            choices=ALL_ATHENA_INDICATORS,
            multiselect=True,
            label="Select Indicators",
            info="Select one or more indicator IDs from the backend master list. This list changes based on API selection.",
            scale=2
        )
    process_button = gr.Button("Process Data", variant="primary")

    # Outputs
    with gr.Column():
        download_file = gr.File(label="Download Generated Excel File", interactive=False)
        status_textbox = gr.Textbox(label="Processing Status", interactive=False)

    # Event listener: When API dropdown changes, update indicator dropdown
    api_dropdown.change(
        fn=update_indicator_dropdown,
        inputs=api_dropdown,
        outputs=indicator_dropdown,
        queue=False
    )
    # Event listener: When Process Data button is clicked
    process_button.click(
        fn=unified_data_processor,
        inputs=[api_dropdown, indicator_dropdown],
        outputs=[download_file, status_textbox]
    )
# Launch the interface
demo.launch(debug=True, share=True)