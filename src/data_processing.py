# src/data_processing.py
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
    """Clean and process surgical data like in the Colab analysis"""
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

def filter_by_region(df, region):
    df = clean_numeric_columns(df)
    if region == 'All' or 'Region' not in df.columns:
        return df
    return df[df['Region'] == region]

def annual_volume_table(df, pop):
    df = clean_numeric_columns(df)
    pop = clean_numeric_columns(pop)
    
    # Use the processed surgical procedures column
    proc_col = 'Surgical Procedures'
    facility_col = 'Facility Code' if 'Facility Code' in df.columns else df.columns[0]
    
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
    
    # Merge with population data
    if 'Population' in pop.columns or 'Total' in pop.columns:
        pop_col = 'Population' if 'Population' in pop.columns else 'Total'
        
        if 'Region' in pop.columns and 'Region' in agg.columns:
            agg = agg.merge(pop[['Region', pop_col]], on='Region', how='left')
            agg = agg.rename(columns={pop_col: 'Population'})
        else:
            total_pop = pop[pop_col].sum()
            agg['Population'] = total_pop
        
        agg['Population'] = agg['Population'].fillna(0)
        # Avoid division by zero
        agg['Proc Rate/100k'] = np.where(
            agg['Population'] > 0,
            (agg['Surgical Procedures'] / agg['Population'] * 100_000).round(1),
            0
        )
    
    return agg

def procedure_categories_table(df):
    df = clean_numeric_columns(df)
    if 'Category' in df.columns:
        result = df.groupby('Category').agg({'Surgical Procedures': 'sum'}).reset_index()
        return result
    else:
        # Try to categorize based on procedure columns
        procedure_cols = identify_procedure_columns(df)
        if procedure_cols:
            # Create basic categories from procedure column names
            categories = []
            for col in procedure_cols:
                # Extract category from column name (basic parsing)
                category = col.split('-')[1] if '-' in col else 'Other'
                categories.append({'Category': category, 'Surgical Procedures': df[col].sum()})
            
            if categories:
                result = pd.DataFrame(categories)
                result = result.groupby('Category').agg({'Surgical Procedures': 'sum'}).reset_index()
                return result
        
        return None

def facility_distribution_table(fac):
    if 'Region' in fac.columns and 'Facility Level' in fac.columns:
        return fac.groupby(['Region', 'Facility Level']).size().unstack(fill_value=0)
    elif 'level' in fac.columns:  # Alternative column name
        if 'region' in fac.columns:
            return fac.groupby(['region', 'level']).size().unstack(fill_value=0)
    return None

def district_heatmap_data(df, pop):
    df = clean_numeric_columns(df)
    pop = clean_numeric_columns(pop)
    
    if 'District' in df.columns:
        map_df = df.groupby('District').agg({'Surgical Procedures': 'sum'}).reset_index()
        
        pop_col = 'Population' if 'Population' in pop.columns else 'Total'
        if pop_col in pop.columns and 'District' in pop.columns:
            map_df = map_df.merge(pop[['District', pop_col]], on='District', how='left')
            map_df = map_df.rename(columns={pop_col: 'Population'})
            map_df['Population'] = map_df['Population'].fillna(0)
            map_df['Proc Rate/100k'] = np.where(
                map_df['Population'] > 0,
                (map_df['Surgical Procedures'] / map_df['Population'] * 100_000).round(1),
                0
            )
        
        return map_df
    else:
        return None

def trends_timeseries_data(years, load_func, pop):
    pop = clean_numeric_columns(pop)
    dfs = []
    
    # Get total population
    pop_col = 'Population' if 'Population' in pop.columns else 'Total'
    pop_total = pop[pop_col].sum() if pop_col in pop.columns else 1
    
    for y in years:
        try:
            df_y = load_func(y)
            df_y = clean_numeric_columns(df_y)  # This now includes procedure processing
            
            total = df_y['Surgical Procedures'].sum()
            rate = (total / pop_total * 100_000).round(1) if pop_total > 0 else 0
            
            dfs.append({'Year': y, 'Procedures': int(total), 'Rate per 100k': rate})
        except Exception as e:
            print(f"Error processing year {y}: {str(e)}")
            dfs.append({'Year': y, 'Procedures': 0, 'Rate per 100k': 0})
    
    return dfs