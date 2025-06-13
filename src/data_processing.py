# src/data_processing.py (CORRECTED based on Colab analysis)
import pandas as pd
import numpy as np

# Region name mapping from Colab analysis
REGION_MAPPING = {
    'Acholi': 'Acholi',
    'Ankole': 'Ankole',
    'Bugisu': 'Elgon',
    'Bukedi': 'Bukedi',
    'Bunyoro': 'Bunyoro',
    'Busoga': 'Busoga',
    'Kampala': 'Kampala',
    'Karamoja': 'Karamoja',
    'Kigezi': 'Kigezi',
    'Lango': 'Lango',
    'North Central': 'Buganda',  # Key fix - combine into Buganda
    'South Central': 'Buganda',  # Key fix - combine into Buganda
    'Teso': 'Teso',
    'Tooro': 'Tooro',
    'West Nile': 'West Nile'
}

def identify_procedure_columns(df):
    """
    Identify ALL procedure columns that contain the actual procedure counts
    These are columns that start with "108-" and contain procedure names
    """
    procedure_cols = [col for col in df.columns if col.startswith('108-')]
    print(f"Identified {len(procedure_cols)} procedure columns")
    return procedure_cols

def clean_and_process_surgical_data(df):
    """Clean and process surgical data exactly like in the Colab analysis"""
    # Clean district names by removing " District" suffix
    if 'orgunitlevel3' in df.columns:
        df['District'] = df['orgunitlevel3'].str.replace(' District', '', case=False).str.strip()
        
        # Add and standardize region column
        if 'orgunitlevel2' in df.columns:
            df['Region_Original'] = df['orgunitlevel2']
            df['Region_Standardized'] = df['orgunitlevel2'].map(REGION_MAPPING)
            df['Region_Standardized'].fillna(df['orgunitlevel2'], inplace=True)
            df['Region'] = df['Region_Standardized']
    
    # Identify procedure columns
    procedure_cols = identify_procedure_columns(df)
    
    if procedure_cols:
        # Convert all procedure columns to numeric
        for col in procedure_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Sum all procedure columns for each row (facility)
        df['total_procedures'] = df[procedure_cols].sum(axis=1)
        df['Surgical Procedures'] = df['total_procedures']  # For compatibility
    else:
        print("Warning: No procedure columns found!")
        df['Surgical Procedures'] = 0
    
    return df

def clean_numeric_columns(df):
    """Clean and convert numeric columns to proper types"""
    # Apply surgical data processing first
    df = clean_and_process_surgical_data(df)
    
    # Convert other potential numeric columns
    numeric_columns = ['Population', 'Procedures', 'Total Procedures', 'Count', 'Total']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

def process_population_data(pop_df):
    """
    Process population data to handle different column naming and structure
    Based on the Colab logic for population data processing
    """
    print("Processing population data...")
    print(f"Original population data shape: {pop_df.shape}")
    print(f"Original population columns: {list(pop_df.columns)}")
    
    # Clean and prepare population data
    # Standardize column names if necessary (from Colab logic)
    expected_columns = ['Region', 'Male', 'Female', 'Total']
    if list(pop_df.columns) != expected_columns and len(pop_df.columns) >= 4:
        # Get the actual first 4 columns, whatever they're called
        current_columns = list(pop_df.columns)[:4]
        # Create a mapping from current to expected column names
        column_mapping = dict(zip(current_columns, expected_columns))
        # Rename the columns
        pop_df = pop_df.rename(columns=column_mapping)
        print(f"Renamed population columns to: {pop_df.columns.tolist()}")

    # Clean the data
    pop_df = pop_df.dropna(how='all')

    # Ensure numeric columns are actually numeric
    for col in ['Male', 'Female', 'Total']:
        if col in pop_df.columns:
            pop_df[col] = pd.to_numeric(pop_df[col], errors='coerce')

    # Remove Uganda total row if present (to avoid double counting)
    pop_df = pop_df[pop_df['Region'].str.lower() != 'uganda']

    # Create lowercase version for matching
    pop_df['region_lower'] = pop_df['Region'].str.lower()

    print(f"Processed population data shape: {pop_df.shape}")
    print(f"Population data sample:")
    print(pop_df.head())
    
    return pop_df

def filter_by_region(df, region):
    df = clean_numeric_columns(df)
    if region == 'All' or 'Region' not in df.columns:
        return df
    return df[df['Region'] == region]

def annual_volume_table(df, pop):
    """Create annual volume table with CORRECTED population handling"""
    df = clean_numeric_columns(df)
    pop = process_population_data(pop.copy())  # Process population data properly
    
    # Use the processed surgical procedures column
    proc_col = 'Surgical Procedures'
    
    # CORRECTED: Use proper facility identification
    # The issue was using wrong column for facility count
    if 'orgunitlevel3' in df.columns:
        facility_col = 'orgunitlevel3'  # This is the actual facility identifier
    elif 'Facility Code' in df.columns:
        facility_col = 'Facility Code'
    else:
        facility_col = df.columns[0]  # Fallback
    
    print(f"Using facility column: {facility_col}")
    print(f"Unique facilities in data: {df[facility_col].nunique()}")
    
    # Check if Region column exists
    if 'Region' not in df.columns:
        total_procedures = df[proc_col].sum()
        total_facilities = df[facility_col].nunique()
        
        agg = pd.DataFrame({
            'Region': ['All Regions'],
            'Surgical Procedures': [total_procedures],
            'Facility Count': [total_facilities]
        })
    else:
        # Group by standardized regions
        agg = df.groupby(['Region']).agg({
            proc_col: 'sum',
            facility_col: 'nunique',
        }).reset_index()
        agg.columns = ['Region', 'Surgical Procedures', 'Facility Count']
    
    # CORRECTED: Merge with population data properly
    if 'Total' in pop.columns:
        # Calculate total population correctly
        total_population = pop['Total'].sum()
        print(f"Total population calculated: {total_population:,}")
        
        if 'Region' in pop.columns and 'Region' in agg.columns:
            # Try to merge by region
            agg = agg.merge(pop[['Region', 'Total']], on='Region', how='left')
            agg = agg.rename(columns={'Total': 'Population'})
            
            # Fill missing values with proportional population
            agg['Population'] = agg['Population'].fillna(0)
            
            # For "All Regions" row, use total population
            if 'All Regions' in agg['Region'].values:
                agg.loc[agg['Region'] == 'All Regions', 'Population'] = total_population
        else:
            # Use total population for all rows
            agg['Population'] = total_population
        
        # Avoid division by zero and calculate rates
        agg['Proc Rate/100k'] = np.where(
            agg['Population'] > 0,
            (agg['Surgical Procedures'] / agg['Population'] * 100_000).round(1),
            0
        )
        
        print(f"Annual volume table result:")
        print(agg)
    else:
        print("Warning: No 'Total' column found in population data")
        print(f"Available population columns: {list(pop.columns)}")
    
    return agg

def procedure_categories_table(df):
    """Create procedure categories table with better categorization"""
    df = clean_numeric_columns(df)
    
    if 'Category' in df.columns:
        result = df.groupby('Category').agg({'Surgical Procedures': 'sum'}).reset_index()
        return result
    else:
        # Try to categorize based on procedure columns (from Colab logic)
        procedure_cols = identify_procedure_columns(df)
        if procedure_cols:
            # Create basic categories from procedure column names
            categories = []
            for col in procedure_cols:
                # Extract category from column name (improved parsing)
                if '-' in col:
                    parts = col.split('-')
                    if len(parts) >= 2:
                        # Use the second part as category (after "108-")
                        category_name = parts[1].strip()
                        # Clean up category name
                        category_name = category_name.replace('_', ' ').title()
                        category_count = df[col].sum()
                        if category_count > 0:  # Only include categories with procedures
                            categories.append({
                                'Category': category_name, 
                                'Surgical Procedures': category_count
                            })
            
            if categories:
                result = pd.DataFrame(categories)
                # Group by category in case there are duplicates
                result = result.groupby('Category').agg({'Surgical Procedures': 'sum'}).reset_index()
                # Sort by procedure count
                result = result.sort_values('Surgical Procedures', ascending=False)
                return result
        
        return None

def facility_distribution_table(fac):
    """Create facility distribution table with better column detection"""
    if len(fac) == 0:
        return None
        
    # Try different possible column name combinations
    region_cols = ['Region', 'region', 'REGION', 'orgunitlevel2']
    level_cols = ['Facility Level', 'Level', 'level', 'LEVEL', 'facility_level', 'Type']
    
    region_col = None
    level_col = None
    
    # Find region column
    for col in region_cols:
        if col in fac.columns:
            region_col = col
            break
    
    # Find level column  
    for col in level_cols:
        if col in fac.columns:
            level_col = col
            break
    
    if region_col and level_col:
        return fac.groupby([region_col, level_col]).size().unstack(fill_value=0)
    else:
        print(f"Available facility columns: {list(fac.columns)}")
        return None

def district_heatmap_data(df, pop):
    """Create district heatmap data with corrected population handling"""
    df = clean_numeric_columns(df)
    pop = process_population_data(pop.copy())
    
    if 'District' in df.columns:
        map_df = df.groupby('District').agg({'Surgical Procedures': 'sum'}).reset_index()
        
        # Look for population by district
        if 'District' in pop.columns and 'Total' in pop.columns:
            # Create lowercase district names for matching
            map_df['district_lower'] = map_df['District'].str.lower()
            pop['district_lower'] = pop['District'].str.lower()
            
            # Merge with population
            map_df = map_df.merge(pop[['district_lower', 'Total']], on='district_lower', how='left')
            map_df = map_df.rename(columns={'Total': 'Population'})
            map_df['Population'] = map_df['Population'].fillna(0)
            
            # Calculate rates
            map_df['Proc Rate/100k'] = np.where(
                map_df['Population'] > 0,
                (map_df['Surgical Procedures'] / map_df['Population'] * 100_000).round(1),
                0
            )
        
        return map_df
    else:
        return None

def trends_timeseries_data(years, load_func, pop):
    """Create time series data with corrected population handling"""
    pop = process_population_data(pop.copy())
    dfs = []
    
    # Get total population correctly
    if 'Total' in pop.columns:
        pop_total = pop['Total'].sum()
        print(f"Using total population for trends: {pop_total:,}")
    else:
        pop_total = 1  # Avoid division by zero
        print("Warning: Could not calculate total population for trends")
    
    for y in years:
        try:
            df_y = load_func(y)
            df_y = clean_numeric_columns(df_y)  # This now includes procedure processing
            
            total = df_y['Surgical Procedures'].sum()
            rate = (total / pop_total * 100_000).round(1) if pop_total > 0 else 0
            
            dfs.append({'Year': y, 'Procedures': int(total), 'Rate per 100k': rate})
            print(f"Year {y}: {total:,} procedures, rate: {rate}")
        except Exception as e:
            print(f"Error processing year {y}: {str(e)}")
            dfs.append({'Year': y, 'Procedures': 0, 'Rate per 100k': 0})
    
    return dfs