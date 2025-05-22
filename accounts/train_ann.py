import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import re
import os

# File paths
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'ann_model.h5')
SCALER_PATH = os.path.join(os.path.dirname(__file__), 'scaler.npy')
DATA_PATH = os.path.join(os.path.dirname(__file__), 'training_data.csv')   # Replace with your actual file path

# Load and preprocess data
df = pd.read_csv(DATA_PATH)

# Feature engineering
df['username_length'] = df['username'].apply(lambda x: len(str(x)))
df['has_numbers'] = df['username'].apply(lambda x: int(bool(re.search(r'\d', str(x)))))
df['bio_length'] = df['bio'].apply(lambda x: len(str(x)))
df['has_link'] = df['bio'].apply(lambda x: int('http' in str(x).lower() or 'www' in str(x).lower()))
df['is_empty_bio'] = df['bio'].apply(lambda x: int(len(str(x).strip()) == 0))

# Drop text fields
df = df.drop(columns=['username', 'bio'])

# Features and labels
X = df.drop(columns=['fake'])
y = df['fake']

# Scale the features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
np.save(SCALER_PATH, [scaler.mean_, scaler.scale_])

# Model builder
def build_model(input_dim):
    model = Sequential([
        Dense(64, activation='relu', input_dim=input_dim),
        Dropout(0.3),
        Dense(32, activation='relu'),
        Dropout(0.2),
        Dense(2, activation='softmax')
    ])
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    return model

# K-Fold Cross Validation
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
val_scores = []

for fold, (train_idx, val_idx) in enumerate(skf.split(X_scaled, y)):
    print(f'\nFold {fold+1}')
    X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
    y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

    model = build_model(X_train.shape[1])
    callbacks = [
        EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
        ModelCheckpoint(MODEL_PATH, monitor='val_loss', save_best_only=True)
    ]

    model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=100, batch_size=32, callbacks=callbacks, verbose=0)
    val_pred = np.argmax(model.predict(X_val), axis=1)
    acc = accuracy_score(y_val, val_pred)
    val_scores.append(acc)
    print(f'Accuracy: {acc:.4f}')
    print(classification_report(y_val, val_pred))
    print(confusion_matrix(y_val, val_pred))

print(f"\nAverage Accuracy: {np.mean(val_scores):.4f}")

# Final model on full data
final_model = build_model(X_scaled.shape[1])
final_model.fit(X_scaled, y, epochs=100, batch_size=32, callbacks=[EarlyStopping(monitor='loss', patience=10, restore_best_weights=True)], verbose=1)
final_model.save(MODEL_PATH)
print("\n✅ Model and scaler saved.")
