# src/data_processing.py
def filter_by_region(df, region):
    if region == 'All' or 'Region' not in df.columns:
        return df
    return df[df['Region'] == region]

def annual_volume_table(df, pop):
    agg = df.groupby(['Region']).agg({
        'Surgical Procedures': 'sum',
        'Facility Code': 'nunique',
    }).reset_index()
    agg = agg.merge(pop[['Region', 'Population']], on='Region', how='left')
    agg['Proc Rate/100k'] = agg['Surgical Procedures'] / agg['Population'] * 100_000
    return agg

def procedure_categories_table(df):
    if 'Category' in df.columns:
        return df.groupby('Category').agg({'Surgical Procedures': 'sum'}).reset_index()
    else:
        return None

def facility_distribution_table(fac):
    if 'Region' in fac.columns and 'Facility Level' in fac.columns:
        return fac.groupby(['Region', 'Facility Level']).size().unstack(fill_value=0)
    else:
        return None

def district_heatmap_data(df, pop):
    if 'District' in df.columns:
        map_df = df.groupby('District').agg({'Surgical Procedures': 'sum'}).reset_index()
        map_df = map_df.merge(pop[['District', 'Population']], on='District', how='left')
        map_df['Proc Rate/100k'] = map_df['Surgical Procedures'] / map_df['Population'] * 100_000
        return map_df
    else:
        return None

def trends_timeseries_data(years, load_func, pop):
    dfs = []
    for y in years:
        df_y = load_func(y)
        total = df_y['Surgical Procedures'].sum() if 'Surgical Procedures' in df_y.columns else df_y.iloc[:,1].sum()
        pop_total = pop['Population'].sum()
        rate = total / pop_total * 100_000
        dfs.append({'Year': y, 'Procedures': total, 'Rate per 100k': rate})
    return dfs
