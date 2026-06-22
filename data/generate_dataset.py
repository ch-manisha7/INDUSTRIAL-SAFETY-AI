import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

zones = ["Zone-A (Coke Oven)", "Zone-B (Blast Furnace)", "Zone-C (Oxygen Plant)", "Zone-D (Workshop)"]
n = 2000
base = datetime(2025, 1, 1)
timestamps = [base + timedelta(hours=i * 0.5) for i in range(n)]

# ── 1. SENSOR READINGS
sensor_df = pd.DataFrame({
    "timestamp":      timestamps,
    "zone":           np.random.choice(zones, n),
    "CO_ppm":         np.clip(np.random.normal(30, 25, n), 0, 400),
    "H2S_ppm":        np.clip(np.random.normal(2, 3, n), 0, 50),
    "CH4_ppm":        np.clip(np.random.normal(50, 40, n), 0, 500),
    "O2_percent":     np.clip(np.random.normal(20.5, 1.5, n), 15, 23),
    "temperature_C":  np.clip(np.random.normal(45, 15, n), 20, 120),
    "pressure_bar":   np.clip(np.random.normal(2.5, 0.8, n), 0.5, 8),
    "vibration_mm_s": np.clip(np.random.normal(3, 2, n), 0, 20),
    "noise_dB":       np.clip(np.random.normal(75, 10, n), 50, 110),
})
danger_idx = np.random.choice(n, 40, replace=False)
sensor_df.loc[danger_idx, "CO_ppm"]        += np.random.uniform(150, 300, 40)
sensor_df.loc[danger_idx, "H2S_ppm"]       += np.random.uniform(10, 40, 40)
sensor_df.loc[danger_idx, "O2_percent"]    -= np.random.uniform(3, 6, 40)
sensor_df.loc[danger_idx, "pressure_bar"]  += np.random.uniform(2, 4, 40)
sensor_df["incident_flag"] = 0
sensor_df.loc[danger_idx, "incident_flag"] = 1
for col in ["CO_ppm","H2S_ppm","CH4_ppm","O2_percent","temperature_C","pressure_bar","vibration_mm_s","noise_dB"]:
    sensor_df[col] = sensor_df[col].round(2)
sensor_df.to_csv("sensor_readings.csv", index=False)
print(f"sensor_readings.csv: {len(sensor_df)} rows, {int(sensor_df['incident_flag'].sum())} danger events")

# ── 2. WORK PERMITS
permit_types = ["Hot Work", "Confined Space Entry", "Electrical Isolation", "Height Work", "Chemical Handling"]
permits = []
for i in range(300):
    start = base + timedelta(hours=random.randint(0, 900))
    permits.append({
        "permit_id":              f"PTW-{1000+i}",
        "permit_type":            random.choice(permit_types),
        "zone":                   random.choice(zones),
        "issued_to":              f"Worker-{random.randint(1,50)}",
        "supervisor":             f"Supervisor-{random.randint(1,10)}",
        "start_time":             start.isoformat(),
        "end_time":               (start + timedelta(hours=random.uniform(1, 8))).isoformat(),
        "status":                 random.choice(["Active","Active","Active","Closed","Suspended"]),
        "gas_clearance_obtained": random.choice([True, True, True, False]),
        "ppe_verified":           random.choice([True, True, False]),
    })
pd.DataFrame(permits).to_csv("work_permits.csv", index=False)
print(f"work_permits.csv: {len(permits)} rows")

# ── 3. INCIDENTS
incident_types = ["Gas leak detected","Worker trapped in confined space","Equipment fire",
                  "Fall from height","Explosion (near miss)","Chemical spill",
                  "Electrical arc flash","Crane overload","H2S exposure"]
severities = ["Low","Medium","High","Critical"]
incidents = []
for i in range(120):
    dt  = base + timedelta(hours=random.randint(0, 8760))
    sev = random.choices(severities, weights=[30,40,20,10])[0]
    incidents.append({
        "incident_id":       f"INC-{2000+i}",
        "date_time":         dt.isoformat(),
        "zone":              random.choice(zones),
        "incident_type":     random.choice(incident_types),
        "severity":          sev,
        "injuries":          0 if sev in ["Low","Medium"] else random.randint(0,3),
        "fatalities":        0 if sev != "Critical" else random.randint(0,1),
        "root_cause":        random.choice(["Lack of gas clearance","PTW not followed","Inadequate PPE",
                                            "Equipment failure","Communication breakdown","Untrained personnel"]),
        "corrective_action": random.choice(["Retrain staff","Upgrade sensors","Revise PTW procedure",
                                            "Install additional ventilation","Mandatory PPE audit"]),
        "days_to_close":     random.randint(1, 30),
    })
pd.DataFrame(incidents).to_csv("incidents.csv", index=False)
print(f"incidents.csv: {len(incidents)} rows")

# ── 4. MAINTENANCE
equipment_list = ["Gas Detector GD-01","Gas Detector GD-02","SCADA Controller",
                  "Coke Oven Battery #3","Oxygen Compressor","Blast Furnace BF-2",
                  "Cooling Tower CT-1","Pressure Relief Valve PRV-7"]
maint = []
for i in range(200):
    dt = base + timedelta(days=random.randint(0, 365))
    maint.append({
        "maintenance_id": f"MNT-{3000+i}",
        "date":           dt.date().isoformat(),
        "equipment":      random.choice(equipment_list),
        "zone":           random.choice(zones),
        "type":           random.choice(["Preventive","Corrective","Emergency","Inspection"]),
        "status":         random.choice(["Completed","In Progress","Overdue","Scheduled"]),
        "technician":     f"Tech-{random.randint(1,20)}",
        "duration_hours": round(random.uniform(0.5, 12), 1),
        "parts_replaced": random.choice([True, False]),
        "next_due_days":  random.randint(7, 180),
    })
pd.DataFrame(maint).to_csv("maintenance_records.csv", index=False)
print(f"maintenance_records.csv: {len(maint)} rows")

# ── 5. WORKER LOCATIONS
workers_loc = []
for i in range(500):
    dt = base + timedelta(hours=random.randint(0, 200))
    workers_loc.append({
        "timestamp":  dt.isoformat(),
        "worker_id":  f"Worker-{random.randint(1,50)}",
        "zone":       random.choice(zones),
        "latitude":   round(17.6868 + random.uniform(-0.005, 0.005), 6),
        "longitude":  round(83.2185 + random.uniform(-0.005, 0.005), 6),
        "shift":      random.choice(["Morning","Afternoon","Night"]),
        "heart_rate": random.randint(60, 110),
        "body_temp_C":round(random.uniform(36.0, 38.5), 1),
    })
pd.DataFrame(workers_loc).to_csv("worker_locations.csv", index=False)
print(f"worker_locations.csv: {len(workers_loc)} rows")

# ── 6. REGULATORY COMPLIANCE
regs = [
    {"regulation":"OISD-116",       "clause":"5.3",     "description":"Gas detector calibration every 6 months",      "compliant":True},
    {"regulation":"OISD-116",       "clause":"7.1",     "description":"PTW system mandatory for hot work",             "compliant":True},
    {"regulation":"Factory Act 1948","clause":"36",     "description":"Confined space entry procedure documented",     "compliant":False},
    {"regulation":"DGMS Circular",  "clause":"2024-03", "description":"Coke oven gas monitoring 24x7",                 "compliant":True},
    {"regulation":"OISD-GDN-169",   "clause":"4.2",     "description":"Emergency response drill quarterly",           "compliant":False},
    {"regulation":"Factory Act 1948","clause":"41B",    "description":"Hazardous process worker health check",         "compliant":True},
    {"regulation":"PESO",           "clause":"8.1",     "description":"Pressure vessel inspection annually",           "compliant":True},
    {"regulation":"OISD-116",       "clause":"9.4",     "description":"SCADA alarm management procedure in place",     "compliant":False},
]
pd.DataFrame(regs).to_csv("regulatory_compliance.csv", index=False)
print(f"regulatory_compliance.csv: {len(regs)} rows")

print("\n✅ All datasets generated successfully!")
