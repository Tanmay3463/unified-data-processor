# 🌐 Unified Data Processor (WHO Athena & DHS Program APIs)

A simple Gradio web interface to fetch, clean, and export health indicators from the **WHO Athena API** and the **DHS Program API**. Designed for data science and public health analysis workflows.


## ✨ Features

- 🔄 **Dynamic Indicator Selection**: Dropdown updates based on selected API.
- 📥 **Live API Integration**:
  - WHO Athena API
  - DHS Program API
- 🧹 **Data Cleaning**:
  - Cleans noisy columns (like 'Value')
  - Merges lookup tables for Country and Indicator metadata
- 📊 **Exports Excel Files**:
  - Cleaned & structured `.xlsx` output for downstream analysis
- 🌍 **No hardcoded indicators** — reads from your uploaded master Excel files


## 📸 UI Preview

> This project uses [Gradio](https://www.gradio.app/) for an interactive browser UI

![Gradio Screenshot Placeholder](/ho2,png)


## 🔧 Requirements

Install required Python packages:

```bash
pip install -r requirements.txt
````

Required Python libraries:

* `gradio`
* `pandas`
* `requests`
* `openpyxl`


## 📁 File Structure

```
unified-data-processor/
├── app.py                   # Main application script
├── requirements.txt         # Python package dependencies
├── README.md                # This file
└── /content/                # Place your input Excel files here
```


## 📂 Input Files Required (Not Included)

> ⚠️ **The required Excel files are NOT included in this repository** due to size or privacy reasons.

Before running the app, **upload the following files manually into the `/content/` directory** (especially if using Google Colab):

| File Name | Description |
|-----------|-------------|
| `master_query.xlsx` | DHS indicator list (must contain `indicatorIds` column) |
| `master_query2.xlsx` | WHO Athena indicator list (must contain `indicatorIds` column) |
| `GHO-Indicator-list.xlsx` | WHO indicator lookup table (maps `GHO` → `IndicatorCode`) |
| `GHO-CountryName-ISO-Matching_16April25.xlsx` | Country name to ISO code mapping |

If you don't have these files, create your own versions with similar structure or contact the developer.



## 🚀 Run the App (Colab or Local)

From command line:

```bash
python app.py
```

Or inside a Colab notebook:

```python
!python app.py
```

The app will launch and provide a public link (via Gradio `share=True`).


## 📌 Notes

* Output files are saved as `.xlsx` in `/content/WHO_Athena/` or `/content/DHS_Program/`
* Consider renaming downloaded files to avoid overwriting
* Make sure input Excel files are well-formed (column names must match)


## 👨‍💻 Developed By

**Tanmay Jain**
B.Tech Computer Science (Data Science & Analytics)
[LinkedIn](https://www.linkedin.com/in/tanmay-jain-396230250/) • [GitHub](https://github.com/Tanmay3463)
