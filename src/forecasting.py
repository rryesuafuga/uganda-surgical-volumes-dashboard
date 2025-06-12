# src/forecasting.py
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

def forecast_procedure_rate(ts_df, steps=6):
    """
    Forecast the procedures per 100,000 rate using Holt-Winters Exponential Smoothing for 2025–2030.
    ts_df: DataFrame with columns ['Year', 'Rate per 100k']
    steps: Number of years to forecast (default 6: 2025–2030)
    Returns a DataFrame with forecasted years and values.
    """
    ts = ts_df.set_index('Year')['Rate per 100k']
    model = ExponentialSmoothing(ts, trend='add', seasonal=None, initialization_method="estimated")
    fit = model.fit()
    forecast = fit.forecast(steps)
    forecast_years = list(range(ts.index.max()+1, ts.index.max()+1+steps))
    forecast_df = pd.DataFrame({'Year': forecast_years, 'Rate per 100k': forecast.values})
    return forecast_df
