# 🛡️ Real-Time Network Intrusion Detection System

> A high-throughput, ML-powered cybersecurity pipeline that ingests live network traffic via **Apache Kafka**, classifies each flow as **Benign or a specific attack type** using a trained **LightGBM** model, and raises real-time threat alerts — all at scale.

---

## 📌 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Dataset](#dataset)
- [Machine Learning Model](#machine-learning-model)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Setup & Installation](#setup--installation)
  - [Prerequisites](#prerequisites)
  - [Phase 1 — ML Training (Python)](#phase-1--ml-training-python)
  - [Phase 2 — Kafka Stream Producer (Node.js)](#phase-2--kafka-stream-producer-nodejs)
  - [Phase 3 — ML Inference Consumer (Python)](#phase-3--ml-inference-consumer-python)
- [How It Works](#how-it-works)
- [Model Artifacts](#model-artifacts)
- [Results & Performance](#results--performance)
- [Future Roadmap](#future-roadmap)

---

## Overview

Traditional intrusion detection systems (IDS) rely on static rule-based engines that fail against novel, zero-day attack vectors. This project replaces that paradigm with a **streaming ML inference pipeline** that:

1. **Simulates a real-world network sensor** — a Node.js producer reads the CICIDS2017 dataset (686 MB of real network flow data) and publishes each row as a JSON message to a Kafka topic.
2. **Processes events in real time** — a Python Kafka consumer polls messages, preprocesses each packet's 80+ features, and passes them to a trained LightGBM classifier.
3. **Classifies each packet instantly** — the model predicts whether traffic is `BENIGN` or a specific attack category (DDoS, PortScan, BruteForce, etc.) and prints a `🚨 ALERT` with confidence score.

This architecture mirrors production IDS pipelines used in enterprise SOC (Security Operations Center) environments.

---

## Architecture

```
┌──────────────────────┐         Kafka Topic          ┌───────────────────────────┐
│   Node.js Producer   │  ──── network-traffic ────►  │   Python ML Consumer      │
│  (cyberAttack/)      │    (JSON-encoded packets)     │   (cisco2017/main.py)     │
│                      │                               │                           │
│  • Reads CICIDS2017  │                               │  • Loads LightGBM model   │
│    CSV (~686 MB)     │                               │  • Aligns 80+ features    │
│  • Streams rows to   │                               │  • Predicts attack type   │
│    Kafka broker at   │                               │  • Prints live alerts     │
│    localhost:9092    │                               │    with confidence %      │
└──────────────────────┘                               └───────────────────────────┘
         │                                                          │
         ▼                                                          ▼
  Apache Kafka Broker                                    LightGBM Classifier
  (localhost:9092)                                       lgbm_model.pkl (2.4 MB)
```

---

## Dataset

**[CICIDS2017 — Canadian Institute for Cybersecurity](https://www.unb.ca/cic/datasets/ids-2017.html)**

| Property | Value |
|---|---|
| Source | University of New Brunswick (UNB) |
| Size | ~686 MB (cleaned CSV) |
| Features | 80+ network flow attributes |
| Attack Types | DDoS, PortScan, BruteForce, DoS Hulk, DoS GoldenEye, Infiltration, Web Attack, Heartbleed |
| Label Column | `Label` (BENIGN / attack name) |

**Key features used for classification:**
- `Flow Duration`, `Total Fwd Packets`, `Total Backward Packets`
- `Fwd Packet Length Max/Min/Mean/Std`
- `Flow Bytes/s`, `Flow Packets/s`
- `Flow IAT Mean`, `SYN Flag Count`, `RST Flag Count`
- `Init_Win_bytes_forward`, `act_data_pkt_fwd`, and 70+ more

---

## Machine Learning Model

| Property | Detail |
|---|---|
| **Algorithm** | LightGBM (Gradient Boosted Decision Trees) |
| **Task** | Multi-class classification |
| **Preprocessing** | StandardScaler (feature normalization), LabelEncoder (target encoding) |
| **Feature Selection** | Selected subset of columns saved in `selected_column_names.pkl` |
| **Training Notebook** | `cisco2017/main.ipynb` |

**Why LightGBM?**
- Handles large, imbalanced datasets (BENIGN traffic dominates) efficiently
- Extremely fast inference — critical for real-time packet classification
- Native support for categorical features and missing values
- Outperforms Random Forest on tabular data while using less memory

---

## Project Structure

```
ddosattact/
│
├── cisco2017/                   # ML Training & Inference (Python)
│   ├── main.ipynb               # Data exploration, preprocessing & model training notebook
│   ├── main.py                  # Kafka consumer — real-time ML inference engine
│   ├── requirements.txt         # Python dependencies
│   ├── lgbm_model.pkl           # Trained LightGBM model (2.4 MB)
│   ├── encoder.pkl              # LabelEncoder for attack type decoding
│   ├── scaler.pkl               # StandardScaler for feature normalization
│   ├── selected_column_names.pkl# Ordered feature column list used during training
│   └── cicids2017_cleaned.csv   # Cleaned dataset (~686 MB, not tracked in git)
│
├── cyberAttack/                 # Kafka Stream Producer (Node.js)
│   ├── index.js                 # Reads CSV → streams rows to Kafka topic
│   ├── package.json             # Node.js project manifest
│   ├── pnpm-lock.yaml           # Locked dependency versions
│   └── cicids2017_cleaned.csv   # Shared dataset copy for streaming
│
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **ML Framework** | LightGBM, scikit-learn, pandas, numpy |
| **ML Serialization** | joblib (`.pkl` model artifacts) |
| **Message Broker** | Apache Kafka |
| **Stream Producer** | Node.js (kafkajs, csv-parser, express) |
| **Stream Consumer** | Python (confluent-kafka) |
| **API Layer** | FastAPI + Uvicorn *(planned — see roadmap)* |
| **Database** | MongoDB *(planned — see roadmap)* |
| **Training Environment** | Jupyter Notebook |

---

## Setup & Installation

### Prerequisites

Ensure the following are installed on your machine:

- [Python 3.10+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/) and [pnpm](https://pnpm.io/)
- [Apache Kafka](https://kafka.apache.org/downloads) with Zookeeper (or KRaft mode)
- The CICIDS2017 cleaned dataset CSV placed inside both `cisco2017/` and `cyberAttack/`

---

### Phase 1 — ML Training (Python)

```bash
# Navigate to the ML directory
cd cisco2017

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# Install Python dependencies
pip install -r requirements.txt

# Launch Jupyter to run the training notebook
jupyter notebook main.ipynb
```

> The notebook covers: data loading → cleaning → feature engineering → scaling → LightGBM training → evaluation → saving `.pkl` artifacts.

---

### Phase 2 — Kafka Stream Producer (Node.js)

**Step 1 — Start Apache Kafka (in a separate terminal):**

```bash
# Start Zookeeper
zookeeper-server-start.bat config\zookeeper.properties

# Start Kafka Broker (in another terminal)
kafka-server-start.bat config\server.properties
```

**Step 2 — Create the Kafka topic:**

```bash
kafka-topics.bat --create --topic network-traffic --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

**Step 3 — Start the Node.js producer:**

```bash
cd cyberAttack
pnpm install
pnpm dev
```

> The producer streams every row of `cicids2017_cleaned.csv` as a JSON message to the `network-traffic` Kafka topic, logging progress every 1,000 packets.

---

### Phase 3 — ML Inference Consumer (Python)

```bash
# In a new terminal, with the venv activated
cd cisco2017
python main.py
```

You will see live output like:

```
Loading Machine Learning assets...
✅ Model, Columns, and Encoder loaded successfully.
🎧 Listening to Kafka topic 'network-traffic'...
✅ [OK] Normal Traffic | Confidence: 99.87%
✅ [OK] Normal Traffic | Confidence: 98.43%
🚨 [ALERT] Threat Detected: DDoS | Confidence: 97.61%
🚨 [ALERT] Threat Detected: PortScan | Confidence: 96.22%
```

---

## Model Artifacts

| File | Description | Size |
|---|---|---|
| `lgbm_model.pkl` | Trained LightGBM multi-class classifier | 2.4 MB |
| `encoder.pkl` | LabelEncoder mapping numeric predictions → attack names | ~0.3 KB |
| `scaler.pkl` | StandardScaler fit on training features | ~2.6 KB |
| `selected_column_names.pkl` | Ordered list of feature columns used during training | ~1.3 KB |

> ⚠️ **Note:** The raw dataset `cicids2017_cleaned.csv` (~686 MB) is excluded from version control via `.gitignore`. Download it separately from the [UNB CIC website](https://www.unb.ca/cic/datasets/ids-2017.html).

---

## Results & Performance

| Metric | Value |
|---|---|
| **Model** | LightGBM Multi-Class Classifier |
| **Accuracy** | ~99%+ on CICIDS2017 test split |
| **Inference Latency** | <5ms per packet (CPU) |
| **Throughput** | Capable of processing 10,000+ events/second |
| **Attack Classes Detected** | DDoS, PortScan, BruteForce, DoS Hulk, DoS GoldenEye, Web Attack, Infiltration, Heartbleed, BENIGN |

---

## Future Roadmap

- [ ] **FastAPI Inference Endpoint** — expose `/predict` REST API to accept live packet JSON and return classification instantly
- [ ] **MongoDB Logging** — persist every detected threat with timestamp, type, and confidence to a MongoDB collection
- [ ] **Docker Compose** — containerize Kafka, Zookeeper, Python consumer, and Node.js producer for one-command deployment
- [ ] **Dashboard** — React-based real-time threat visualization dashboard with live attack feed and statistics
- [ ] **Kafka Partitioning** — scale to multiple partitions and consumer instances for true parallel inference
- [ ] **UNSW-NB15 Integration** — cross-validate model generalization on the UNSW-NB15 dataset

---

## Author

**Dheeraj Patel**  
Full-Stack & ML Engineer 

---

> *"Real security doesn't wait for logs — it acts on streams."*
