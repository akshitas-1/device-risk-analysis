"""
Device Risk Analysis - Main Calculation Script
================================================
Used inside Relevance AI as a Python step.
Upstream variables (device_data, customer_data, incident_data) are injected
via Relevance AI's variable picker using {{ }} references.

Author: Device Risk Analysis Pipeline
Version: 1.0.0
"""

import pandas as pd
from datetime import datetime

# ── Constants ────────────────────────────────────────────────────────────────
PREVENTIVE_ACTION_FIXED_COST = 3000   # Fixed cost ($) for any preventive action
FAILURE_PROB_THRESHOLD       = 0.85   # Only flag devices at or above this probability

# ── Load data from Relevance AI Knowledge tables ──────────────────────────────
# Note: device_data, customer_data, incident_data are injected by Relevance AI
# via the {{ }} variable picker — do not hardcode these references.
df_devices   = pd.DataFrame(device_data['data'])
df_customers = pd.DataFrame(customer_data['data'])
df_incidents = pd.DataFrame(incident_data['data'])

# ── Normalise column names ────────────────────────────────────────────────────
df_devices.columns   = df_devices.columns.str.strip().str.lower().str.replace("-", "_").str.replace(" ", "_")
df_customers.columns = df_customers.columns.str.strip().str.lower().str.replace("-", "_").str.replace(" ", "_")
df_incidents.columns = df_incidents.columns.str.strip().str.lower().str.replace("-", "_").str.replace(" ", "_")

# ── Filter high-risk devices ──────────────────────────────────────────────────
df_high_risk = df_devices[df_devices["failure_probability"] >= FAILURE_PROB_THRESHOLD][
    ["device_id", "device_type", "failure_probability"]
].copy()

# ── Join with customer SLA data ───────────────────────────────────────────────
df_merged = df_high_risk.merge(
    df_customers[["device_id", "customer_name", "revenue", "sla_hours"]],
    on="device_id",
    how="inner"
)
df_merged.rename(columns={"revenue": "revenue_per_hour"}, inplace=True)

# ── Round failure probability to match incident bucket keys (0.5, 0.6 … 1.0) ─
df_merged["failure_prob_rounded"]    = (df_merged["failure_probability"] * 10).round() / 10
df_incidents["failure_prob_rounded"] = df_incidents["failure_probability"]

# ── Join with incident history ────────────────────────────────────────────────
df_final = df_merged.merge(
    df_incidents[[
        "device_type", "failure_prob_rounded",
        "unplanned_downtime_hours", "planned_downtime_hours"
    ]],
    on=["device_type", "failure_prob_rounded"],
    how="left"
)

# ── Financial calculations ────────────────────────────────────────────────────
df_final["downtime_rev_loss"] = (
    df_final["unplanned_downtime_hours"] * df_final["revenue_per_hour"]
)

sla_excess = (df_final["unplanned_downtime_hours"] - df_final["sla_hours"]).clip(lower=0)
df_final["sla_penalty"] = (
    sla_excess * df_final["failure_probability"] * df_final["revenue_per_hour"]
)

df_final["expected_cost_of_inaction"] = (
    df_final["sla_penalty"] + df_final["downtime_rev_loss"]
)

df_final["expected_cost_of_preventive_action"] = (
    df_final["planned_downtime_hours"] * df_final["revenue_per_hour"]
    + PREVENTIVE_ACTION_FIXED_COST
)

df_final["net_benefit"] = (
    df_final["expected_cost_of_inaction"] - df_final["expected_cost_of_preventive_action"]
)

# ── Build per-device output ───────────────────────────────────────────────────
per_device = df_final[[
    "device_id", "device_type", "customer_name",
    "failure_probability", "revenue_per_hour", "sla_hours",
    "unplanned_downtime_hours", "planned_downtime_hours",
    "downtime_rev_loss", "sla_penalty",
    "expected_cost_of_inaction",
    "expected_cost_of_preventive_action",
    "net_benefit"
]].to_dict(orient="records")

# ── Aggregate totals ──────────────────────────────────────────────────────────
totals = {
    "total_downtime_rev_loss":  df_final["downtime_rev_loss"].sum(),
    "total_sla_penalty":        df_final["sla_penalty"].sum(),
    "total_cost_of_inaction":   df_final["expected_cost_of_inaction"].sum(),
    "total_cost_of_prevention": df_final["expected_cost_of_preventive_action"].sum(),
    "total_net_benefit":        df_final["net_benefit"].sum(),
}

# ── Build maintenance log record ──────────────────────────────────────────────
log_record = {
    "timestamp":          datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    "device_id":          df_final["device_id"].iloc[0],
    "customer_name":      df_final["customer_name"].iloc[0],
    "engineer_assigned":  "James Carter",          # updated dynamically via Lovable approval form
    "maintenance_date":   "2026-03-21",             # updated dynamically via Lovable approval form
    "cost_of_inaction":   round(df_final["expected_cost_of_inaction"].sum(), 2),
    "cost_of_prevention": round(df_final["expected_cost_of_preventive_action"].sum(), 2),
    "net_benefit":        round(df_final["net_benefit"].sum(), 2),
    "decision":           "Approved",
}

# ── Return all outputs ────────────────────────────────────────────────────────
return {
    "per_device":             per_device,
    "totals":                 totals,
    "high_risk_device_count": len(df_final),
    "log_record":             log_record,
}
