# src/data_loading.py (CORRECTED for population data handling)
import os
import pandas as pd
import geopandas as gpd
from functools import lru_cache
import streamlit as st

# Configuration
DATA_DIR = 'data/raw'
YEARS = [2020, 2021, 2022, 2023, 2024]

# File path patterns - updated based on actual Colab file structure
SURGICAL_DATA_PATTERNS = [
    'Uganda Surgical Procedures_raw data_{year}.csv',
    'Uganda_Surgical_Procedures_raw_data_{year}.csv',
    'surgical_procedures_{year}.csv',
    'Uganda Surgical Procedures_{year}.csv'
]

# CORRECTED: Population data patterns based on Colab structure
POPULATION_DATA_PATTERNS = [
    'Uganda Population Data 2024/Population_census 2024.xlsx',
    'Uganda Population Data 2024/Population by Subregion, 2024.xlsx',  # This is the correct sheet from Colab
    'Uganda Population Data 2024/District population, 2024.xlsx',
    'Population_census_2024.xlsx',
    'Population by Subregion, 2024.xlsx',
    'District population, 2024.xlsx'
]

FACILITY_DATA_PATTERNS = [
    'Uganda_Shape_files_2020/GEO MFL SURVEY DATASET.xlsx',
    'GEO MFL SURVEY DATASET.xlsx',
    'Master Facility List/Uganda_MFL_2024.csv',
    'MFL/Uganda_Master_Facility_List.csv',
    'facility_data.xlsx',
    'mfl_data.csv'
]

SHAPEFILE_PATTERNS = [
    'Uganda_Shape_files_2020/Region/UDHS_Regions_2019.shp',
    'Uganda_Shape_files_2020/UBOS_Districts 146_2021/*.shp',
    'Uganda_Shape_files_2020/uganda_districts_2019-wgs84/*.shp',
    'shapefiles/regions.shp',
    'shapefiles/districts.shp'
]

def find_file(patterns, data_dir=DATA_DIR):
    """
    Find the first existing file from a list of patterns
    """
    for pattern in patterns:
        # Handle wildcard patterns for shapefiles
        if '*' in pattern:
            import glob
            base_dir = os.path.dirname(pattern)
            file_pattern = os.path.basename(pattern)
            full_pattern = os.path.join(data_dir, base_dir, file_pattern)
            matches = glob.glob(full_pattern)
            if matches:
                return matches[0]
        else:
            full_path = os.path.join(data_dir, pattern)
            if os.path.exists(full_path):
                return full_path
    return None

@lru_cache(maxsize=10)
def load_surgical_data(year):
    """
    Load surgical procedure data for a specific year
    Handles multiple possible file naming conventions
    """
    # Try different naming patterns
    patterns_for_year = [pattern.format(year=year) for pattern in SURGICAL_DATA_PATTERNS]
    file_path = find_file(patterns_for_year)
    
    if file_path is None:
        # List available files for debugging
        available_files = []
        if os.path.exists(DATA_DIR):
            for file in os.listdir(DATA_DIR):
                if file.endswith('.csv') and str(year) in file:
                    available_files.append(file)
        
        error_msg = f"Surgical data file for {year} not found. Tried patterns: {patterns_for_year}"
        if available_files:
            error_msg += f"\nAvailable files with {year}: {available_files}"
        else:
            error_msg += f"\nNo CSV files found containing {year} in {DATA_DIR}"
        
        raise FileNotFoundError(error_msg)
    
    try:
        df = pd.read_csv(file_path)
        print(f"Successfully loaded surgical data for {year}: {df.shape}")
        return df
    except Exception as e:
        raise Exception(f"Error reading surgical data file {file_path}: {str(e)}")

@lru_cache(maxsize=1)
def load_population_data():
    """
    Load population data with CORRECTED sheet handling based on Colab analysis
    The Colab analysis used 'Population by Subregion, 2024' sheet specifically
    """
    file_path = find_file(POPULATION_DATA_PATTERNS)
    
    if file_path is None:
        # List available population files for debugging
        available_files = []
        pop_dir = os.path.join(DATA_DIR, 'Uganda Population Data 2024')
        if os.path.exists(pop_dir):
            available_files = [f for f in os.listdir(pop_dir) if f.endswith(('.xlsx', '.csv'))]
        elif os.path.exists(DATA_DIR):
            available_files = [f for f in os.listdir(DATA_DIR) if 'population' in f.lower()]
        
        error_msg = f"Population data file not found. Tried patterns: {POPULATION_DATA_PATTERNS}"
        if available_files:
            error_msg += f"\nAvailable population files: {available_files}"
        
        raise FileNotFoundError(error_msg)
    
    try:
        # CORRECTED: Handle Excel files properly based on Colab logic
        if file_path.endswith('.xlsx'):
            # First, get all sheet names
            xl_file = pd.ExcelFile(file_path)
            sheet_names = xl_file.sheet_names
            print(f"Available sheets in population file: {sheet_names}")
            
            # CORRECTED: Priority order based on what Colab actually used
            sheet_patterns = [
                'Population by Subregion, 2024',  # This is what Colab used
                'District population, 2024',       # Alternative for district-level
                'Population_census 2024',
                'Population by district',
                'District population',
                'Population',
                'Sheet1'
            ]
            
            sheet_to_use = None
            for pattern in sheet_patterns:
                if pattern in sheet_names:
                    sheet_to_use = pattern
                    print(f"Using sheet: {sheet_to_use}")
                    break
            
            if sheet_to_use is None:
                # Use the first sheet and warn
                sheet_to_use = sheet_names[0]
                st.warning(f"Using default sheet '{sheet_to_use}' from available sheets: {sheet_names}")
            
            df = pd.read_excel(file_path, sheet_name=sheet_to_use)
            
            # CORRECTED: Apply the same column standardization as in Colab
            print(f"Original population data columns: {list(df.columns)}")
            
            # The Colab code expected these columns for subregion data
            expected_columns = ['Region', 'Male', 'Female', 'Total']
            if list(df.columns) != expected_columns and len(df.columns) >= 4:
                # Get the actual first 4 columns, whatever they're called
                current_columns = list(df.columns)[:4]
                # Create a mapping from current to expected column names
                column_mapping = dict(zip(current_columns, expected_columns))
                # Rename the columns
                df = df.rename(columns=column_mapping)
                print(f"Renamed columns to: {df.columns.tolist()}")
        else:
            df = pd.read_csv(file_path)
        
        print(f"Successfully loaded population data: {df.shape}")
        print(f"Population data sample:")
        print(df.head())
        
        # CRITICAL: Ensure numeric columns are numeric
        for col in ['Male', 'Female', 'Total']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove any completely null rows
        df = df.dropna(how='all')
        
        # Calculate total population for verification
        if 'Total' in df.columns:
            total_pop = df['Total'].sum()
            print(f"Total population in loaded data: {total_pop:,}")
            
            # If total population is still 0 or very low, there might be an issue
            if total_pop < 1000000:  # Uganda should have 40+ million people
                print("WARNING: Total population seems unusually low")
                print("Sample of population data:")
                print(df[['Region', 'Total']].head(10))
        
        return df
        
    except Exception as e:
        raise Exception(f"Error reading population data file {file_path}: {str(e)}")

@lru_cache(maxsize=1)
def load_facility_metadata():
    """
    Load facility metadata with flexible file pattern matching
    """
    file_path = find_file(FACILITY_DATA_PATTERNS)
    
    if file_path is None:
        # List available facility files for debugging
        available_files = []
        shape_dir = os.path.join(DATA_DIR, 'Uganda_Shape_files_2020')
        if os.path.exists(shape_dir):
            available_files = [f for f in os.listdir(shape_dir) if f.endswith(('.xlsx', '.csv'))]
        elif os.path.exists(DATA_DIR):
            available_files = [f for f in os.listdir(DATA_DIR) if any(term in f.lower() for term in ['facility', 'mfl', 'hospital'])]
        
        error_msg = f"Facility data file not found. Tried patterns: {FACILITY_DATA_PATTERNS}"
        if available_files:
            error_msg += f"\nAvailable facility files: {available_files}"
        
        # Return empty dataframe instead of raising error (facility data is optional)
        st.warning(error_msg)
        return pd.DataFrame()
    
    try:
        if file_path.endswith('.xlsx'):
            # Try different sheet names for facility data
            xl_file = pd.ExcelFile(file_path)
            sheet_names = xl_file.sheet_names
            
            # Use first sheet or find a relevant one
            sheet_to_use = sheet_names[0]
            if len(sheet_names) > 1:
                st.info(f"Using sheet '{sheet_to_use}' from available sheets: {sheet_names}")
            
            df = pd.read_excel(file_path, sheet_name=sheet_to_use)
        else:
            df = pd.read_csv(file_path)
        
        print(f"Successfully loaded facility data: {df.shape}")
        print(f"Facility columns: {list(df.columns)}")
        return df
        
    except Exception as e:
        st.warning(f"Error reading facility data file {file_path}: {str(e)}")
        return pd.DataFrame()

@lru_cache(maxsize=1)
def load_shapefile():
    """
    Load shapefile data with flexible pattern matching
    """
    file_path = find_file(SHAPEFILE_PATTERNS)
    
    if file_path is None:
        # List available shapefiles for debugging
        available_files = []
        shape_dir = os.path.join(DATA_DIR, 'Uganda_Shape_files_2020')
        if os.path.exists(shape_dir):
            for root, dirs, files in os.walk(shape_dir):
                for file in files:
                    if file.endswith('.shp'):
                        rel_path = os.path.relpath(os.path.join(root, file), DATA_DIR)
                        available_files.append(rel_path)
        elif os.path.exists(DATA_DIR):
            for root, dirs, files in os.walk(DATA_DIR):
                for file in files:
                    if file.endswith('.shp'):
                        rel_path = os.path.relpath(os.path.join(root, file), DATA_DIR)
                        available_files.append(rel_path)
        
        error_msg = f"Shapefile not found. Tried patterns: {SHAPEFILE_PATTERNS}"
        if available_files:
            error_msg += f"\nAvailable shapefiles: {available_files}"
        
        # Return None instead of raising error (shapefile is optional for basic functionality)
        st.warning(error_msg)
        return None
    
    try:
        gdf = gpd.read_file(file_path)
        print(f"Successfully loaded shapefile: {gdf.shape}")
        print(f"Shapefile columns: {list(gdf.columns)}")
        print(f"Shapefile CRS: {gdf.crs}")
        return gdf
        
    except Exception as e:
        st.warning(f"Error reading shapefile {file_path}: {str(e)}")
        return None

def get_data_directory_info():
    """Get information about the data directory structure for debugging"""
    info = {
        'data_dir_exists': os.path.exists(DATA_DIR),
        'data_dir_path': os.path.abspath(DATA_DIR) if os.path.exists(DATA_DIR) else 'Not found',
        'files_found': {},
        'directory_structure': {}
    }
    
    if os.path.exists(DATA_DIR):
        # Get directory structure
        for root, dirs, files in os.walk(DATA_DIR):
            rel_root = os.path.relpath(root, DATA_DIR)
            if rel_root == '.':
                rel_root = 'root'
            info['directory_structure'][rel_root] = {
                'directories': dirs,
                'files': files
            }
        
        # Check for specific file types
        info['files_found']['csv_files'] = []
        info['files_found']['xlsx_files'] = []
        info['files_found']['shp_files'] = []
        
        for root, dirs, files in os.walk(DATA_DIR):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), DATA_DIR)
                if file.endswith('.csv'):
                    info['files_found']['csv_files'].append(rel_path)
                elif file.endswith('.xlsx'):
                    info['files_found']['xlsx_files'].append(rel_path)
                elif file.endswith('.shp'):
                    info['files_found']['shp_files'].append(rel_path)
    
    return info

def validate_data_files():
    """Validate that required data files are available"""
    validation = {
        'surgical_data': {},
        'population_data': {'available': False, 'path': None, 'error': None},
        'facility_data': {'available': False, 'path': None, 'error': None},
        'shapefile_data': {'available': False, 'path': None, 'error': None}
    }
    
    # Check surgical data for each year
    for year in YEARS:
        patterns_for_year = [pattern.format(year=year) for pattern in SURGICAL_DATA_PATTERNS]
        file_path = find_file(patterns_for_year)
        
        validation['surgical_data'][year] = {
            'available': file_path is not None,
            'path': file_path,
            'error': None if file_path else f"No file found for patterns: {patterns_for_year}"
        }
    
    # Check population data
    pop_path = find_file(POPULATION_DATA_PATTERNS)
    validation['population_data']['available'] = pop_path is not None
    validation['population_data']['path'] = pop_path
    if pop_path is None:
        validation['population_data']['error'] = f"No file found for patterns: {POPULATION_DATA_PATTERNS}"
    
    # Check facility data
    fac_path = find_file(FACILITY_DATA_PATTERNS)
    validation['facility_data']['available'] = fac_path is not None
    validation['facility_data']['path'] = fac_path
    if fac_path is None:
        validation['facility_data']['error'] = f"No file found for patterns: {FACILITY_DATA_PATTERNS}"
    
    # Check shapefile data
    shp_path = find_file(SHAPEFILE_PATTERNS)
    validation['shapefile_data']['available'] = shp_path is not None
    validation['shapefile_data']['path'] = shp_path
    if shp_path is None:
        validation['shapefile_data']['error'] = f"No file found for patterns: {SHAPEFILE_PATTERNS}"
    
    return validation

# Test function for debugging
def test_data_loading():
    """
    Test data loading functions and return results for debugging
    """
    results = {
        'directory_info': get_data_directory_info(),
        'validation': validate_data_files(),
        'load_tests': {}
    }
    
    # Test loading each type of data
    for year in YEARS:
        try:
            df = load_surgical_data(year)
            results['load_tests'][f'surgical_{year}'] = {
                'success': True,
                'shape': df.shape,
                'columns': list(df.columns)[:10],  # First 10 columns
                'procedure_columns': len([col for col in df.columns if col.startswith('108-')])
            }
        except Exception as e:
            results['load_tests'][f'surgical_{year}'] = {
                'success': False,
                'error': str(e)
            }
    
    # Test population data
    try:
        pop_df = load_population_data()
        results['load_tests']['population'] = {
            'success': True,
            'shape': pop_df.shape,
            'columns': list(pop_df.columns)
        }
    except Exception as e:
        results['load_tests']['population'] = {
            'success': False,
            'error': str(e)
        }
    
    # Test facility data
    try:
        fac_df = load_facility_metadata()
        results['load_tests']['facility'] = {
            'success': True,
            'shape': fac_df.shape,
            'columns': list(fac_df.columns)
        }
    except Exception as e:
        results['load_tests']['facility'] = {
            'success': False,
            'error': str(e)
        }
    
    # Test shapefile
    try:
        gdf = load_shapefile()
        if gdf is not None:
            results['load_tests']['shapefile'] = {
                'success': True,
                'shape': gdf.shape,
                'columns': list(gdf.columns),
                'crs': str(gdf.crs)
            }
        else:
            results['load_tests']['shapefile'] = {
                'success': False,
                'error': 'Shapefile returned None'
            }
    except Exception as e:
        results['load_tests']['shapefile'] = {
            'success': False,
            'error': str(e)
        }
    
    return results