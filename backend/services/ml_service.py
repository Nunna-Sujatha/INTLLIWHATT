"""Machine Learning service for electricity bill prediction."""

import os
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, StackingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

from config import MODELS_DIRECTORY, DATASET_PATH

# Model files
STACKING_MODEL_PATH = MODELS_DIRECTORY / "stacking_regressor.joblib"
MLP_MODEL_PATH = MODELS_DIRECTORY / "mlp_model.keras"
MLP_MODEL_PATH_OLD = MODELS_DIRECTORY / "mlp_model.h5"  # Legacy path
SCALER_PATH = MODELS_DIRECTORY / "scaler.joblib"
ENCODERS_PATH = MODELS_DIRECTORY / "encoders.joblib"

# Global variables for loaded models
_stacking_model = None
_mlp_model = None
_scaler = None
_encoders = None
_active_model = "stacking"  # Default model


def load_dataset() -> pd.DataFrame:
    """Load the electricity bill dataset."""
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")
    
    df = pd.read_csv(DATASET_PATH)
    return df


def preprocess_data(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, Dict]:
    """Preprocess data for training."""
    # Features and target
    feature_cols = ['Fan', 'Refrigerator', 'AirConditioner', 'Television', 'Monitor', 
                    'MotorPump', 'Month', 'MonthlyHours', 'TariffRate']
    target_col = 'ElectricityBill'
    
    # Handle categorical columns
    encoders = {}
    df_processed = df.copy()
    
    # Encode City and Company if they exist
    if 'City' in df.columns:
        le_city = LabelEncoder()
        df_processed['City_encoded'] = le_city.fit_transform(df['City'].fillna('Unknown'))
        encoders['City'] = le_city
        feature_cols.append('City_encoded')
    
    if 'Company' in df.columns:
        le_company = LabelEncoder()
        df_processed['Company_encoded'] = le_company.fit_transform(df['Company'].fillna('Unknown'))
        encoders['Company'] = le_company
        feature_cols.append('Company_encoded')
    
    # Extract features and target
    X = df_processed[feature_cols].values
    y = df_processed[target_col].values
    
    return X, y, encoders


def train_stacking_model(X_train: np.ndarray, y_train: np.ndarray) -> StackingRegressor:
    """Train a Stacking Regressor model."""
    # Define base estimators
    base_estimators = [
        ('lr', LinearRegression()),
        ('ridge', Ridge(alpha=1.0)),
        ('rf', RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1))
    ]
    
    # Create stacking regressor
    stacking_model = StackingRegressor(
        estimators=base_estimators,
        final_estimator=Ridge(alpha=0.5),
        cv=3,
        n_jobs=-1
    )
    
    # Fit the model
    stacking_model.fit(X_train, y_train)
    
    return stacking_model


def train_mlp_model(X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray, y_val: np.ndarray):
    """Train an MLP Neural Network model."""
    try:
        from tensorflow import keras
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
        from tensorflow.keras.callbacks import EarlyStopping
        from tensorflow.keras.optimizers import Adam
        
        # Build MLP model
        model = Sequential([
            Dense(128, activation='relu', input_shape=(X_train.shape[1],)),
            BatchNormalization(),
            Dropout(0.3),
            Dense(64, activation='relu'),
            BatchNormalization(),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dense(1)
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        # Early stopping
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )
        
        # Train
        model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=100,
            batch_size=64,
            callbacks=[early_stopping],
            verbose=0
        )
        
        return model
    
    except ImportError:
        print("TensorFlow not available. MLP model training skipped.")
        return None


def train_models(force_retrain: bool = False) -> Dict:
    """Train all ML models."""
    global _stacking_model, _mlp_model, _scaler, _encoders
    
    # Check if models already exist
    if not force_retrain and STACKING_MODEL_PATH.exists() and SCALER_PATH.exists():
        return {"status": "Models already trained. Use force_retrain=True to retrain."}
    
    # Load and preprocess data
    print("Loading dataset...")
    df = load_dataset()
    
    print("Preprocessing data...")
    X, y, encoders = preprocess_data(df)
    
    # Split data
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Stacking Regressor
    print("Training Stacking Regressor...")
    stacking_model = train_stacking_model(X_train_scaled, y_train)
    
    # Evaluate Stacking Regressor
    stacking_preds = stacking_model.predict(X_test_scaled)
    stacking_metrics = {
        "mae": float(mean_absolute_error(y_test, stacking_preds)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, stacking_preds))),
        "r2": float(r2_score(y_test, stacking_preds))
    }
    
    # Train MLP model
    print("Training MLP Neural Network...")
    mlp_model = train_mlp_model(X_train_scaled, y_train, X_val_scaled, y_val)
    
    mlp_metrics = None
    if mlp_model:
        mlp_preds = mlp_model.predict(X_test_scaled).flatten()
        mlp_metrics = {
            "mae": float(mean_absolute_error(y_test, mlp_preds)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, mlp_preds))),
            "r2": float(r2_score(y_test, mlp_preds))
        }
    
    # Save models
    print("Saving models...")
    MODELS_DIRECTORY.mkdir(exist_ok=True)
    
    joblib.dump(stacking_model, STACKING_MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    joblib.dump(encoders, ENCODERS_PATH)
    
    if mlp_model:
        try:
            mlp_model.save(MLP_MODEL_PATH)  # Native Keras format
            # Remove old format if it exists
            if MLP_MODEL_PATH_OLD.exists():
                os.remove(MLP_MODEL_PATH_OLD)
        except Exception as e:
            print(f"Error saving MLP model: {e}")
    
    # Update global variables
    _stacking_model = stacking_model
    _scaler = scaler
    _encoders = encoders
    _mlp_model = mlp_model
    
    return {
        "status": "success",
        "message": "Models trained successfully",
        "stacking_metrics": stacking_metrics,
        "mlp_metrics": mlp_metrics
    }


def load_models() -> bool:
    """Load trained models from disk."""
    global _stacking_model, _mlp_model, _scaler, _encoders
    
    try:
        if STACKING_MODEL_PATH.exists():
            _stacking_model = joblib.load(STACKING_MODEL_PATH)
        
        if SCALER_PATH.exists():
            _scaler = joblib.load(SCALER_PATH)
        
        if ENCODERS_PATH.exists():
            _encoders = joblib.load(ENCODERS_PATH)
        
        # Try loading MLP model from native Keras format first, then legacy H5
        mlp_loaded = False
        for model_path in [MLP_MODEL_PATH, MLP_MODEL_PATH_OLD]:
            if model_path.exists() and not mlp_loaded:
                try:
                    from tensorflow import keras
                    _mlp_model = keras.models.load_model(model_path, compile=False)
                    _mlp_model.compile(optimizer='adam', loss='mse', metrics=['mae'])
                    mlp_loaded = True
                except Exception as e:
                    print(f"Warning: Could not load MLP from {model_path}: {e}")
        
        return True
    except Exception as e:
        print(f"Error loading models: {e}")
        return False


def get_available_models() -> List[Dict]:
    """Get list of available models."""
    models = []
    
    if STACKING_MODEL_PATH.exists():
        models.append({
            "id": "stacking",
            "name": "Stacking Regressor",
            "description": "Ensemble of Linear Regression, Ridge, and Random Forest",
            "status": "ready"
        })
    else:
        models.append({
            "id": "stacking",
            "name": "Stacking Regressor",
            "description": "Ensemble of Linear Regression, Ridge, and Random Forest",
            "status": "not_trained"
        })
    
    if MLP_MODEL_PATH.exists() or MLP_MODEL_PATH_OLD.exists():
        models.append({
            "id": "mlp",
            "name": "MLP Neural Network",
            "description": "Multi-layer Perceptron with 3 hidden layers",
            "status": "ready"
        })
    else:
        models.append({
            "id": "mlp",
            "name": "MLP Neural Network",
            "description": "Multi-layer Perceptron with 3 hidden layers",
            "status": "not_trained"
        })
    
    return models


def set_active_model(model_id: str) -> Dict:
    """Set the active model for predictions."""
    global _active_model
    
    if model_id not in ["stacking", "mlp"]:
        return {"status": "error", "message": "Invalid model ID. Choose 'stacking' or 'mlp'."}
    
    _active_model = model_id
    return {"status": "success", "active_model": model_id}


def get_active_model() -> str:
    """Get the currently active model."""
    return _active_model


def predict_bill(appliance_data: Dict, city: str = "Unknown", company: str = "Unknown", 
                 tariff_rate: float = 8.0, model_id: Optional[str] = None) -> Dict:
    """
    Predict electricity bill based on appliance usage.
    
    appliance_data should contain:
    - fan: number of fans and hours
    - refrigerator: number of refrigerators and hours (usually 24)
    - air_conditioner: number of ACs and hours
    - television: number of TVs and hours
    - monitor: number of monitors and hours
    - motor_pump: number of motor pumps and hours
    - month: month number (1-12)
    """
    global _stacking_model, _mlp_model, _scaler, _encoders, _active_model
    
    # Load models if not loaded
    if _stacking_model is None:
        load_models()
    
    if _stacking_model is None and _mlp_model is None:
        return {"status": "error", "message": "No trained models available. Please train models first."}
    
    # Use specified model or active model
    use_model = model_id if model_id else _active_model
    
    # Extract features from appliance data
    fan_count = appliance_data.get('fan', {}).get('count', 0)
    fridge_hours = appliance_data.get('refrigerator', {}).get('hours', 24)
    ac_count = appliance_data.get('air_conditioner', {}).get('count', 0)
    tv_count = appliance_data.get('television', {}).get('count', 0)
    monitor_count = appliance_data.get('monitor', {}).get('count', 0)
    motor_pump = appliance_data.get('motor_pump', {}).get('count', 0)
    month = appliance_data.get('month', 6)
    
    # Calculate monthly hours based on appliance usage
    # This is a simplified calculation - in reality it would be more complex
    fan_hours = appliance_data.get('fan', {}).get('hours', 8)
    ac_hours = appliance_data.get('air_conditioner', {}).get('hours', 4)
    tv_hours = appliance_data.get('television', {}).get('hours', 4)
    monitor_hours = appliance_data.get('monitor', {}).get('hours', 8)
    motor_hours = appliance_data.get('motor_pump', {}).get('hours', 1)
    
    # Estimate monthly hours (simplified)
    total_daily_hours = (fan_count * fan_hours + fridge_hours + ac_count * ac_hours * 10 + 
                         tv_count * tv_hours + monitor_count * monitor_hours + motor_pump * motor_hours * 5)
    monthly_hours = total_daily_hours * 30 / 10  # Adjustment factor
    
    # Prepare feature vector
    features = [
        fan_count,           # Fan
        fridge_hours,        # Refrigerator (using hours as proxy)
        ac_count,            # AirConditioner
        tv_count,            # Television
        monitor_count,       # Monitor
        motor_pump,          # MotorPump
        month,              # Month
        monthly_hours,       # MonthlyHours
        tariff_rate          # TariffRate
    ]
    
    # Add encoded city and company if encoders exist
    if _encoders:
        if 'City' in _encoders:
            try:
                city_encoded = _encoders['City'].transform([city])[0]
            except ValueError:
                city_encoded = 0
            features.append(city_encoded)
        
        if 'Company' in _encoders:
            try:
                company_encoded = _encoders['Company'].transform([company])[0]
            except ValueError:
                company_encoded = 0
            features.append(company_encoded)
    
    # Scale features
    features_array = np.array([features])
    if _scaler:
        features_scaled = _scaler.transform(features_array)
    else:
        features_scaled = features_array
    
    # Make prediction
    if use_model == "stacking" and _stacking_model:
        prediction = _stacking_model.predict(features_scaled)[0]
        model_used = "Stacking Regressor"
    elif use_model == "mlp" and _mlp_model:
        prediction = _mlp_model.predict(features_scaled)[0][0]
        model_used = "MLP Neural Network"
    elif _stacking_model:
        prediction = _stacking_model.predict(features_scaled)[0]
        model_used = "Stacking Regressor"
    else:
        return {"status": "error", "message": "Selected model not available."}
    
    # Calculate consumption breakdown
    # Power ratings in watts
    power_ratings = {
        'fan': 75,
        'refrigerator': 150,
        'air_conditioner': 1500,
        'television': 100,
        'monitor': 50,
        'motor_pump': 750
    }
    
    consumption_breakdown = {}
    total_kwh = 0
    
    for appliance, rating in power_ratings.items():
        hours = appliance_data.get(appliance, {}).get('hours', 0)
        count = appliance_data.get(appliance, {}).get('count', 0)
        if appliance == 'refrigerator':
            # Respect user's hours/count instead of hardcoding
            hours = appliance_data.get('refrigerator', {}).get('hours', 24)
            count = appliance_data.get('refrigerator', {}).get('count', 1)
        
        kwh = (rating * hours * count * 30) / 1000  # Monthly kWh
        consumption_breakdown[appliance] = {
            "power_rating_w": rating,
            "daily_hours": hours,
            "count": count,
            "monthly_kwh": round(kwh, 2),
            "cost": round(kwh * tariff_rate, 2)
        }
        total_kwh += kwh
    
    return {
        "status": "success",
        "predicted_bill": round(float(prediction), 2),
        "model_used": model_used,
        "estimated_consumption_kwh": round(total_kwh, 2),
        "tariff_rate": tariff_rate,
        "consumption_breakdown": consumption_breakdown,
        "input_summary": {
            "city": city,
            "company": company,
            "month": month,
            "total_appliances": fan_count + ac_count + tv_count + monitor_count + motor_pump + 1  # +1 for fridge
        }
    }


# Initialize by trying to load existing models
load_models()
