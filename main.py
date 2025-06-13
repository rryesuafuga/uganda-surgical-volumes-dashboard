# main.py (Updated with proper data processing from Colab analysis)
import streamlit as st
import os
import pandas as pd
import plotly.express as px
import geopandas as gpd
import traceback

from src.data_loading import load_surgical_data, load_population_data, load_facility_metadata, load_shapefile, YEARS
from src.data_processing import filter_by_region, annual_volume_table, procedure_categories_table, facility_distribution_table, district_heatmap_data, trends_timeseries_data
from src.export_helpers import dataframe_to_pdf, plotly_export, safe_download_button
from src.forecasting import forecast_procedure_rate

# Configure page
st.set_page_config(
    page_title="Uganda National Surgical Volumes Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏥 Uganda National Surgical Volumes Dashboard")

# --- SIDEBAR FILTERS ---
st.sidebar.title('Filters')
year_selected = st.sidebar.selectbox('Year', YEARS, index=YEARS.index(2024))
region_selected = st.sidebar.selectbox('Region', ['All', 'Central', 'East', 'North', 'West'])

# Add debug info in sidebar
with st.sidebar.expander("Debug Info", expanded=False):
    st.write("**Selected Year:**", year_selected)
    st.write("**Selected Region:**", region_selected)

# Add data loading debug button
st.sidebar.markdown("---")
st.sidebar.subheader("🔧 Debug Tools")

# Debug Data Loading
if st.sidebar.button("🔍 Debug Data Loading", help="Check data file availability and structure"):
    from src.data_loading import test_data_loading
    
    with st.spinner("Running data loading diagnostics..."):
        debug_results = test_data_loading()
    
    st.sidebar.success("Debug complete! Check main area for results.")
    
    # Show debug results in main area
    st.header("🔧 Data Loading Debug Results")
    
    # Create tabs for different debug info
    debug_tab1, debug_tab2, debug_tab3, debug_tab4 = st.tabs([
        "Directory Structure", 
        "File Validation", 
        "Load Test Results", 
        "Raw Debug Data"
    ])
    
    with debug_tab1:
        st.subheader("Directory Structure")
        dir_info = debug_results['directory_info']
        
        st.write(f"**Data Directory Exists:** {dir_info['data_dir_exists']}")
        st.write(f"**Data Directory Path:** `{dir_info['data_dir_path']}`")
        
        if dir_info['data_dir_exists']:
            st.write("**Directory Structure:**")
            for folder, contents in dir_info['directory_structure'].items():
                with st.expander(f"📁 {folder}"):
                    if contents['directories']:
                        st.write("**Subdirectories:**", contents['directories'])
                    if contents['files']:
                        st.write("**Files:**", contents['files'])
                    else:
                        st.write("*No files found*")
            
            st.write("**Files by Type:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("**CSV Files:**")
                for f in dir_info['files_found']['csv_files']:
                    st.write(f"- {f}")
            with col2:
                st.write("**Excel Files:**")
                for f in dir_info['files_found']['xlsx_files']:
                    st.write(f"- {f}")
            with col3:
                st.write("**Shapefiles:**")
                for f in dir_info['files_found']['shp_files']:
                    st.write(f"- {f}")
        else:
            st.error("Data directory not found! Please check your file structure.")
    
    with debug_tab2:
        st.subheader("File Validation Results")
        validation = debug_results['validation']
        
        # Surgical data validation
        st.write("**Surgical Data Files:**")
        surgical_data = validation['surgical_data']
        for year, info in surgical_data.items():
            if info['available']:
                st.success(f"✅ {year}: Found at `{info['path']}`")
            else:
                st.error(f"❌ {year}: {info['error']}")
        
        # Other data validation
        st.write("**Other Data Files:**")
        other_data = {
            'Population Data': validation['population_data'],
            'Facility Data': validation['facility_data'], 
            'Shapefile Data': validation['shapefile_data']
        }
        
        for data_type, info in other_data.items():
            if info['available']:
                st.success(f"✅ {data_type}: Found at `{info['path']}`")
            else:
                st.error(f"❌ {data_type}: {info['error']}")
    
    with debug_tab3:
        st.subheader("Load Test Results")
        load_tests = debug_results['load_tests']
        
        # Surgical data tests
        st.write("**Surgical Data Loading:**")
        for year in YEARS:
            test_key = f'surgical_{year}'
            if test_key in load_tests:
                test = load_tests[test_key]
                if test['success']:
                    st.success(f"✅ {year}: Loaded successfully")
                    st.write(f"  - Shape: {test['shape']}")
                    st.write(f"  - Procedure columns: {test['procedure_columns']}")
                    st.write(f"  - Sample columns: {test['columns']}")
                else:
                    st.error(f"❌ {year}: {test['error']}")
        
        # Other data tests
        st.write("**Other Data Loading:**")
        other_tests = ['population', 'facility', 'shapefile']
        for test_type in other_tests:
            if test_type in load_tests:
                test = load_tests[test_type]
                if test['success']:
                    st.success(f"✅ {test_type.title()}: Loaded successfully")
                    st.write(f"  - Shape: {test['shape']}")
                    st.write(f"  - Columns: {test['columns']}")
                    if 'crs' in test:
                        st.write(f"  - CRS: {test['crs']}")
                else:
                    st.error(f"❌ {test_type.title()}: {test['error']}")
    
    with debug_tab4:
        st.subheader("Raw Debug Data")
        st.json(debug_results)

# Quick validation display
if st.sidebar.button("📋 Quick Validation", help="Quick check of data availability"):
    from src.data_loading import validate_data_files
    validation = validate_data_files()
    
    st.sidebar.write("**Quick Status:**")
    
    # Count available years
    available_years = sum(1 for year_info in validation['surgical_data'].values() if year_info['available'])
    st.sidebar.write(f"Surgical data: {available_years}/{len(YEARS)} years")
    
    # Other data status
    other_status = [
        ("Population", validation['population_data']['available']),
        ("Facility", validation['facility_data']['available']),
        ("Shapefile", validation['shapefile_data']['available'])
    ]
    
    for name, available in other_status:
        status = "✅" if available else "❌"
        st.sidebar.write(f"{name}: {status}")

# File structure help
with st.sidebar.expander("📁 Expected File Structure", expanded=False):
    st.write("""
    **Expected directory structure:**
    ```
    data/raw/
    ├── Uganda Surgical Procedures_raw data_2020.csv
    ├── Uganda Surgical Procedures_raw data_2021.csv
    ├── Uganda Surgical Procedures_raw data_2022.csv
    ├── Uganda Surgical Procedures_raw data_2023.csv
    ├── Uganda Surgical Procedures_raw data_2024.csv
    ├── Uganda Population Data 2024/
    │   └── Population_census 2024.xlsx
    └── Uganda_Shape_files_2020/
        ├── GEO MFL SURVEY DATASET.xlsx
        └── Region/
            └── UDHS_Regions_2019.shp
    ```
    """)

# --- LOAD DATA WITH ERROR HANDLING ---
@st.cache_data
def load_and_process_data(year_selected, region_selected):
    try:
        # Load surgical data
        df = load_surgical_data(year_selected)
        st.sidebar.success(f"✅ Loaded surgical data for {year_selected}")
        
        # Load population data
        pop = load_population_data()
        st.sidebar.success("✅ Loaded population data")
        
        # Load facility data
        try:
            fac = load_facility_metadata()
            st.sidebar.success("✅ Loaded facility metadata")
        except Exception as e:
            st.sidebar.warning(f"⚠️ Facility data: {str(e)}")
            fac = pd.DataFrame()  # Empty dataframe as fallback
        
        # Load shapefile
        try:
            gdf = load_shapefile()
            st.sidebar.success("✅ Loaded shapefile")
        except Exception as e:
            st.sidebar.warning(f"⚠️ Shapefile: {str(e)}")
            gdf = None
        
        # Filter by region
        df_filtered = filter_by_region(df, region_selected)
        
        return df, df_filtered, pop, fac, gdf
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.error("**Full error details:**")
        st.code(traceback.format_exc())
        
        # Show file structure help
        st.error("**Troubleshooting Steps:**")
        st.write("1. Check that your `data/raw/` directory exists")
        st.write("2. Verify file names match the expected patterns")
        st.write("3. Use the 'Debug Data Loading' button in the sidebar")
        st.write("4. Check the 'Expected File Structure' in the sidebar")
        
        return None, None, None, None, None

# Load data
data_loading_failed = False
try:
    df, df_filtered, pop, fac, gdf = load_and_process_data(year_selected, region_selected)
    if df is None:
        data_loading_failed = True
except Exception as e:
    st.error(f"Critical error in data loading: {str(e)}")
    data_loading_failed = True
    df, df_filtered, pop, fac, gdf = None, None, None, None, None

# Check if data loaded successfully
if data_loading_failed or df is None:
    st.error("⚠️ **Data Loading Failed**")
    st.write("The dashboard cannot display data because the required files are not accessible.")
    st.write("**Please use the debug tools in the sidebar to diagnose the issue:**")
    st.write("- Click '🔍 Debug Data Loading' for detailed diagnostics")
    st.write("- Click '📋 Quick Validation' for a quick status check")
    st.write("- Check '📁 Expected File Structure' for required file layout")
    
    # Show basic file structure check
    if os.path.exists('data'):
        st.write("**Found 'data' directory. Contents:**")
        for root, dirs, files in os.walk('data'):
            level = root.replace('data', '').count(os.sep)
            indent = ' ' * 2 * level
            st.write(f"{indent}📁 {os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                st.write(f"{subindent}📄 {file}")
    else:
        st.error("❌ 'data' directory not found in the application root")
    
    st.stop()

# --- DATA STRUCTURE DEBUG PANEL ---
with st.expander("🔍 Data Structure Debug Panel", expanded=False):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Surgical Data Structure")
        st.write(f"**Shape:** {df.shape}")
        st.write(f"**Columns ({len(df.columns)}):**")
        for i, col in enumerate(df.columns[:20]):  # Show first 20 columns
            st.write(f"{i+1}. {col}")
        if len(df.columns) > 20:
            st.write(f"... and {len(df.columns) - 20} more columns")
        
        # Check for procedure columns
        procedure_cols = [col for col in df.columns if col.startswith('108-')]
        st.write(f"**Procedure columns found:** {len(procedure_cols)}")
        if procedure_cols:
            st.write("Sample procedure columns:")
            for col in procedure_cols[:5]:
                st.write(f"  - {col}")
    
    with col2:
        st.subheader("Population Data Structure")
        st.write(f"**Shape:** {pop.shape}")
        st.write("**Columns:**", list(pop.columns))
        st.write("**Sample data:**")
        st.dataframe(pop.head(3))

# --- TABS ---
tabs = st.tabs([
    'National Dashboard',
    'Annual Volumes & Rates',
    'Procedure Categories',
    'Facility Distribution',
    'Geographic Heatmap',
    'Trends/Time Series',
    'Raw Data Tables',
    'About'
])

# === 1. National Dashboard (KPIs) ===
with tabs[0]:
    st.header(f"Uganda National Surgical Volumes Dashboard: {year_selected}")
    
    # Display region filter info
    if region_selected != 'All':
        st.info(f"📍 Showing data for: **{region_selected}** region")
    
    # Create metrics columns
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        # Calculate total procedures
        if 'Surgical Procedures' in df_filtered.columns:
            total_procedures = int(df_filtered['Surgical Procedures'].sum())
        else:
            total_procedures = 0
            st.warning("No 'Surgical Procedures' column found after processing")
        
        # Calculate reporting facilities
        facility_col = 'Facility Code' if 'Facility Code' in df_filtered.columns else df_filtered.columns[0]
        total_facilities = int(df_filtered[facility_col].nunique())
        
        # Calculate population and rate
        pop_col = 'Population' if 'Population' in pop.columns else 'Total'
        if pop_col in pop.columns:
            total_pop = int(pop[pop_col].sum())
            if total_pop > 0:
                proc_rate = (total_procedures / total_pop) * 100_000
            else:
                proc_rate = 0
        else:
            total_pop = 0
            proc_rate = 0
        
        # Display metrics
        with col1:
            st.metric('Total Procedures', f"{total_procedures:,}")
        
        with col2:
            st.metric('Reporting Facilities', f"{total_facilities:,}")
        
        with col3:
            st.metric('Total Population', f"{total_pop:,}")
        
        with col4:
            st.metric('Procedures per 100,000', f"{proc_rate:,.1f}")
        
        # Additional insights
        if total_procedures > 0:
            st.success(f"✅ Successfully processed {total_procedures:,} surgical procedures from {total_facilities} facilities")
        else:
            st.error("❌ No surgical procedures found. Please check data processing.")
            
            # Show what columns were found
            st.write("**Available columns in filtered data:**")
            st.write(list(df_filtered.columns))
            
            # Show sample data
            st.write("**Sample of raw data:**")
            st.dataframe(df_filtered.head())
    
    except Exception as e:
        st.error(f"Error calculating metrics: {str(e)}")
        st.code(traceback.format_exc())

# === 2. Annual Volumes & Rates Table ===
with tabs[1]:
    st.header('Annual Surgical Volumes & Rates')
    
    try:
        agg = annual_volume_table(df_filtered, pop)
        
        if agg is not None and len(agg) > 0:
            st.dataframe(agg, use_container_width=True)
            
            # Export options
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    'Download Table (CSV)', 
                    agg.to_csv(index=False), 
                    file_name='annual_volumes_rates.csv',
                    mime='text/csv'
                )
            
            with col2:
                try:
                    pdf_file = dataframe_to_pdf(agg, "Annual Surgical Volumes & Rates")
                    with open(pdf_file, "rb") as f:
                        st.download_button(
                            "Download Table as PDF", 
                            f, 
                            file_name="annual_volumes_rates.pdf", 
                            mime="application/pdf"
                        )
                except Exception as e:
                    st.warning(f"PDF export not available: {str(e)}")
        else:
            st.warning("No data available for annual volumes table")
            
    except Exception as e:
        st.error(f"Error creating annual volumes table: {str(e)}")
        st.code(traceback.format_exc())

# === 3. Procedure Categories Table ===
with tabs[2]:
    st.header('Surgical Procedures by Category (2024)')
    
    try:
        cat_counts = procedure_categories_table(df_filtered)
        
        if cat_counts is not None and len(cat_counts) > 0:
            # Create chart
            fig = px.bar(
                cat_counts, 
                x='Category', 
                y='Surgical Procedures',
                title=f'Surgical Procedures by Category ({year_selected})'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Show table
            st.dataframe(cat_counts, use_container_width=True)
            
            # Export options
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    'Download Table (CSV)', 
                    cat_counts.to_csv(index=False), 
                    file_name='category_counts.csv',
                    mime='text/csv'
                )
            
            with col2:
                try:
                    pdf_file = dataframe_to_pdf(cat_counts, "Surgical Procedures by Category")
                    with open(pdf_file, "rb") as f:
                        st.download_button(
                            "Download Table as PDF", 
                            f, 
                            file_name="procedure_categories.pdf", 
                            mime="application/pdf"
                        )
                except Exception as e:
                    st.warning(f"PDF export not available: {str(e)}")
        else:
            st.warning("No category data available. Categories may need to be derived from procedure codes.")
            
    except Exception as e:
        st.error(f"Error creating procedure categories table: {str(e)}")
        st.code(traceback.format_exc())

# === 4. Facility Distribution Table ===
with tabs[3]:
    st.header('Facility Distribution')
    
    try:
        fac_table = facility_distribution_table(fac)
        
        if fac_table is not None and len(fac_table) > 0:
            st.dataframe(fac_table, use_container_width=True)
            
            # Export options
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    'Download Table (CSV)', 
                    fac_table.to_csv(), 
                    file_name='facility_distribution.csv',
                    mime='text/csv'
                )
            
            with col2:
                try:
                    pdf_file = dataframe_to_pdf(fac_table.reset_index(), "Facility Distribution")
                    with open(pdf_file, "rb") as f:
                        st.download_button(
                            "Download Table as PDF", 
                            f, 
                            file_name="facility_distribution.pdf", 
                            mime="application/pdf"
                        )
                except Exception as e:
                    st.warning(f"PDF export not available: {str(e)}")
        else:
            st.warning("No facility distribution data available")
            if len(fac) > 0:
                st.write("Available facility data columns:", list(fac.columns))
                st.dataframe(fac.head())
            
    except Exception as e:
        st.error(f"Error creating facility distribution table: {str(e)}")
        st.code(traceback.format_exc())

# === 5. Geographic Heatmap ===
with tabs[4]:
    st.header('Surgical Procedure Rate Heatmap (District)')
    
    try:
        map_df = district_heatmap_data(df_filtered, pop)
        
        if map_df is not None and gdf is not None:
            # Try to merge with shapefile
            if 'District' in gdf.columns:
                gdf_merged = gdf.merge(map_df, left_on='District', right_on='District', how='left')
                
                if 'Proc Rate/100k' in gdf_merged.columns:
                    fig = px.choropleth(
                        gdf_merged,
                        geojson=gdf_merged.geometry,
                        locations=gdf_merged.index,
                        color='Proc Rate/100k',
                        hover_name='District',
                        title=f'Surgical Procedures per 100,000 Population ({year_selected})',
                        color_continuous_scale='viridis'
                    )
                    fig.update_geos(fitbounds="locations", visible=False)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show data table
                    st.subheader("District Data")
                    st.dataframe(map_df, use_container_width=True)
                    
                    # Export options
                    buf_png = plotly_export(fig, 'png')
                    buf_tiff = plotly_export(fig, 'tiff')
                    safe_download_button('Download Map (PNG)', buf_png, 'district_heatmap.png', 'image/png', key='map_png')
                    safe_download_button('Download Map (TIFF)', buf_tiff, 'district_heatmap.tiff', 'image/tiff', key='map_tiff')
                else:
                    st.warning("Could not calculate procedure rates. Check population data.")
            else:
                st.warning("District column not found in shapefile")
        else:
            st.warning("Geographic data not available. Check district columns and shapefile.")
            if map_df is not None:
                st.write("Available district data:")
                st.dataframe(map_df.head())
                
    except Exception as e:
        st.error(f"Error creating geographic heatmap: {str(e)}")
        st.code(traceback.format_exc())

# === 6. Trends: Time Series Plots (with Forecast) ===
with tabs[5]:
    st.header('Trends: Procedures per 100,000 by Year and Forecast (2025–2030)')
    
    try:
        ts_data = trends_timeseries_data(YEARS, load_surgical_data, pop)
        ts = pd.DataFrame(ts_data)
        
        if len(ts) > 0 and ts['Procedures'].sum() > 0:
            # Create time series chart
            fig = px.line(
                ts, 
                x='Year', 
                y='Rate per 100k', 
                title='Procedures per 100,000 Population by Year', 
                markers=True
            )
            
            # Add forecast
            try:
                forecast_df = forecast_procedure_rate(ts, steps=6)  # 2025–2030
                ts_all = pd.concat([ts, forecast_df], ignore_index=True)
                
                fig.add_scatter(
                    x=forecast_df['Year'], 
                    y=forecast_df['Rate per 100k'],
                    mode='lines+markers', 
                    name='Forecast', 
                    line=dict(dash='dash', color='red')
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show combined table
                st.subheader('Observed and Forecasted Rates (2020–2030)')
                st.dataframe(ts_all, use_container_width=True)
                
                # Export options
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button(
                        'Download Full Table (CSV)', 
                        ts_all.to_csv(index=False), 
                        file_name='procedures_timeseries_forecast.csv',
                        mime='text/csv'
                    )
                
                with col2:
                    buf_png = plotly_export(fig, 'png')
                    safe_download_button('Download Chart (PNG)', buf_png, 'trend_forecast_chart.png', 'image/png', key='trend_png')
                
                with col3:
                    buf_tiff = plotly_export(fig, 'tiff')
                    safe_download_button('Download Chart (TIFF)', buf_tiff, 'trend_forecast_chart.tiff', 'image/tiff', key='trend_tiff')
                    
            except Exception as e:
                st.warning(f"Forecasting not available: {str(e)}")
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(ts, use_container_width=True)
        else:
            st.warning("No time series data available")
            st.write("Debug: Time series data structure:")
            st.write(ts_data)
            
    except Exception as e:
        st.error(f"Error creating time series: {str(e)}")
        st.code(traceback.format_exc())

# === 7. Raw Data Tables ===
with tabs[6]:
    st.header('Raw Data Explorer')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader('Data Structure Information')
        st.write('**Surgical Data:**')
        st.write(f"- Shape: {df.shape}")
        st.write(f"- Columns: {len(df.columns)}")
        
        # Show procedure columns specifically
        procedure_cols = [col for col in df.columns if col.startswith('108-')]
        st.write(f"- Procedure columns: {len(procedure_cols)}")
        
        st.write('**Population Data:**')
        st.write(f"- Shape: {pop.shape}")
        st.write(f"- Columns: {list(pop.columns)}")
        
        st.write('**Facility Data:**')
        st.write(f"- Shape: {fac.shape}")
        st.write(f"- Columns: {list(fac.columns)}")
    
    with col2:
        st.subheader('Sample Data Preview')
        
        # Show sample of key columns
        if 'Surgical Procedures' in df.columns:
            sample_data = df[['Surgical Procedures'] + list(df.columns)[:5]]
            st.write("**Processed Surgical Data Sample:**")
            st.dataframe(sample_data.head())
        else:
            st.write("**Raw Surgical Data Sample:**")
            st.dataframe(df.head())
    
    # Full data explorers
    st.subheader('Full Data Tables')
    
    data_tab1, data_tab2, data_tab3 = st.tabs(['Surgical Data', 'Population Data', 'Facility Data'])
    
    with data_tab1:
        st.dataframe(df, use_container_width=True)
        st.download_button(
            'Download Surgical Data (CSV)', 
            df.to_csv(index=False), 
            file_name=f'surgical_data_{year_selected}.csv',
            mime='text/csv'
        )
    
    with data_tab2:
        st.dataframe(pop, use_container_width=True)
        st.download_button(
            'Download Population Data (CSV)', 
            pop.to_csv(index=False), 
            file_name='population_data.csv',
            mime='text/csv'
        )
    
    with data_tab3:
        st.dataframe(fac, use_container_width=True)
        if len(fac) > 0:
            st.download_button(
                'Download Facility Data (CSV)', 
                fac.to_csv(index=False), 
                file_name='facility_data.csv',
                mime='text/csv'
            )

# === 8. About ===
with tabs[7]:
    st.header('About This App')
    st.markdown('''
    ## 🏥 National Surgical Volumes Dashboard
    
    **Purpose:** Interactive analytics and visualizations for surgical capacity and operative volumes in Uganda
    
    **Data Sources:**
    - Uganda Ministry of Health HMIS (2020–2024)
    - Uganda Population Census (2024)
    - Master Facility List and Geographic Data
    
    **Features:**
    - 📊 Annual and regional surgical volumes and rates
    - 📈 Time series analysis with forecasting (2025-2030)
    - 🗺️ Interactive district/region heatmaps
    - 📋 Procedure category distributions
    - 🏥 Facility distribution analysis
    - 📁 Raw data exploration
    - 💾 Export capabilities (CSV, PDF, PNG, TIFF)
    
    **Technical Notes:**
    - Processes 100+ surgical procedure categories from HMIS data
    - Aggregates facility-level data to district and regional levels
    - Calculates population-adjusted rates per 100,000 inhabitants
    - Uses Holt-Winters exponential smoothing for forecasting
    
    **Development:**
    - Original analysis developed in Google Colab
    - Translated to Streamlit Cloud for interactive access
    - Based on comprehensive geospatial and statistical analysis
    
    **For Questions:** Contact the development team or open an issue in the repository.
    ''')
    
    # Show system info
    with st.expander("System Information"):
        st.write(f"**Streamlit Version:** {st.__version__}")
        st.write(f"**Available Years:** {YEARS}")
        st.write(f"**Data Directory:** {os.path.abspath('data/raw') if os.path.exists('data/raw') else 'Not found'}")