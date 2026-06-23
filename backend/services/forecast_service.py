"""Forecasting service for predicting future electricity bills."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np

from services.data_service import get_historical_data, get_appliances


def calculate_seasonal_factor(month: int) -> float:
    """Calculate seasonal factor for electricity consumption."""
    # Higher consumption in summer (Apr-Jun) and winter (Dec-Feb)
    seasonal_factors = {
        1: 1.15,   # January - Winter heating
        2: 1.10,   # February
        3: 1.0,    # March
        4: 1.20,   # April - Summer starts
        5: 1.35,   # May - Peak summer
        6: 1.40,   # June - Peak summer
        7: 1.30,   # July - Monsoon
        8: 1.20,   # August
        9: 1.10,   # September
        10: 1.0,   # October
        11: 1.05,  # November
        12: 1.15   # December - Winter
    }
    return seasonal_factors.get(month, 1.0)


def estimate_current_consumption(appliances: List[Dict], tariff_rate: float = 8.0) -> Dict:
    """Estimate current monthly consumption based on appliances."""
    total_kwh = 0
    breakdown = {}
    
    for app in appliances:
        power_w = app.get('power_rating', 0)
        hours = app.get('average_daily_hours', 0)
        qty = app.get('quantity', 1)
        
        monthly_kwh = (power_w * hours * qty * 30) / 1000
        breakdown[app.get('name', 'Unknown')] = {
            'monthly_kwh': round(monthly_kwh, 2),
            'monthly_cost': round(monthly_kwh * tariff_rate, 2)
        }
        total_kwh += monthly_kwh
    
    return {
        'total_kwh': round(total_kwh, 2),
        'total_cost': round(total_kwh * tariff_rate, 2),
        'breakdown': breakdown
    }


def simple_moving_average(data: List[float], window: int = 3) -> float:
    """Calculate simple moving average."""
    if len(data) < window:
        return np.mean(data) if data else 0
    return np.mean(data[-window:])


def exponential_smoothing(data: List[float], alpha: float = 0.3) -> float:
    """Apply exponential smoothing for forecasting."""
    if not data:
        return 0
    
    result = data[0]
    for value in data[1:]:
        result = alpha * value + (1 - alpha) * result
    return result


def calculate_trend(data: List[float]) -> float:
    """Calculate trend (rate of change) from historical data."""
    if len(data) < 2:
        return 0
    
    # Simple linear regression slope
    x = np.arange(len(data))
    y = np.array(data)
    
    n = len(data)
    slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x**2) - np.sum(x)**2)
    
    return slope


def forecast_months(
    num_months: int,
    base_consumption: float,
    tariff_rate: float = 8.0,
    historical_bills: Optional[List[float]] = None,
    start_month: Optional[int] = None
) -> Dict:
    """
    Forecast electricity bills for specified number of months.
    
    Args:
        num_months: Number of months to forecast
        base_consumption: Base monthly consumption in kWh
        tariff_rate: Electricity tariff rate per kWh
        historical_bills: Optional list of historical bill amounts
        start_month: Starting month for forecast (1-12)
    
    Returns:
        Dictionary with forecast details
    """
    if start_month is None:
        start_month = datetime.now().month
    
    forecasts = []
    current_month = start_month
    
    # Calculate trend from historical data if available
    trend = 0
    base_value = base_consumption
    
    if historical_bills and len(historical_bills) >= 3:
        trend = calculate_trend(historical_bills)
        # Use exponential smoothing for base value
        base_value = exponential_smoothing(historical_bills)
        # Convert from bill amount to kWh
        base_value = base_value / tariff_rate
    
    for i in range(num_months):
        forecast_month = ((current_month - 1 + i) % 12) + 1
        forecast_date = datetime.now() + timedelta(days=30 * (i + 1))
        
        # Apply seasonal factor
        seasonal_factor = calculate_seasonal_factor(forecast_month)
        
        # Apply trend
        trend_adjustment = trend * (i + 1) / tariff_rate  # Convert to kWh
        
        # Calculate forecasted consumption
        forecasted_kwh = (base_value + trend_adjustment) * seasonal_factor
        forecasted_kwh = max(0, forecasted_kwh)  # Ensure non-negative
        
        # Calculate bill amount
        forecasted_bill = forecasted_kwh * tariff_rate
        
        # Calculate confidence interval (wider for further forecasts)
        confidence_width = 0.1 + (0.05 * i)  # 10% base, +5% per month
        lower_bound = forecasted_bill * (1 - confidence_width)
        upper_bound = forecasted_bill * (1 + confidence_width)
        
        forecasts.append({
            'month': forecast_month,
            'month_name': datetime(2000, forecast_month, 1).strftime('%B'),
            'year': forecast_date.year,
            'forecasted_kwh': round(forecasted_kwh, 2),
            'forecasted_bill': round(forecasted_bill, 2),
            'lower_bound': round(lower_bound, 2),
            'upper_bound': round(upper_bound, 2),
            'confidence': round((1 - confidence_width) * 100, 1),
            'seasonal_factor': seasonal_factor
        })
    
    # Calculate summary statistics
    total_forecasted = sum(f['forecasted_bill'] for f in forecasts)
    avg_monthly = total_forecasted / num_months if num_months > 0 else 0
    
    return {
        'status': 'success',
        'forecast_period': f'{num_months} months',
        'start_date': datetime.now().strftime('%Y-%m-%d'),
        'tariff_rate': tariff_rate,
        'base_consumption_kwh': round(base_value, 2),
        'trend_detected': 'increasing' if trend > 0 else ('decreasing' if trend < 0 else 'stable'),
        'forecasts': forecasts,
        'summary': {
            'total_forecasted_bill': round(total_forecasted, 2),
            'average_monthly_bill': round(avg_monthly, 2),
            'min_monthly': round(min(f['forecasted_bill'] for f in forecasts), 2),
            'max_monthly': round(max(f['forecasted_bill'] for f in forecasts), 2)
        }
    }


def get_3_month_forecast(tariff_rate: float = 8.0) -> Dict:
    """Get 3-month electricity bill forecast."""
    # Get current appliances
    appliances = get_appliances()
    current = estimate_current_consumption(appliances, tariff_rate)
    
    # Get historical data
    history = get_historical_data()
    historical_bills = [h.get('total_bill', 0) for h in history if h.get('total_bill')]
    
    return forecast_months(
        num_months=3,
        base_consumption=current['total_kwh'],
        tariff_rate=tariff_rate,
        historical_bills=historical_bills
    )


def get_6_month_forecast(tariff_rate: float = 8.0) -> Dict:
    """Get 6-month electricity bill forecast."""
    # Get current appliances
    appliances = get_appliances()
    current = estimate_current_consumption(appliances, tariff_rate)
    
    # Get historical data
    history = get_historical_data()
    historical_bills = [h.get('total_bill', 0) for h in history if h.get('total_bill')]
    
    return forecast_months(
        num_months=6,
        base_consumption=current['total_kwh'],
        tariff_rate=tariff_rate,
        historical_bills=historical_bills
    )


def get_custom_forecast(
    num_months: int,
    tariff_rate: float = 8.0,
    custom_consumption: Optional[float] = None
) -> Dict:
    """Get custom period forecast."""
    # Validate input
    if num_months < 1 or num_months > 24:
        return {
            'status': 'error',
            'message': 'Forecast period must be between 1 and 24 months'
        }
    
    # Get base consumption
    if custom_consumption:
        base_kwh = custom_consumption
    else:
        appliances = get_appliances()
        current = estimate_current_consumption(appliances, tariff_rate)
        base_kwh = current['total_kwh']
    
    # Get historical data
    history = get_historical_data()
    historical_bills = [h.get('total_bill', 0) for h in history if h.get('total_bill')]
    
    return forecast_months(
        num_months=num_months,
        base_consumption=base_kwh,
        tariff_rate=tariff_rate,
        historical_bills=historical_bills
    )


def get_yearly_projection(tariff_rate: float = 8.0) -> Dict:
    """Get yearly projection with monthly breakdown."""
    forecast = get_custom_forecast(12, tariff_rate)
    
    if forecast['status'] != 'success':
        return forecast
    
    # Add yearly summary
    forecasts = forecast['forecasts']
    
    # Group by quarters
    q1 = sum(f['forecasted_bill'] for f in forecasts[:3])
    q2 = sum(f['forecasted_bill'] for f in forecasts[3:6])
    q3 = sum(f['forecasted_bill'] for f in forecasts[6:9])
    q4 = sum(f['forecasted_bill'] for f in forecasts[9:12])
    
    forecast['quarterly_summary'] = {
        'Q1': round(q1, 2),
        'Q2': round(q2, 2),
        'Q3': round(q3, 2),
        'Q4': round(q4, 2)
    }
    
    # Find peak and low months
    sorted_forecasts = sorted(forecasts, key=lambda x: x['forecasted_bill'])
    forecast['peak_months'] = [f['month_name'] for f in sorted_forecasts[-3:]]
    forecast['low_months'] = [f['month_name'] for f in sorted_forecasts[:3]]
    
    return forecast


def compare_with_history(forecast: Dict) -> Dict:
    """Compare forecast with historical data."""
    history = get_historical_data()
    
    if not history:
        return {
            'status': 'warning',
            'message': 'No historical data available for comparison',
            'forecast': forecast
        }
    
    # Calculate historical averages
    historical_bills = [h.get('total_bill', 0) for h in history if h.get('total_bill')]
    historical_avg = np.mean(historical_bills) if historical_bills else 0
    
    # Compare with forecast
    forecast_avg = forecast.get('summary', {}).get('average_monthly_bill', 0)
    
    change_percent = ((forecast_avg - historical_avg) / historical_avg * 100) if historical_avg else 0
    
    return {
        'status': 'success',
        'historical_average': round(historical_avg, 2),
        'forecasted_average': round(forecast_avg, 2),
        'change_percent': round(change_percent, 1),
        'trend': 'increasing' if change_percent > 5 else ('decreasing' if change_percent < -5 else 'stable'),
        'historical_data_points': len(historical_bills),
        'forecast': forecast
    }
