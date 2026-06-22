"""
Industrial Safety Intelligence Platform — FastAPI Backend
Uses OpenRouter API for AI-powered compound risk analysis.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
import json
import httpx
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")


app = FastAPI(title="Industrial Safety Intelligence API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Config ────────────────────────────────────────────────────────────────────
DATA_DIR       = Path(__file__).parent.parent / "data"
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "YOUR_OPENROUTER_KEY_HERE")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-oss-20b:free"
# fast & free-tier friendly

# ── Load data ─────────────────────────────────────────────────────────────────
def load_data():
    return {
        "sensors":     pd.read_csv(DATA_DIR / "sensor_readings.csv"),
        "permits":     pd.read_csv(DATA_DIR / "work_permits.csv"),
        "incidents":   pd.read_csv(DATA_DIR / "incidents.csv"),
        "maintenance": pd.read_csv(DATA_DIR / "maintenance_records.csv"),
        "workers":     pd.read_csv(DATA_DIR / "worker_locations.csv"),
        "compliance":  pd.read_csv(DATA_DIR / "regulatory_compliance.csv"),
    }

data = load_data()

# ── Thresholds (OISD / industrial standards) ──────────────────────────────────
THRESHOLDS = {
    "CO_ppm":         {"warning": 25,  "critical": 50},
    "H2S_ppm":        {"warning": 5,   "critical": 10},
    "CH4_ppm":        {"warning": 100, "critical": 200},
    "O2_percent_low": {"warning": 19.5,"critical": 18.0},
    "temperature_C":  {"warning": 80,  "critical": 100},
    "pressure_bar":   {"warning": 5,   "critical": 7},
    "vibration_mm_s": {"warning": 10,  "critical": 15},
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def compute_risk_score(row: dict) -> dict:
    """Score a sensor reading 0-100 and flag breached thresholds."""
    score   = 0
    alerts  = []
    weights = {"critical": 30, "warning": 10}

    checks = [
        ("CO_ppm",        row.get("CO_ppm", 0),        "CO"),
        ("H2S_ppm",       row.get("H2S_ppm", 0),       "H2S"),
        ("CH4_ppm",       row.get("CH4_ppm", 0),       "CH4"),
        ("temperature_C", row.get("temperature_C", 0), "Temperature"),
        ("pressure_bar",  row.get("pressure_bar", 0),  "Pressure"),
        ("vibration_mm_s",row.get("vibration_mm_s",0), "Vibration"),
    ]
    for key, val, label in checks:
        t = THRESHOLDS.get(key, {})
        if val >= t.get("critical", 9e9):
            score += weights["critical"]
            alerts.append({"param": label, "value": val, "level": "CRITICAL"})
        elif val >= t.get("warning", 9e9):
            score += weights["warning"]
            alerts.append({"param": label, "value": val, "level": "WARNING"})

    # Low O2 check
    o2 = row.get("O2_percent", 21)
    if o2 <= THRESHOLDS["O2_percent_low"]["critical"]:
        score += weights["critical"]
        alerts.append({"param": "O2", "value": o2, "level": "CRITICAL"})
    elif o2 <= THRESHOLDS["O2_percent_low"]["warning"]:
        score += weights["warning"]
        alerts.append({"param": "O2", "value": o2, "level": "WARNING"})

    return {"score": min(score, 100), "alerts": alerts}


async def call_openrouter(system_prompt: str, user_prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type":  "application/json",
        "HTTP-Referer":  "https://industrial-safety-ai.local",
        "X-Title":       "Industrial Safety Intelligence",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "max_tokens": 800,
        "temperature": 0.3,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(OPENROUTER_URL, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "service": "Industrial Safety Intelligence Platform"}


@app.get("/api/dashboard")
def dashboard():
    """High-level KPIs for the dashboard."""
    sensors    = data["sensors"]
    incidents  = data["incidents"]
    compliance = data["compliance"]
    permits    = data["permits"]

    danger_rows = sensors[sensors["incident_flag"] == 1]
    critical_inc = incidents[incidents["severity"].isin(["High", "Critical"])]
    non_compliant = compliance[compliance["compliant"] == False]
    active_permits = permits[permits["status"] == "Active"]

    # Zone risk heatmap (avg across dangerous readings)
    zone_risk = (
        danger_rows.groupby("zone")[["CO_ppm","H2S_ppm","pressure_bar"]]
        .mean().round(2).reset_index()
        .rename(columns={"CO_ppm":"avg_CO","H2S_ppm":"avg_H2S","pressure_bar":"avg_pressure"})
    )

    return {
        "kpis": {
            "total_sensor_readings":    len(sensors),
            "danger_events_detected":   int(sensors["incident_flag"].sum()),
            "total_incidents":          len(incidents),
            "critical_incidents":       len(critical_inc),
            "compliance_gap_count":     len(non_compliant),
            "active_permits":           len(active_permits),
            "overall_compliance_pct":   round(compliance["compliant"].mean() * 100, 1),
        },
        "zone_risk_heatmap": zone_risk.to_dict(orient="records"),
        "incident_by_severity": incidents["severity"].value_counts().to_dict(),
        "incident_by_type":     incidents["incident_type"].value_counts().head(5).to_dict(),
        "compliance_gaps":      non_compliant[["regulation","clause","description"]].to_dict(orient="records"),
    }


@app.get("/api/sensors/latest")
def sensors_latest(zone: Optional[str] = None, limit: int = 50):
    """Return latest sensor readings with risk scores."""
    df = data["sensors"].copy()
    if zone:
        df = df[df["zone"] == zone]
    df = df.tail(limit)
    rows = df.to_dict(orient="records")
    for r in rows:
        risk = compute_risk_score(r)
        r["risk_score"] = risk["score"]
        r["alerts"]     = risk["alerts"]
    return {"readings": rows}


@app.get("/api/sensors/stats")
def sensor_stats():
    """Time-series aggregated stats for charts."""
    df = data["sensors"].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"]      = df["timestamp"].dt.date.astype(str)
    agg = df.groupby("date").agg(
        avg_CO      =("CO_ppm",         "mean"),
        avg_H2S     =("H2S_ppm",        "mean"),
        avg_O2      =("O2_percent",      "mean"),
        avg_pressure=("pressure_bar",    "mean"),
        danger_count=("incident_flag",   "sum"),
    ).round(3).reset_index()
    return {"timeseries": agg.to_dict(orient="records")}


@app.get("/api/permits")
def permits(status: Optional[str] = None):
    df = data["permits"].copy()
    if status:
        df = df[df["status"] == status]
    return {"permits": df.to_dict(orient="records"), "total": len(df)}


@app.get("/api/incidents")
def incidents(severity: Optional[str] = None, limit: int = 100):
    df = data["incidents"].copy()
    if severity:
        df = df[df["severity"] == severity]
    df = df.sort_values("date_time", ascending=False).head(limit)
    return {"incidents": df.to_dict(orient="records"), "total": len(df)}


@app.get("/api/maintenance")
def maintenance(status: Optional[str] = None):
    df = data["maintenance"].copy()
    if status:
        df = df[df["status"] == status]
    return {"records": df.to_dict(orient="records"), "total": len(df)}


@app.get("/api/workers")
def workers(zone: Optional[str] = None):
    df = data["workers"].copy()
    if zone:
        df = df[df["zone"] == zone]
    return {"workers": df.tail(100).to_dict(orient="records")}


@app.get("/api/compliance")
def compliance():
    df = data["compliance"]
    return {
        "items":              df.to_dict(orient="records"),
        "compliant_count":    int(df["compliant"].sum()),
        "non_compliant_count":int((~df["compliant"]).sum()),
    }


# ── Compound Risk Detection ───────────────────────────────────────────────────
@app.get("/api/compound-risk")
def compound_risk():
    """
    Detect dangerous compound conditions:
    e.g. Hot Work permit ACTIVE + high CO + active maintenance in same zone.
    """
    sensors  = data["sensors"]
    permits  = data["permits"]
    maint    = data["maintenance"]

    # Dangerous sensor readings
    danger = sensors[sensors["incident_flag"] == 1][["zone","CO_ppm","H2S_ppm","O2_percent","pressure_bar"]].copy()

    # Active hot-work or confined-space permits
    risky_permits = permits[
        (permits["status"] == "Active") &
        (permits["permit_type"].isin(["Hot Work", "Confined Space Entry"]))
    ][["zone","permit_id","permit_type","gas_clearance_obtained"]]

    # Overdue maintenance
    overdue = maint[maint["status"] == "Overdue"][["zone","equipment","maintenance_id"]]

    compound_events = []
    for zone in danger["zone"].unique():
        z_danger  = danger[danger["zone"] == zone]
        z_permits = risky_permits[risky_permits["zone"] == zone]
        z_overdue = overdue[overdue["zone"] == zone]

        if len(z_danger) > 0 and len(z_permits) > 0:
            for _, p in z_permits.iterrows():
                row = z_danger.iloc[0]
                compound_events.append({
                    "zone":             zone,
                    "condition":        f"{p['permit_type']} active during hazardous gas accumulation",
                    "CO_ppm":           round(float(row["CO_ppm"]), 2),
                    "H2S_ppm":          round(float(row["H2S_ppm"]), 2),
                    "O2_percent":       round(float(row["O2_percent"]), 2),
                    "permit_id":        p["permit_id"],
                    "permit_type":      p["permit_type"],
                    "gas_clearance":    bool(p["gas_clearance_obtained"]),
                    "overdue_equipment":[e for e in z_overdue["equipment"].tolist()],
                    "risk_level":       "CRITICAL" if not p["gas_clearance_obtained"] else "HIGH",
                    "recommendation":   (
                        "SUSPEND permit immediately. Evacuate zone. Verify gas clearance before re-entry."
                        if not p["gas_clearance_obtained"]
                        else "Monitor closely. Re-verify gas levels. Consider suspending if levels rise."
                    ),
                })

    return {
        "compound_events": compound_events,
        "total_detected":  len(compound_events),
        "zones_at_risk":   list({e["zone"] for e in compound_events}),
    }


# ── AI Analysis ───────────────────────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    zone:       Optional[str] = None
    query_type: str = "risk_summary"  # risk_summary | incident_pattern | compliance_review | emergency


@app.post("/api/ai/analyze")
async def ai_analyze(req: AnalyzeRequest):
    """Call OpenRouter LLM with plant data for intelligent safety analysis."""
    sensors    = data["sensors"]
    incidents  = data["incidents"]
    compliance = data["compliance"]
    permits    = data["permits"]

    # Filter by zone if requested
    if req.zone:
        s = sensors[sensors["zone"] == req.zone]
        p = permits[permits["zone"] == req.zone]
    else:
        s = sensors
        p = permits

    danger_count  = int(s["incident_flag"].sum())
    avg_CO        = round(float(s["CO_ppm"].mean()), 2)
    avg_H2S       = round(float(s["H2S_ppm"].mean()), 2)
    avg_O2        = round(float(s["O2_percent"].mean()), 2)
    active_hot    = int(p[(p["status"]=="Active") & (p["permit_type"]=="Hot Work")].shape[0])
    confined_entry= int(p[(p["status"]=="Active") & (p["permit_type"]=="Confined Space Entry")].shape[0])
    critical_inc  = incidents[incidents["severity"]=="Critical"]
    non_compliant = compliance[compliance["compliant"]==False]

    data_summary = f"""
Plant Safety Data Summary{f' — {req.zone}' if req.zone else ' — All Zones'}:
- Danger events detected: {danger_count} out of {len(s)} sensor readings
- Avg CO: {avg_CO} ppm | Avg H2S: {avg_H2S} ppm | Avg O2: {avg_O2}%
- Active Hot Work permits: {active_hot}
- Active Confined Space Entry permits: {confined_entry}
- Critical incidents (all time): {len(critical_inc)}
- Regulatory non-compliance items: {len(non_compliant)}
- Non-compliant clauses: {', '.join(non_compliant['regulation'].tolist())}
- Top root causes: {incidents['root_cause'].value_counts().head(3).to_dict()}
"""

    prompts = {
        "risk_summary": (
            "You are an Industrial Safety Intelligence AI for a heavy industrial plant (steel/coke oven). "
            "Analyse the data and provide a concise risk summary: current risk level, top 3 immediate threats, "
            "and 3 actionable recommendations. Use OISD, Factory Act, and DGMS standards as reference.",
            data_summary + "\nProvide a structured risk summary with: RISK LEVEL, TOP THREATS, RECOMMENDATIONS."
        ),
        "incident_pattern": (
            "You are a safety incident analyst for Indian heavy industry. "
            "Identify recurring incident patterns and systemic root causes from the data provided. "
            "Reference relevant OISD or Factory Act clauses where applicable.",
            data_summary + "\nIdentify incident patterns and systemic causes. Suggest preventive measures."
        ),
        "compliance_review": (
            "You are a regulatory compliance officer for Indian heavy industry (OISD, Factory Act, DGMS, PESO). "
            "Review the compliance status and generate a priority-ordered corrective action plan.",
            data_summary + "\nGenerate a compliance corrective action plan with priority levels (P1/P2/P3)."
        ),
        "emergency": (
            "You are an Emergency Response Coordinator for a heavy industrial facility. "
            "Based on the current dangerous conditions, generate an immediate emergency response protocol. "
            "Be specific, actionable, and time-bound (first 10 minutes).",
            data_summary + "\nGenerate an EMERGENCY RESPONSE PROTOCOL for the current conditions."
        ),
    }

    if req.query_type not in prompts:
        raise HTTPException(400, "query_type must be one of: risk_summary, incident_pattern, compliance_review, emergency")

    system_p, user_p = prompts[req.query_type]

    try:
        response = await call_openrouter(system_p, user_p)
        return {
            "zone":       req.zone or "All Zones",
            "query_type": req.query_type,
            "analysis":   response,
            "data_used":  data_summary.strip(),
            "model":      MODEL,
            "timestamp":  datetime.now().isoformat(),
        }
    except httpx.HTTPStatusError as e:
        raise HTTPException(502, f"OpenRouter API error: {e.response.text}")
    except Exception as e:
        raise HTTPException(500, str(e))


class ChatRequest(BaseModel):
    message: str
    zone: Optional[str] = None


@app.post("/api/ai/chat")
async def ai_chat(req: ChatRequest):
    """Free-form safety Q&A chatbot powered by OpenRouter."""
    sensors   = data["sensors"]
    incidents = data["incidents"]
    permits   = data["permits"]

    context = f"""
You are SafetyGPT, an AI assistant for an Indian heavy industrial plant safety team.
Current plant status:
- Total danger events: {int(sensors['incident_flag'].sum())}
- Avg CO across plant: {round(float(sensors['CO_ppm'].mean()),2)} ppm
- Active permits: {int(permits[permits['status']=='Active'].shape[0])}
- Recent critical incidents: {int(incidents[incidents['severity']=='Critical'].shape[0])}
- Zones monitored: {', '.join(sensors['zone'].unique().tolist())}
{"- Current zone focus: " + req.zone if req.zone else ""}

Answer the operator's question accurately. If recommending actions, reference OISD/Factory Act standards.
Keep answers clear and concise for field operators.
"""
    try:
        reply = await call_openrouter(context, req.message)
        return {"reply": reply, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(500, str(e))
