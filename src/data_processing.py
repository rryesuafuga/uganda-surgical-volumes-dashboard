# src/data_processing.py
import pandas as pd

def clean_numeric_columns(df):
    """Clean and convert numeric columns to proper types"""
    # Convert 'Surgical Procedures' column to numeric
    if 'Surgical Procedures' in df.columns:
        df['Surgical Procedures'] = pd.to_numeric(df['Surgical Procedures'], errors='coerce').fillna(0)
    
    # Convert other potential numeric columns
    numeric_columns = ['Population', 'Procedures', 'Total Procedures', 'Count']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

def filter_by_region(df, region):
    df = clean_numeric_columns(df)  # Clean data first
    if region == 'All' or 'Region' not in df.columns:
        return df
    return df[df['Region'] == region]

def annual_volume_table(df, pop):
    df = clean_numeric_columns(df)
    pop = clean_numeric_columns(pop)
    
    # Determine the correct column name for procedures
    proc_col = 'Surgical Procedures' if 'Surgical Procedures' in df.columns else df.columns[1]
    facility_col = 'Facility Code' if 'Facility Code' in df.columns else df.columns[0]
    
    # Check if Region column exists, if not create a summary table
    if 'Region' not in df.columns:
        # Create a single row summary without regional breakdown
        total_procedures = df[proc_col].sum()
        total_facilities = df[facility_col].nunique()
        
        agg = pd.DataFrame({
            'Region': ['All Regions'],
            'Surgical Procedures': [total_procedures],
            'Facility Count': [total_facilities]
        })
    else:
        agg = df.groupby(['Region']).agg({
            proc_col: 'sum',
            facility_col: 'nunique',
        }).reset_index()
        
        # Rename columns for consistency
        agg.columns = ['Region', 'Surgical Procedures', 'Facility Count']
    
    # Merge with population data if available
    if 'Population' in pop.columns:
        if 'Region' in pop.columns and 'Region' in df.columns:
            agg = agg.merge(pop[['Region', 'Population']], on='Region', how='left')
        else:
            # Use total population for summary
            total_pop = pop['Population'].sum()
            agg['Population'] = total_pop
        
        agg['Population'] = agg['Population'].fillna(0)
        agg['Proc Rate/100k'] = (agg['Surgical Procedures'] / agg['Population'] * 100_000).round(1)
    
    return agg

def procedure_categories_table(df):
    df = clean_numeric_columns(df)
    if 'Category' in df.columns:
        proc_col = 'Surgical Procedures' if 'Surgical Procedures' in df.columns else df.columns[1]
        result = df.groupby('Category').agg({proc_col: 'sum'}).reset_index()
        result.columns = ['Category', 'Surgical Procedures']
        return result
    else:
        return None

def facility_distribution_table(fac):
    if 'Region' in fac.columns and 'Facility Level' in fac.columns:
        return fac.groupby(['Region', 'Facility Level']).size().unstack(fill_value=0)
    else:
        return None

def district_heatmap_data(df, pop):
    df = clean_numeric_columns(df)
    pop = clean_numeric_columns(pop)
    
    if 'District' in df.columns:
        proc_col = 'Surgical Procedures' if 'Surgical Procedures' in df.columns else df.columns[1]
        map_df = df.groupby('District').agg({proc_col: 'sum'}).reset_index()
        map_df.columns = ['District', 'Surgical Procedures']
        
        if 'Population' in pop.columns and 'District' in pop.columns:
            map_df = map_df.merge(pop[['District', 'Population']], on='District', how='left')
            map_df['Population'] = map_df['Population'].fillna(0)
            map_df['Proc Rate/100k'] = (map_df['Surgical Procedures'] / map_df['Population'] * 100_000).round(1)
        
        return map_df
    else:
        return None

def trends_timeseries_data(years, load_func, pop):
    pop = clean_numeric_columns(pop)
    dfs = []
    
    for y in years:
        try:
            df_y = load_func(y)
            df_y = clean_numeric_columns(df_y)
            
            proc_col = 'Surgical Procedures' if 'Surgical Procedures' in df_y.columns else df_y.columns[1]
            total = df_y[proc_col].sum()
            
            if 'Population' in pop.columns:
                pop_total = pop['Population'].sum()
                if pop_total > 0:
                    rate = total / pop_total * 100_000
                else:
                    rate = 0
            else:
                rate = 0
            
            dfs.append({'Year': y, 'Procedures': int(total), 'Rate per 100k': round(rate, 1)})
        except Exception as e:
            print(f"Error processing year {y}: {str(e)}")
            dfs.append({'Year': y, 'Procedures': 0, 'Rate per 100k': 0})
    
    return dfs