# National Surgical Volumes Dashboard (Uganda, 2020–2024)

This Streamlit Cloud web app provides interactive analytics and visualizations for surgical capacity and operative volumes in Uganda, based on data from the Ministry of Health (2020–2024).

## Features

* **Annual and regional surgical volumes and rates**
* **Procedure category distributions**
* **Facility distribution by level and ownership**
* **Interactive district/region heatmaps**
* **Observed and forecasted trends (2020–2030, Holt-Winters)**
* **Export results to CSV, PDF, PNG, TIFF**
* **Raw data explorer**

## Project Structure

```
<repo-root>/
├── main.py
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── data_loading.py
│   ├── data_processing.py
│   ├── export_helpers.py
│   └── forecasting.py
├── data/
│   └── raw/
│       ├── Uganda Surgical Procedures_raw data_2020.csv
│       ├── ...
│       ├── Uganda Population Data 2024/
│       │   ├── Population by district_census 2024.xlsx
│       ├── Uganda_Shape_files_2020/
│       │   ├── GEO MFL SURVEY DATASET.xlsx
│       │   └── Region/
│       │       └── UDHS_Regions_2019.shp
└── README.md
```

## Setup & Usage

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add your data

* Place your CSV, Excel, and shapefiles in `data/raw/` as above

### 4. Launch the app

```bash
streamlit run main.py
```

### 5. Use with Streamlit Cloud or GitHub Codespaces

* Just push your code and data; deploy from the browser!

---

## Data Sources

* Uganda Ministry of Health (HMIS)
* Uganda Population Census (2024)
* Facility and shapefile data for mapping

## Acknowledgements

* Authors: Ministry of Health Uganda, QMUL, Busitema University, and collaborators
* App design and analytics: \[Raymond Reuel Wayesu]

---

For questions, issues, or suggestions, open an Issue or contact the repository maintainer.
