"""
Electricity Bill Prediction - Model Training Script

This script trains the ML models for electricity bill prediction.
Run this script when deploying to a new system to train fresh models.

Usage:
    python train_models.py
    python train_models.py --force  # Force retrain even if models exist
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, StackingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

# Configuration
SCRIPT_DIR = Path(__file__).parent
MODELS_DIR = SCRIPT_DIR / "models"
DATASET_PATH = SCRIPT_DIR.parent / "electricity_bill_dataset.csv"

# Create models directory if it doesn't exist
MODELS_DIR.mkdir(exist_ok=True)


def print_header():
    """Print script header."""
    print("\n" + "=" * 60)
    print("   Electricity Bill Prediction - Model Training")
    print("=" * 60 + "\n")


def load_dataset():
    """Load the electricity bill dataset."""
    if not DATASET_PATH.exists():
        print(f"❌ Dataset not found at: {DATASET_PATH}")
        print("\nMake sure the 'electricity_bill_dataset.csv' file is in the project root.")
        sys.exit(1)
    
    print(f"📂 Loading dataset from: {DATASET_PATH}")
    df = pd.read_csv(DATASET_PATH)
    print(f"   ✓ Loaded {len(df):,} records with {len(df.columns)} features")
    return df


def preprocess_data(df):
    """Preprocess data for training."""
    print("\n🔧 Preprocessing data...")
    
    # Features and target
    feature_cols = ['Fan', 'Refrigerator', 'AirConditioner', 'Television', 'Monitor', 
                    'MotorPump', 'Month', 'MonthlyHours', 'TariffRate']
    target_col = 'ElectricityBill'
    
    # Handle categorical columns
    encoders = {}
    df_processed = df.copy()
    
    # Encode City if it exists
    if 'City' in df.columns:
        le_city = LabelEncoder()
        df_processed['City_encoded'] = le_city.fit_transform(df['City'].fillna('Unknown'))
        encoders['City'] = le_city
        feature_cols.append('City_encoded')
        print(f"   ✓ Encoded 'City' column ({len(le_city.classes_)} unique values)")
    
    # Encode Company if it exists
    if 'Company' in df.columns:
        le_company = LabelEncoder()
        df_processed['Company_encoded'] = le_company.fit_transform(df['Company'].fillna('Unknown'))
        encoders['Company'] = le_company
        feature_cols.append('Company_encoded')
        print(f"   ✓ Encoded 'Company' column ({len(le_company.classes_)} unique values)")
    
    # Extract features and target
    X = df_processed[feature_cols].values
    y = df_processed[target_col].values
    
    print(f"   ✓ Feature matrix shape: {X.shape}")
    print(f"   ✓ Target shape: {y.shape}")
    
    return X, y, encoders


def train_stacking_model(X_train, y_train):
    """Train a Stacking Regressor model."""
    print("\n🤖 Training Stacking Regressor...")
    
    # Define base estimators
    base_estimators = [
        ('lr', LinearRegression()),
        ('ridge', Ridge(alpha=1.0)),
        ('rf', RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1))
    ]
    
    print("   Base models:")
    print("   • Linear Regression")
    print("   • Ridge Regression (α=1.0)")
    print("   • Random Forest (50 trees, max_depth=10)")
    print("   • Meta-learner: Ridge Regression (α=0.5)")
    
    # Create stacking regressor
    stacking_model = StackingRegressor(
        estimators=base_estimators,
        final_estimator=Ridge(alpha=0.5),
        cv=3,
        n_jobs=-1
    )
    
    # Fit the model
    print("   Training in progress...")
    stacking_model.fit(X_train, y_train)
    print("   ✓ Training complete!")
    
    return stacking_model


def train_mlp_model(X_train, y_train, X_val, y_val):
    """Train an MLP Neural Network model."""
    print("\n🧠 Training MLP Neural Network...")
    
    try:
        import tensorflow as tf
        from tensorflow import keras
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
        from tensorflow.keras.callbacks import EarlyStopping
        from tensorflow.keras.optimizers import Adam
        
        # Suppress TensorFlow warnings
        tf.get_logger().setLevel('ERROR')
        
        print("   Architecture:")
        print("   • Input Layer → 128 neurons (ReLU)")
        print("   • BatchNorm + Dropout (0.3)")
        print("   • Hidden Layer → 64 neurons (ReLU)")
        print("   • BatchNorm + Dropout (0.2)")
        print("   • Hidden Layer → 32 neurons (ReLU)")
        print("   • Output Layer → 1 neuron")
        
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
            restore_best_weights=True,
            verbose=0
        )
        
        # Train
        print("   Training in progress (max 100 epochs with early stopping)...")
        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=100,
            batch_size=64,
            callbacks=[early_stopping],
            verbose=0
        )
        
        epochs_trained = len(history.history['loss'])
        print(f"   ✓ Training complete! (stopped at epoch {epochs_trained})")
        
        return model
    
    except ImportError:
        print("   ⚠️ TensorFlow not installed. Skipping MLP model.")
        print("   To enable MLP, install TensorFlow: pip install tensorflow")
        return None


def evaluate_model(model, X_test, y_test, model_name):
    """Evaluate a trained model."""
    if hasattr(model, 'predict'):
        predictions = model.predict(X_test)
        if len(predictions.shape) > 1:
            predictions = predictions.flatten()
        
        mae = mean_absolute_error(y_test, predictions)
        rmse = np.sqrt(mean_squared_error(y_test, predictions))
        r2 = r2_score(y_test, predictions)
        
        return {"mae": mae, "rmse": rmse, "r2": r2}
    return None


def print_metrics(metrics, model_name):
    """Print model metrics."""
    print(f"\n📊 {model_name} Performance:")
    print(f"   • MAE  (Mean Absolute Error):  ₹{metrics['mae']:,.2f}")
    print(f"   • RMSE (Root Mean Sq Error):   ₹{metrics['rmse']:,.2f}")
    print(f"   • R²   (Coefficient of Det):   {metrics['r2']:.4f} ({metrics['r2']*100:.2f}%)")


def main():
    parser = argparse.ArgumentParser(description='Train electricity bill prediction models')
    parser.add_argument('--force', action='store_true', help='Force retrain even if models exist')
    args = parser.parse_args()
    
    print_header()
    
    # Check if models already exist
    stacking_path = MODELS_DIR / "stacking_regressor.joblib"
    scaler_path = MODELS_DIR / "scaler.joblib"
    encoders_path = MODELS_DIR / "encoders.joblib"
    mlp_path = MODELS_DIR / "mlp_model.keras"
    
    if stacking_path.exists() and scaler_path.exists() and not args.force:
        print("⚠️ Models already exist!")
        print(f"   Location: {MODELS_DIR}")
        print("\n   To force retrain, run: python train_models.py --force")
        print("   To skip training and use existing models, just start the server.")
        sys.exit(0)
    
    # Load and preprocess data
    df = load_dataset()
    X, y, encoders = preprocess_data(df)
    
    # Split data
    print("\n📊 Splitting data...")
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)
    print(f"   ✓ Training set:   {len(X_train):,} samples (70%)")
    print(f"   ✓ Validation set: {len(X_val):,} samples (15%)")
    print(f"   ✓ Test set:       {len(X_test):,} samples (15%)")
    
    # Scale features
    print("\n⚖️ Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    print("   ✓ StandardScaler fitted and applied")
    
    # Train Stacking Regressor
    stacking_model = train_stacking_model(X_train_scaled, y_train)
    stacking_metrics = evaluate_model(stacking_model, X_test_scaled, y_test, "Stacking Regressor")
    if stacking_metrics:
        print_metrics(stacking_metrics, "Stacking Regressor")
    
    # Train MLP model
    mlp_model = train_mlp_model(X_train_scaled, y_train, X_val_scaled, y_val)
    if mlp_model:
        mlp_metrics = evaluate_model(mlp_model, X_test_scaled, y_test, "MLP Neural Network")
        if mlp_metrics:
            print_metrics(mlp_metrics, "MLP Neural Network")
    
    # Save models
    print("\n💾 Saving models...")
    
    joblib.dump(stacking_model, stacking_path)
    print(f"   ✓ Stacking Regressor → {stacking_path.name}")
    
    joblib.dump(scaler, scaler_path)
    print(f"   ✓ Scaler → {scaler_path.name}")
    
    joblib.dump(encoders, encoders_path)
    print(f"   ✓ Encoders → {encoders_path.name}")
    
    if mlp_model:
        mlp_model.save(mlp_path)
        print(f"   ✓ MLP Model → {mlp_path.name}")
    
    # Summary
    print("\n" + "=" * 60)
    print("   ✅ Training Complete!")
    print("=" * 60)
    print(f"\n📁 Models saved to: {MODELS_DIR}")
    print("\n🚀 Next steps:")
    print("   1. Start the backend: python main.py")
    print("   2. Start the frontend: npm run dev (in frontend folder)")
    print("   3. Open http://localhost:5173 in your browser")
    print()


if __name__ == "__main__":
    main()
