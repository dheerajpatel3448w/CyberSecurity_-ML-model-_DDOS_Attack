import json
import joblib
import numpy as np
import pandas as pd
from confluent_kafka import Consumer

print("Loading Machine Learning assets...")
try:
    model = joblib.load('lgbm_model.pkl')
    expected_columns = joblib.load('selected_column_names.pkl')
    encoder = joblib.load('encoder.pkl') 
    print("✅ Model, Columns, and Encoder loaded successfully.")
except Exception as e:
    print(f"❌ Error loading .pkl files: {e}")
    exit(1)

conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'ml-inference-group',
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(conf)
consumer.subscribe(['network-traffic'])

print("🎧 Listening to Kafka topic 'network-traffic'...")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None or msg.error():
            continue

        raw_json_data = json.loads(msg.value().decode('utf-8'))

        # Align columns exactly as LightGBM expects
        aligned_features = []
        for col_name in expected_columns:
            val = raw_json_data.get(col_name, 0.0)
            try:
                aligned_features.append(float(val))
            except ValueError:
                aligned_features.append(0.0)

    # Convert to a Pandas DataFrame so the model gets the column names it expects
        X_live = pd.DataFrame([aligned_features], columns=expected_columns)

        # Predict
        prediction_num = model.predict(X_live)[0]
        attack_type = encoder.inverse_transform([prediction_num])[0]
        confidence = model.predict_proba(X_live)[0].max() * 100

        if "Normal" not in str(attack_type) and "BENIGN" not in str(attack_type):
            print(f"🚨 [ALERT] Threat Detected: {attack_type} | Confidence: {confidence:.2f}%")
        else:
            print(f"✅ [OK] Normal Traffic | Confidence: {confidence:.2f}%", end='\r')

except KeyboardInterrupt:
    print("\n🛑 Shutting down ML Consumer...")
finally:
    consumer.close()