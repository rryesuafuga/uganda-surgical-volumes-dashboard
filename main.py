# main.py (Modularized for /src structure, with Holt-Winters Forecasting)
import streamlit as st
import os
import pandas as pd
import plotly.express as px
import geopandas as gpd

from src.data_loading import load_surgical_data, load_population_data, load_facility_metadata, load_shapefile, YEARS
from src.data_processing import filter_by_region, annual_volume_table, procedure_categories_table, facility_distribution_table, district_heatmap_data, trends_timeseries_data
from src.export_helpers import dataframe_to_pdf, plotly_export, safe_download_button
from src.forecasting import forecast_procedure_rate

# --- SIDEBAR FILTERS ---
st.sidebar.title('Filters')
year_selected = st.sidebar.selectbox('Year', YEARS, index=YEARS.index(2024))
region_selected = st.sidebar.selectbox('Region', ['All', 'Central', 'East', 'North', 'West'])

# --- LOAD DATA ---
df = load_surgical_data(year_selected)
pop = load_population_data()
fac = load_facility_metadata()
gdf = load_shapefile()
df = filter_by_region(df, region_selected)

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
    
    # Check data structure and handle non-numeric values
    try:
        if 'Surgical Procedures' in df.columns:
            # Convert to numeric, coercing errors to NaN, then fill NaN with 0
            df['Surgical Procedures'] = pd.to_numeric(df['Surgical Procedures'], errors='coerce').fillna(0)
            total_procedures = df['Surgical Procedures'].sum()
        else:
            # Handle fallback column (convert to numeric as well)
            df.iloc[:,1] = pd.to_numeric(df.iloc[:,1], errors='coerce').fillna(0)
            total_procedures = df.iloc[:,1].sum()
        
        total_procedures = int(total_procedures)  # Convert to int to ensure proper formatting
        
        if 'Facility Code' in df.columns:
            total_facilities = df['Facility Code'].nunique()
        else:
            total_facilities = df.iloc[:,0].nunique()
        
        total_facilities = int(total_facilities)  # Convert to int to ensure proper formatting
        
        st.metric('Total Procedures', f"{total_procedures:,}")
        st.metric('Reporting Facilities', total_facilities)
        
        if 'Population' in pop.columns:
            # Also ensure population data is numeric
            pop['Population'] = pd.to_numeric(pop['Population'], errors='coerce').fillna(0)
            total_pop = pop['Population'].sum()
            total_pop = int(total_pop)  # Convert to int
            
            if total_pop > 0:  # Avoid division by zero
                proc_rate = total_procedures / total_pop * 100_000
                st.metric('Procedures per 100,000', f"{proc_rate:,.1f}")
            else:
                st.metric('Procedures per 100,000', "N/A")
    
    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        st.write("Please check your data format. Expected numeric values for procedures and population.")
        
        # Display data structure for debugging
        st.write("Data structure:")
        st.write(f"Columns: {list(df.columns)}")
        st.write("First few rows:")
        st.dataframe(df.head())

# === 2. Annual Volumes & Rates Table ===
with tabs[1]:
    st.header('Annual Surgical Volumes & Rates')
    try:
        agg = annual_volume_table(df, pop)
        st.dataframe(agg)
        st.download_button('Download Table (CSV)', agg.to_csv(index=False), file_name='annual_volumes_rates.csv')
        pdf_file = dataframe_to_pdf(agg, "Annual Surgical Volumes & Rates")
        with open(pdf_file, "rb") as f:
            st.download_button("Download Table as PDF", f, file_name="annual_volumes_rates.pdf", mime="application/pdf")
    except Exception as e:
        st.error(f"Error creating annual volumes table: {str(e)}")
        st.write("Available columns in surgical data:", list(df.columns))
        st.write("Available columns in population data:", list(pop.columns))
        st.dataframe(df.head())

# === 3. Procedure Categories Table (Table 3, 2024) ===
with tabs[2]:
    st.header('Surgical Procedures by Category (2024)')
    cat_counts = procedure_categories_table(df)
    if cat_counts is not None:
        st.bar_chart(cat_counts.set_index('Category'))
        st.dataframe(cat_counts)
        st.download_button('Download Table (CSV)', cat_counts.to_csv(index=False), file_name='category_counts.csv')
        pdf_file = dataframe_to_pdf(cat_counts, "Surgical Procedures by Category (2024)")
        with open(pdf_file, "rb") as f:
            st.download_button("Download Table as PDF", f, file_name="procedure_categories.pdf", mime="application/pdf")

# === 4. Facility Distribution Table ===
with tabs[3]:
    st.header('Facility Distribution')
    fac_table = facility_distribution_table(fac)
    if fac_table is not None:
        st.dataframe(fac_table)
        st.download_button('Download Table (CSV)', fac_table.to_csv(), file_name='facility_distribution.csv')
        pdf_file = dataframe_to_pdf(fac_table.reset_index(), "Facility Distribution")
        with open(pdf_file, "rb") as f:
            st.download_button("Download Table as PDF", f, file_name="facility_distribution.pdf", mime="application/pdf")

# === 5. Geographic Heatmap (District-level Rates) ===
with tabs[4]:
    st.header('Surgical Procedure Rate Heatmap (District)')
    map_df = district_heatmap_data(df, pop)
    if map_df is not None and 'District' in gdf.columns:
        gdf_merged = gdf.merge(map_df, left_on='District', right_on='District', how='left')
        fig = px.choropleth(gdf_merged,
                            geojson=gdf_merged.geometry,
                            locations=gdf_merged.index,
                            color='Proc Rate/100k',
                            hover_name='District',
                            title=f'Surgical Procedures per 100,000 ({year_selected})')
        fig.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Safe image export
        buf_png = plotly_export(fig, 'png')
        buf_tiff = plotly_export(fig, 'tiff')
        safe_download_button('Download Map (PNG)', buf_png, 'district_heatmap.png', 'image/png', key='map_png')
        safe_download_button('Download Map (TIFF)', buf_tiff, 'district_heatmap.tiff', 'image/tiff', key='map_tiff')
    else:
        st.warning('District columns not found in data or shapefile.')

# === 6. Trends: Time Series Plots (with Forecast) ===
with tabs[5]:
    st.header('Trends: Procedures per 100,000 by Year and Forecast (2025–2030)')
    ts = pd.DataFrame(trends_timeseries_data(
        YEARS,
        load_surgical_data,
        pop
    ))
    fig = px.line(ts, x='Year', y='Rate per 100k', title='Procedures per 100,000 by Year', markers=True)

    # --- Forecast Panel using Holt-Winters Exponential Smoothing ---
    forecast_df = forecast_procedure_rate(ts, steps=6)  # 2025–2030
    ts_all = pd.concat([ts, forecast_df], ignore_index=True)
    fig.add_scatter(x=forecast_df['Year'], y=forecast_df['Rate per 100k'],
                    mode='lines+markers', name='Forecast', line=dict(dash='dash', color='red'))
    st.plotly_chart(fig)

    # Show combined observed + forecast table
    st.write('Observed and Forecasted Rates (2020–2030)')
    st.dataframe(ts_all)
    st.download_button('Download Full Table (CSV)', ts_all.to_csv(index=False), file_name='procedures_timeseries_forecast.csv')
    # Export buttons for chart
    buf_png = plotly_export(fig, 'png')
    buf_tiff = plotly_export(fig, 'tiff')
    safe_download_button('Download Chart (PNG)', buf_png, 'trend_forecast_chart.png', 'image/png', key='trend_png')
    safe_download_button('Download Chart (TIFF)', buf_tiff, 'trend_forecast_chart.tiff', 'image/tiff', key='trend_tiff')

# === 7. Raw Data Tables ===
with tabs[6]:
    st.header('Raw Data Explorer')
    
    st.subheader('Data Structure Information')
    st.write('**Surgical Data Columns:**', list(df.columns))
    st.write('**Surgical Data Shape:**', df.shape)
    st.write('**Population Data Columns:**', list(pop.columns))
    st.write('**Population Data Shape:**', pop.shape)
    st.write('**Facility Data Columns:**', list(fac.columns))
    st.write('**Facility Data Shape:**', fac.shape)
    
    st.subheader('Surgical Data')
    st.dataframe(df.head(10))
    
    st.subheader('Population Data')
    st.dataframe(pop.head(10))
    
    st.subheader('Facility Metadata')
    st.dataframe(fac.head(10))

# === 8. About ===
with tabs[7]:
    st.header('About This App')
    st.markdown('''
    **National Surgical Volumes Dashboard**
    - Source: Uganda Ministry of Health HMIS (2020–2024)
    - Developed for streamlined reporting, monitoring, and research
    - All outputs formerly saved in the 'results' folder are now interactive and accessible in this dashboard.
    ''')