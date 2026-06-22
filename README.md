# 🏭 AI-Powered Industrial Safety Intelligence Platform
**ET AI Hackathon 2026 — Problem Statement 1**

> Compound risk detection for zero-harm industrial operations using AI agents, sensor fusion, and OpenRouter LLM analysis.

---

## 📁 Project Structure

```
industrial-safety-ai/
├── backend/
│   ├── main.py                  # FastAPI backend (all API routes)
│   └── requirements.txt
├── frontend/
│   └── index.html               # Single-file React-free dashboard
├── data/
│   ├── generate_dataset.py      # Synthetic dataset generator
│   ├── sensor_readings.csv      # 2,000 sensor readings (40 danger events)
│   ├── work_permits.csv         # 300 PTW records
│   ├── incidents.csv            # 120 incidents/near-misses
│   ├── maintenance_records.csv  # 200 maintenance records
│   ├── worker_locations.csv     # 500 geo-tagged worker positions
│   └── regulatory_compliance.csv# 8 OISD/Factory Act compliance items
└── README.md
```

---

## 🚀 Quick Start

### 1. Set your OpenRouter API Key

Get a free key at https://openrouter.ai

```bash
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"
```

### 2. Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Start the backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 4. Open the frontend

Open `frontend/index.html` in your browser (no build step needed).

> The dashboard auto-loads data from `http://localhost:8000`

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard` | KPIs, zone heatmap, compliance gaps |
| GET | `/api/sensors/latest` | Latest sensor readings with risk scores |
| GET | `/api/sensors/stats` | Time-series aggregated stats |
| GET | `/api/compound-risk` | **Compound danger event detection** |
| GET | `/api/permits` | Work permit registry |
| GET | `/api/incidents` | Incident/near-miss registry |
| GET | `/api/maintenance` | Maintenance records |
| GET | `/api/compliance` | Regulatory compliance status |
| POST | `/api/ai/analyze` | LLM safety analysis (OpenRouter) |
| POST | `/api/ai/chat` | SafetyGPT chatbot |

---

## 🤖 AI Features (OpenRouter)

The platform uses `mistralai/mistral-7b-instruct` via OpenRouter for:

- **Risk Summary** — Current risk level + top threats + recommendations
- **Incident Pattern Analysis** — Recurring causes and systemic issues
- **Compliance Review** — Priority-ordered corrective action plan (P1/P2/P3)
- **Emergency Protocol** — Time-bound emergency response for first 10 minutes
- **SafetyGPT Chat** — Field operator Q&A (OISD regulations, gas levels, PTW)

To use a different model, change `MODEL` in `backend/main.py`:
```python
MODEL = "mistralai/mistral-7b-instruct"   # free tier
# MODEL = "openai/gpt-4o"                 # higher quality
# MODEL = "anthropic/claude-3-haiku"      # balanced
```

---

## 🧠 Compound Risk Detection Logic

The engine flags **dangerous compound conditions** when:
1. A zone has **active sensor danger readings** (CO, H2S, O2, pressure breach)
2. **AND** a Hot Work / Confined Space Entry permit is **Active** in the same zone
3. **AND** (optional) maintenance is **Overdue** on equipment in that zone

This mirrors the Visakhapatnam Steel Plant incident pattern — data existed but no layer connected it.

---

## 📊 Datasets

| File | Rows | Description |
|------|------|-------------|
| `sensor_readings.csv` | 2,000 | Hourly gas/pressure/temp/vibration readings, 40 injected danger events |
| `work_permits.csv` | 300 | PTW records with permit type, zone, gas clearance status |
| `incidents.csv` | 120 | Historical incidents with severity, root cause, corrective action |
| `maintenance_records.csv` | 200 | Equipment maintenance with overdue tracking |
| `worker_locations.csv` | 500 | Geo-tagged worker positions with biometric data |
| `regulatory_compliance.csv` | 8 | OISD/Factory Act/DGMS/PESO clause compliance |

All datasets are synthetic but calibrated to realistic industrial ranges.

---

## 🏆 Judging Criteria Alignment

| Criterion | Implementation |
|-----------|---------------|
| Innovation (25%) | Compound risk detection engine; multi-source fusion; AI chatbot |
| Business Impact (25%) | Visakhapatnam-pattern detection; OISD/Factory Act references |
| Technical Excellence (20%) | FastAPI + pandas risk engine + OpenRouter LLM |
| Scalability (15%) | Modular REST API; swappable LLM model; CSV→DB ready |
| User Experience (15%) | Dark-theme command centre; real-time risk scores; one-click AI analysis |

---

## 🛡️ Safety Standards Referenced

- **OISD-116** — Gas detector calibration, PTW for hot work, SCADA alarm management
- **OISD-GDN-169** — Emergency response drills
- **Factory Act 1948** — Confined space procedures, hazardous process health checks
- **DGMS Circular 2024-03** — Coke oven gas monitoring
- **PESO** — Pressure vessel inspection

---

## 📝 Architecture

```
Browser (index.html)
       │
       │  REST API calls
       ▼
FastAPI Backend (main.py)
       │
       ├── /api/compound-risk  ──► Risk Engine (pandas rule-based)
       ├── /api/ai/analyze     ──► OpenRouter API ──► Mistral-7B
       ├── /api/ai/chat        ──► OpenRouter API ──► Mistral-7B
       └── /api/sensors/*      ──► CSV DataFrames
                                         │
                               data/*.csv (synthetic datasets)
```
