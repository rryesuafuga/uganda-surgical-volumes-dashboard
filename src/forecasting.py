# src/forecasting.py (FIXED - Complete Implementation)
import pandas as pd
import numpy as np
import streamlit as st

def forecast_procedure_rate(ts_df, steps=6):
    """
    Forecast the procedures per 100,000 rate using Holt-Winters Exponential Smoothing for 2025–2030.
    FIXED to handle edge cases and ensure proper data output
    
    ts_df: DataFrame with columns ['Year', 'Rate per 100k']
    steps: Number of years to forecast (default 6: 2025–2030)
    Returns a DataFrame with forecasted years and values.
    """
    try:
        print(f"🔄 Starting forecast with {len(ts_df)} data points")
        print(f"Input data:\n{ts_df}")
        
        # Validate input data
        if len(ts_df) < 2:
            print("❌ Insufficient data for forecasting (need at least 2 points)")
            # Return simple linear projection as fallback
            if len(ts_df) == 1:
                base_rate = ts_df['Rate per 100k'].iloc[0]
                growth_rate = 0.05  # Assume 5% annual growth
            else:
                return pd.DataFrame()  # No data to work with
        else:
            # Calculate simple growth rate as fallback
            first_rate = ts_df['Rate per 100k'].iloc[0]
            last_rate = ts_df['Rate per 100k'].iloc[-1]
            years_span = ts_df['Year'].iloc[-1] - ts_df['Year'].iloc[0]
            
            if years_span > 0 and first_rate > 0:
                growth_rate = (last_rate / first_rate) ** (1/years_span) - 1
            else:
                growth_rate = 0.05  # Default 5% growth
            
            base_rate = last_rate
        
        print(f"✅ Baseline rate: {base_rate:.1f}, Growth rate: {growth_rate:.3f}")
        
        # Try advanced forecasting first
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            
            # Prepare time series
            ts = ts_df.set_index('Year')['Rate per 100k']
            
            # Fit Holt-Winters model
            model = ExponentialSmoothing(
                ts, 
                trend='add', 
                seasonal=None, 
                initialization_method="estimated"
            )
            fit = model.fit()
            
            # Generate forecast
            forecast = fit.forecast(steps)
            forecast_years = list(range(ts.index.max() + 1, ts.index.max() + 1 + steps))
            
            forecast_df = pd.DataFrame({
                'Year': forecast_years,
                'Procedures': ['None'] * steps,  # Match the dashboard format
                'Rate per 100k': forecast.values.round(4)  # Higher precision as shown in dashboard
            })
            
            print(f"✅ Advanced forecasting successful")
            print(f"Forecast data:\n{forecast_df}")
            
            return forecast_df
            
        except ImportError:
            print("⚠️ statsmodels not available, using simple projection")
        except Exception as e:
            print(f"⚠️ Advanced forecasting failed: {str(e)}, using simple projection")
        
        # Fallback: Simple exponential growth projection
        forecast_years = list(range(ts_df['Year'].max() + 1, ts_df['Year'].max() + 1 + steps))
        forecast_values = []
        
        current_rate = base_rate
        for i in range(steps):
            current_rate *= (1 + growth_rate)
            forecast_values.append(current_rate)
        
        forecast_df = pd.DataFrame({
            'Year': forecast_years,
            'Procedures': ['None'] * steps,  # Match dashboard format
            'Rate per 100k': [round(val, 4) for val in forecast_values]  # Match precision
        })
        
        print(f"✅ Simple projection completed")
        print(f"Forecast data:\n{forecast_df}")
        
        return forecast_df
        
    except Exception as e:
        print(f"❌ Forecasting failed completely: {str(e)}")
        st.error(f"Forecasting error: {str(e)}")
        
        # Return empty forecast as last resort
        return pd.DataFrame({
            'Year': [],
            'Procedures': [],
            'Rate per 100k': []
        })

def validate_time_series_data(ts_df):
    """
    Validate time series data before forecasting
    """
    issues = []
    
    if ts_df is None or len(ts_df) == 0:
        issues.append("Time series data is empty")
        return issues
    
    required_columns = ['Year', 'Rate per 100k']
    missing_columns = [col for col in required_columns if col not in ts_df.columns]
    if missing_columns:
        issues.append(f"Missing columns: {missing_columns}")
    
    if 'Rate per 100k' in ts_df.columns:
        if ts_df['Rate per 100k'].isna().all():
            issues.append("All rate values are NaN")
        elif ts_df['Rate per 100k'].sum() == 0:
            issues.append("All rate values are zero")
    
    if 'Year' in ts_df.columns:
        if len(ts_df['Year'].unique()) != len(ts_df):
            issues.append("Duplicate years in data")
    
    return issues

def create_enhanced_forecast_table(ts_df, forecast_df):
    """
    Create an enhanced forecast table that matches the dashboard format exactly
    """
    try:
        # Combine observed and forecasted data
        ts_all = pd.concat([ts_df, forecast_df], ignore_index=True)
        
        # Add row numbers to match dashboard
        ts_all.insert(0, '', range(1, len(ts_all) + 1))
        
        # Ensure proper formatting
        if 'Rate per 100k' in ts_all.columns:
            ts_all['Rate per 100k'] = ts_all['Rate per 100k'].round(4)
        
        # Replace None with proper None values for procedures
        if 'Procedures' in ts_all.columns:
            ts_all['Procedures'] = ts_all['Procedures'].replace('None', None)
        
        return ts_all
        
    except Exception as e:
        print(f"❌ Error creating enhanced forecast table: {str(e)}")
        return ts_df