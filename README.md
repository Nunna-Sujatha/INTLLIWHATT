

# ⚡ IntelliWatt – AI-Powered Smart Electricity Management System

## 📌 Overview

IntelliWatt is an AI-powered smart electricity management platform designed to help users monitor, analyze, predict, and optimize their electricity consumption. The system combines Machine Learning, OCR, Data Analytics, and Interactive Dashboards to provide intelligent insights into energy usage.

The platform enables users to upload electricity bills, extract bill information automatically, predict future energy consumption, forecast electricity usage trends, and receive AI-powered recommendations for energy savings.

---

## 🚀 Features

### 📊 Dashboard Analytics

* Real-time electricity consumption monitoring
* Interactive charts and visualizations
* Monthly and yearly usage statistics

### 🔮 Energy Consumption Prediction

* Machine Learning-based electricity usage prediction
* Future consumption estimation
* Data-driven energy planning

### 📈 Forecasting

* Historical usage trend analysis
* Future electricity demand forecasting
* Smart energy management insights

### 📄 OCR Bill Processing

* Upload electricity bill PDFs
* Automatic bill data extraction using OCR
* Digital bill management

### 🤖 AI Chatbot Assistant

* Intelligent energy-related assistance
* User query handling
* Personalized recommendations

### ⚙️ Appliance Management

* Track household appliance energy consumption
* Identify high-energy-consuming devices
* Optimize appliance usage

### 💰 Bill Generation & Analysis

* Electricity bill estimation
* Cost analysis and reporting
* Energy-saving suggestions

---

## 🛠️ Technology Stack

### Frontend

* React.js
* Vite
* JavaScript
* CSS

### Backend

* FastAPI
* Python

### Machine Learning & AI

* Scikit-Learn
* Pandas
* NumPy
* OCR Processing
* Predictive Analytics

### Data Storage

* JSON-based data management

---

## 📂 Project Structure

```text
INTLLIWHATT/
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
│
├── backend/
│   ├── routers/
│   ├── services/
│   ├── data/
│   ├── uploads/
│   ├── main.py
│   └── requirements.txt
│
└── electricity_bill_dataset.csv
```

---

## ⚡ Installation

### Clone Repository

```bash
git clone https://github.com/Nunna-Sujatha/INTLLIWHATT.git
cd INTLLIWHATT
```

### Backend Setup

```bash
cd backend

python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt

uvicorn main:app --reload
```

Backend runs at:

```text
http://localhost:8000
```

### Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

Frontend runs at:

```text
http://localhost:5173
```

---

## 🎯 Objectives

* Monitor electricity consumption effectively.
* Predict future energy usage using Machine Learning.
* Automate bill data extraction through OCR.
* Provide AI-driven energy-saving recommendations.
* Promote efficient and sustainable energy utilization.

---

## 📈 Future Enhancements

* Smart Meter Integration
* IoT Device Connectivity
* Mobile Application Support
* Advanced Deep Learning Models
* Real-time Notification System
* Cloud Deployment

---


Copy this into a file named **README.md**, then run:

```bash
git add README.md
git commit -m "Added project README"
git push
```

This will make your GitHub repository look professional.
