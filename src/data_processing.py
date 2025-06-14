# src/data_processing.py (COMPLETELY FIXED - Full Colab Logic Translation)
import pandas as pd
import numpy as np
import streamlit as st

# Region name mapping from Colab analysis - EXACT COPY
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
    'North Central': 'Buganda',  # CRITICAL: combine into Buganda
    'South Central': 'Buganda',  # CRITICAL: combine into Buganda
    'Teso': 'Teso',
    'Tooro': 'Tooro',
    'West Nile': 'West Nile'
}

def identify_procedure_columns(df):
    """
    EXACT COLAB LOGIC: Identify ALL procedure columns that contain the actual procedure counts
    These are columns that start with "108-" and contain procedure names
    """
    procedure_cols = [col for col in df.columns if col.startswith('108-')]
    
    if procedure_cols:
        print(f"✅ Identified {len(procedure_cols)} procedure columns")
        print(f"Sample procedure columns: {procedure_cols[:5]}")
    else:
        print("❌ No procedure columns found starting with '108-'")
    
    return procedure_cols

def clean_and_process_surgical_data(df):
    """
    EXACT COLAB LOGIC: Clean and process surgical data 
    This is the CORE calculation that was missing in the original Streamlit version
    """
    if df is None or len(df) == 0:
        print("❌ Empty dataframe received")
        return df
    
    df = df.copy()  # Work with a copy
    print(f"Processing surgical data: {df.shape[0]} rows, {df.shape[1]} columns")
    
    # Step 1: Clean district names (EXACT COLAB LOGIC)
    if 'orgunitlevel3' in df.columns:
        df['District'] = df['orgunitlevel3'].str.replace(' District', '', case=False).str.strip()
        print(f"✅ Created District column from orgunitlevel3")
        
        # Step 2: Add and standardize region column (EXACT COLAB LOGIC)
        if 'orgunitlevel2' in df.columns:
            df['Region_Original'] = df['orgunitlevel2']
            df['Region_Standardized'] = df['orgunitlevel2'].map(REGION_MAPPING)
            df['Region_Standardized'].fillna(df['orgunitlevel2'], inplace=True)
            df['Region'] = df['Region_Standardized']
            print(f"✅ Standardized regions using mapping")
    
    # Step 3: CRITICAL - Identify and process procedure columns (THIS WAS MISSING)
    procedure_cols = identify_procedure_columns(df)
    
    if procedure_cols:
        print(f"🔄 Processing {len(procedure_cols)} procedure columns...")
        
        # EXACT COLAB LOGIC: Convert all procedure columns to numeric
        for col in procedure_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # CORE CALCULATION: Sum all procedure columns for each row (facility)
        df['total_procedures'] = df[procedure_cols].sum(axis=1)
        df['Surgical Procedures'] = df['total_procedures']  # For compatibility
        
        # Verification (EXACT COLAB LOGIC)
        total_procs = df['total_procedures'].sum()
        facilities_with_procs = (df['total_procedures'] > 0).sum()
        total_facilities = len(df)
        
        print(f"✅ CALCULATION COMPLETE:")
        print(f"   Total procedures: {total_procs:,}")
        print(f"   Facilities with procedures: {facilities_with_procs:,}")
        print(f"   Total facilities: {total_facilities:,}")
        print(f"   Average procedures per facility: {total_procs/total_facilities:.1f}")
        
    else:
        print("❌ CRITICAL ERROR: No procedure columns found!")
        st.error("❌ No procedure columns starting with '108-' found in the data!")
        st.error("This means the core calculation cannot be performed.")
        
        # Show available columns for debugging
        st.write("**Available columns in the dataset:**")
        for i, col in enumerate(df.columns):
            st.write(f"{i+1}. {col}")
        
        # Set zero values as fallback
        df['Surgical Procedures'] = 0
        df['total_procedures'] = 0
    
    return df

def process_population_data(pop_df):
    """
    EXACT COLAB LOGIC: Process population data including Buganda consolidation
    """
    if pop_df is None or len(pop_df) == 0:
        print("❌ Empty population dataframe received")
        return pd.DataFrame()
    
    pop_df = pop_df.copy()
    print(f"Processing population data: {pop_df.shape[0]} rows, {pop_df.shape[1]} columns")
    print(f"Original columns: {list(pop_df.columns)}")
    
    # EXACT COLAB LOGIC: Standardize column names
    expected_columns = ['Region', 'Male', 'Female', 'Total']
    if list(pop_df.columns) != expected_columns and len(pop_df.columns) >= 4:
        current_columns = list(pop_df.columns)[:4]
        column_mapping = dict(zip(current_columns, expected_columns))
        pop_df = pop_df.rename(columns=column_mapping)
        print(f"✅ Renamed columns to: {pop_df.columns.tolist()}")

    # Clean the data (EXACT COLAB LOGIC)
    pop_df = pop_df.dropna(how='all')

    # Ensure numeric columns are numeric (EXACT COLAB LOGIC)
    for col in ['Male', 'Female', 'Total']:
        if col in pop_df.columns:
            pop_df[col] = pd.to_numeric(pop_df[col], errors='coerce')

    # Remove Uganda total row (EXACT COLAB LOGIC)
    pop_df = pop_df[pop_df['Region'].str.lower() != 'uganda']

    # Create standardized region name column (EXACT COLAB LOGIC)
    pop_df['Region_Standard'] = pop_df['Region'].str.lower().map(
        lambda x: REGION_MAPPING.get(x, x) if isinstance(x, str) else x
    )

    # CRITICAL: Combine North and South Buganda (EXACT COLAB LOGIC)
    buganda_regions = pop_df[pop_df['Region_Standard'] == 'buganda']

    if len(buganda_regions) > 1:
        print(f"✅ Found {len(buganda_regions)} regions that map to Buganda, combining...")
        
        # Sum the population for all Buganda regions
        buganda_male = buganda_regions['Male'].sum()
        buganda_female = buganda_regions['Female'].sum()
        buganda_total = buganda_regions['Total'].sum()

        # Remove the original Buganda regions
        pop_df = pop_df[pop_df['Region_Standard'] != 'buganda']

        # Add a single combined Buganda row
        buganda_row = pd.DataFrame({
            'Region': ['Buganda'],
            'Male': [buganda_male],
            'Female': [buganda_female],
            'Total': [buganda_total],
            'Region_Standard': ['buganda']
        })

        pop_df = pd.concat([pop_df, buganda_row], ignore_index=True)
        print(f"✅ Combined Buganda population: {buganda_total:,}")

    # Create lookup column for matching
    pop_df['region_lower'] = pop_df['Region_Standard']

    total_population = pop_df['Total'].sum()
    print(f"✅ Processed population data: {len(pop_df)} regions, total: {total_population:,}")
    
    return pop_df

def calculate_national_metrics(df, pop):
    """
    EXACT COLAB LOGIC: Calculate national-level metrics
    """
    print("🔄 Calculating national metrics...")
    
    # Process the data using exact Colab logic
    df_processed = clean_and_process_surgical_data(df)
    pop_processed = process_population_data(pop)
    
    # Calculate total procedures (EXACT COLAB LOGIC)
    total_procedures = df_processed['Surgical Procedures'].sum()
    
    # Calculate reporting facilities (EXACT COLAB LOGIC)
    facilities_with_procedures = df_processed[df_processed['Surgical Procedures'] > 0]
    
    # Get facility identifier column
    if 'orgunitlevel3' in df_processed.columns:
        facility_col = 'orgunitlevel3'
    elif 'Facility Code' in df_processed.columns:
        facility_col = 'Facility Code'
    else:
        facility_col = df_processed.columns[0]
    
    total_facilities = facilities_with_procedures[facility_col].nunique()
    
    # Calculate total population (EXACT COLAB LOGIC)
    if not pop_processed.empty and 'Total' in pop_processed.columns:
        total_population = pop_processed['Total'].sum()
    else:
        total_population = 0
        print("⚠️ No population data available")
    
    # Calculate rate per 100,000 (EXACT COLAB LOGIC)
    if total_population > 0:
        proc_rate = (total_procedures / total_population) * 100_000
    else:
        proc_rate = 0
    
    print(f"✅ NATIONAL METRICS CALCULATED:")
    print(f"   Total procedures: {total_procedures:,}")
    print(f"   Reporting facilities: {total_facilities:,}")
    print(f"   Total population: {total_population:,}")
    print(f"   Rate per 100,000: {proc_rate:.1f}")
    
    return {
        'total_procedures': int(total_procedures),
        'total_facilities': int(total_facilities),
        'total_population': int(total_population),
        'proc_rate': float(proc_rate)
    }

def filter_by_region(df, region):
    """Filter surgical data by region with proper processing"""
    df_processed = clean_and_process_surgical_data(df)
    
    if region == 'All' or 'Region' not in df_processed.columns:
        return df_processed
    
    return df_processed[df_processed['Region'] == region]

def annual_volume_table(df, pop):
    """
    EXACT COLAB LOGIC: Create annual volume table
    """
    print("🔄 Creating annual volume table...")
    
    df_processed = clean_and_process_surgical_data(df)
    pop_processed = process_population_data(pop)
    
    if pop_processed.empty:
        print("❌ Population data is empty after processing")
        return pd.DataFrame()
    
    # Use processed procedure column
    proc_col = 'Surgical Procedures'
    
    # Get facility identifier
    if 'orgunitlevel3' in df_processed.columns:
        facility_col = 'orgunitlevel3'
    else:
        facility_col = df_processed.columns[0]
    
    # Filter to facilities with procedures
    df_with_procedures = df_processed[df_processed[proc_col] > 0]
    
    if 'Region' not in df_processed.columns:
        # No region breakdown
        total_procedures = df_processed[proc_col].sum()
        total_facilities = df_with_procedures[facility_col].nunique()
        total_population = pop_processed['Total'].sum()
        
        agg = pd.DataFrame({
            'Region': ['All Regions'],
            'Surgical Procedures': [total_procedures],
            'Facility Count': [total_facilities],
            'Population': [total_population]
        })
    else:
        # Group by region (EXACT COLAB LOGIC)
        agg = df_processed.groupby(['Region']).agg({
            proc_col: 'sum',
        }).reset_index()
        
        # Count facilities with procedures by region
        facility_counts = df_with_procedures.groupby(['Region'])[facility_col].nunique().reset_index()
        facility_counts.columns = ['Region', 'Facility Count']
        
        # Merge
        agg = agg.merge(facility_counts, on='Region', how='left')
        agg['Facility Count'] = agg['Facility Count'].fillna(0).astype(int)
        agg.columns = ['Region', 'Surgical Procedures', 'Facility Count']
        
        # Add population (EXACT COLAB LOGIC)
        if 'Region' in pop_processed.columns:
            agg = agg.merge(pop_processed[['Region', 'Total']], on='Region', how='left')
            agg = agg.rename(columns={'Total': 'Population'})
            agg['Population'] = agg['Population'].fillna(0)
        else:
            # Use total population proportionally
            total_pop = pop_processed['Total'].sum()
            agg['Population'] = total_pop / len(agg)
    
    # Calculate rates (EXACT COLAB LOGIC)
    agg['Proc Rate/100k'] = np.where(
        agg['Population'] > 0,
        (agg['Surgical Procedures'] / agg['Population'] * 100_000).round(1),
        0
    )
    
    print(f"✅ Annual volume table created: {len(agg)} rows")
    return agg

def procedure_categories_table(df):
    """
    EXACT COLAB LOGIC: Create procedure categories from column names
    """
    print("🔄 Creating procedure categories table...")
    
    df_processed = clean_and_process_surgical_data(df)
    
    # Check if explicit category column exists
    if 'Category' in df_processed.columns:
        result = df_processed.groupby('Category').agg({'Surgical Procedures': 'sum'}).reset_index()
        return result
    
    # EXACT COLAB LOGIC: Create categories from procedure columns
    procedure_cols = identify_procedure_columns(df_processed)
    
    if not procedure_cols:
        print("❌ No procedure columns found for categorization")
        return None
    
    categories = []
    for col in procedure_cols:
        if '-' in col:
            parts = col.split('-', 2)  # Split into max 3 parts
            if len(parts) >= 2:
                # Extract category name from column
                category_name = parts[1].strip()
                # Clean up category name
                category_name = category_name.replace('_', ' ').title()
                # Get count for this procedure
                category_count = df_processed[col].sum()
                
                if category_count > 0:  # Only include non-zero categories
                    categories.append({
                        'Category': category_name,
                        'Surgical Procedures': int(category_count)
                    })
    
    if categories:
        result = pd.DataFrame(categories)
        # Group by category (in case of duplicates)
        result = result.groupby('Category').agg({'Surgical Procedures': 'sum'}).reset_index()
        # Sort by count
        result = result.sort_values('Surgical Procedures', ascending=False)
        print(f"✅ Created {len(result)} procedure categories")
        return result
    
    print("❌ No valid categories could be created")
    return None

def facility_distribution_table(fac):
    """Create facility distribution table with better column detection"""
    if len(fac) == 0:
        print("❌ Empty facility dataframe")
        return None
        
    print(f"🔄 Creating facility distribution table from {len(fac)} facilities")
    
    # Try different possible column combinations
    region_cols = ['Region', 'region', 'REGION', 'orgunitlevel2', 'Region_Name']
    level_cols = ['Facility Level', 'Level', 'level', 'LEVEL', 'facility_level', 'Type', 'Facility_Type']
    
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
        print(f"✅ Using region column: {region_col}, level column: {level_col}")
        result = fac.groupby([region_col, level_col]).size().unstack(fill_value=0)
        return result
    else:
        print(f"❌ Could not find suitable columns. Available: {list(fac.columns)}")
        return None

def district_heatmap_data(df, pop):
    """
    EXACT COLAB LOGIC: Create district heatmap data
    """
    print("🔄 Creating district heatmap data...")
    
    df_processed = clean_and_process_surgical_data(df)
    pop_processed = process_population_data(pop)
    
    if 'District' not in df_processed.columns:
        print("❌ No District column found")
        return None
    
    # Sum procedures by district (EXACT COLAB LOGIC)
    map_df = df_processed.groupby('District').agg({'Surgical Procedures': 'sum'}).reset_index()
    
    # Add population data
    if not pop_processed.empty and 'Total' in pop_processed.columns:
        # Use total population divided by districts as estimate
        total_pop = pop_processed['Total'].sum()
        num_districts = len(map_df)
        avg_district_pop = total_pop / num_districts if num_districts > 0 else 1
        
        map_df['Population'] = avg_district_pop
        
        # Calculate rates
        map_df['Proc Rate/100k'] = np.where(
            map_df['Population'] > 0,
            (map_df['Surgical Procedures'] / map_df['Population'] * 100_000).round(1),
            0
        )
        
        print(f"✅ Created heatmap data for {len(map_df)} districts")
    else:
        print("⚠️ No population data available for rate calculation")
        map_df['Population'] = 0
        map_df['Proc Rate/100k'] = 0
    
    return map_df

def trends_timeseries_data(years, load_func, pop):
    """
    EXACT COLAB LOGIC: Create time series data
    """
    print("🔄 Creating time series data...")
    
    pop_processed = process_population_data(pop)
    
    # Get total population
    if not pop_processed.empty and 'Total' in pop_processed.columns:
        pop_total = pop_processed['Total'].sum()
        print(f"✅ Using total population: {pop_total:,}")
    else:
        pop_total = 1
        print("⚠️ No population data available")
    
    results = []
    
    for year in years:
        try:
            print(f"🔄 Processing year {year}...")
            df_year = load_func(year)
            df_processed = clean_and_process_surgical_data(df_year)
            
            total_procedures = df_processed['Surgical Procedures'].sum()
            rate = (total_procedures / pop_total * 100_000) if pop_total > 0 else 0
            
            results.append({
                'Year': year,
                'Procedures': int(total_procedures),
                'Rate per 100k': round(rate, 1)
            })
            
            print(f"✅ Year {year}: {total_procedures:,} procedures, rate: {rate:.1f}")
            
        except Exception as e:
            print(f"❌ Error processing year {year}: {str(e)}")
            results.append({
                'Year': year,
                'Procedures': 0,
                'Rate per 100k': 0.0
            })
    
    print(f"✅ Time series data created for {len(results)} years")
    return results