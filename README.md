# 🔧 Device Risk Analysis & Notification Pipeline

An end-to-end automated pipeline built on **Relevance AI** that identifies high-risk devices, calculates financial impact, and orchestrates a full notification and scheduling workflow — all without manual intervention.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Knowledge Tables](#knowledge-tables)
- [Pipeline Steps](#pipeline-steps)
- [Financial Calculations](#financial-calculations)
- [Setup & Installation](#setup--installation)
- [Project Structure](#project-structure)
- [Sample Output](#sample-output)

---

## Overview

This pipeline automatically:

1. Scans device telemetry data for failure probabilities ≥ 0.85
2. Calculates cost of inaction vs. cost of preventive maintenance
3. Emails the manager with a full risk analysis and engineer availability
4. Notifies the customer about scheduled maintenance
5. Assigns and notifies the engineer via email
6. Creates a calendar block in Outlook via Make.com webhook
7. Logs the maintenance decision to a database

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RELEVANCE AI TOOL                        │
│                                                             │
│  Knowledge Tables (x4)                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ device_data  │  │customer_data │  │incident_data │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         └─────────────────┼─────────────────┘              │
│                           ▼                                 │
│                  ┌────────────────┐                         │
│                  │ Python Step    │                         │
│                  │ (calculations) │                         │
│                  └────────┬───────┘                         │
│                           ▼                                 │
│            ┌──────────────────────────┐                     │
│            │   LLM → Gmail (Manager)  │                     │
│            └──────────────────────────┘                     │
│                           ▼                                 │
│            ┌──────────────────────────┐                     │
│            │  LLM → Gmail (Customer)  │                     │
│            └──────────────────────────┘                     │
│                           ▼                                 │
│            ┌──────────────────────────┐                     │
│            │  LLM → Outlook (Engineer)│                     │
│            └──────────────────────────┘                     │
│                           ▼                                 │
│            ┌──────────────────────────┐                     │
│            │  API → Make.com Webhook  │                     │
│            │  → Outlook Calendar      │                     │
│            └──────────────────────────┘                     │
│                           ▼                                 │
│            ┌──────────────────────────┐                     │
│            │  Insert Knowledge (Log)  │                     │
│            └──────────────────────────┘                     │
│                           ▼                                 │
│            ┌──────────────────────────┐                     │
│            │  LLM Success Message     │                     │
│            └──────────────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Pipeline Orchestration | [Relevance AI](https://relevanceai.com) |
| Data Storage | Relevance AI Knowledge Tables |
| Calculations | Python (pandas) |
| AI/LLM | Claude (via Relevance AI) |
| Email (Manager/Customer) | Outlook API (via Relevance AI) |
| Email (Engineer) | Microsoft Outlook (via Relevance AI) |
| Calendar | Microsoft Outlook Calendar via Make.com Webhook |
| Automation | [Make.com](https://make.com) |
| Version Control | GitHub |

---

## Knowledge Tables

### `device_failure_dataset`
| Column | Type | Description |
|---|---|---|
| device_id | string | Unique device identifier |
| device_type | string | Type/model of device |
| failure_probability | float | Predicted failure probability (0.0 - 1.0) |

### `customers_sla`
| Column | Type | Description |
|---|---|---|
| device_id | string | Links to device table |
| customer_name | string | Customer name |
| revenue | float | Revenue per hour ($) |
| sla_hours | float | SLA threshold in hours |

### `incidency_history`
| Column | Type | Description |
|---|---|---|
| device_type | string | Device type |
| failure_probability | float | Bucket (0.5, 0.6, 0.7, 0.8, 0.9, 1.0) |
| planned_downtime_hours | float | Hours for planned maintenance |
| unplanned_downtime_hours | float | Hours for unplanned failure |

### `engineer_availability`
| Column | Type | Description |
|---|---|---|
| name | string | Engineer full name |
| email | string | Engineer email |
| av_date_1 | string | Available date 1 |
| av_date_2 | string | Available date 2 |
| av_date_3 | string | Available date 3 |

### `maintenance_log`
| Column | Type | Description |
|---|---|---|
| timestamp | string | UTC timestamp of decision |
| device_id | string | Device flagged |
| customer_name | string | Affected customer |
| engineer_assigned | string | Assigned engineer |
| maintenance_date | string | Scheduled date |
| cost_of_inaction | float | Expected cost if no action |
| cost_of_prevention | float | Cost of preventive action |
| net_benefit | float | Financial benefit of acting |
| decision | string | Approved / Rejected |

---

## Pipeline Steps

| # | Step Type | Name | Description |
|---|---|---|---|
| 1 | Get Knowledge | device_data | Fetch all device telemetry |
| 2 | Get Knowledge | customer_data | Fetch customer SLA data |
| 3 | Get Knowledge | incident_data | Fetch incident history |
| 4 | Get Knowledge | engineer_data | Fetch engineer availability |
| 5 | Python | python | Filter, merge, calculate financials |
| 6 | LLM | llm_manager_email | Generate HTML manager email |
| 7 | Send Gmail | send_manager_email | Email manager with risk summary |
| 8 | LLM | llm_customer_email | Generate customer notification |
| 9 | Send Gmail | send_customer_email | Email customer |
| 10 | LLM | llm_engineer_email | Generate engineer assignment email |
| 11 | Send Outlook | send_engineer_email | Email engineer |
| 12 | API Call | calendar_make | POST to Make.com → Outlook Calendar |
| 13 | Insert Knowledge | insert_knowledge_data | Log record to maintenance_log |
| 14 | LLM | success_message | Generate final success summary |

---

## Financial Calculations

```
Downtime Revenue Loss  = unplanned_downtime_hours × revenue_per_hour

SLA Excess             = max(0, unplanned_downtime_hours − sla_hours)
SLA Penalty            = sla_excess × failure_probability × revenue_per_hour

Cost of Inaction       = downtime_revenue_loss + sla_penalty

Cost of Prevention     = (planned_downtime_hours × revenue_per_hour) + $3,000 fixed cost

Net Benefit            = cost_of_inaction − cost_of_prevention
```

### Sample Output (Device D3750 — Bank of Seattle)

| Metric | Value |
|---|---|
| Failure Probability | 0.85 |
| Revenue per Hour | $6,900 |
| Unplanned Downtime | 3.6 hrs |
| Planned Downtime | 2.8 hrs |
| Downtime Revenue Loss | $24,840.00 |
| SLA Penalty | $13,489.50 |
| **Cost of Inaction** | **$38,329.50** |
| **Cost of Prevention** | **$22,320.00** |
| **Net Benefit** | **$16,009.50** |

---

## Setup & Installation

### Prerequisites
- [Relevance AI](https://relevanceai.com) account
- Gmail account connected to Relevance AI
- Microsoft Outlook account connected to Relevance AI
- [Make.com](https://make.com) account

### Steps

1. **Clone this repository**
```bash
git clone https://github.com/YOUR_USERNAME/device-risk-analysis.git
cd device-risk-analysis
```

2. **Upload Knowledge Tables** to Relevance AI
   - Import `data/engineer_availability.csv` as `engineer_availability` table
   - Create remaining tables manually or via CSV upload

3. **Create Tool** in Relevance AI
   - Follow step configuration in `relevance-ai/tool_config.yaml`
   - Copy Python code from `relevance-ai/python_calculation.py`

4. **Configure Make.com Webhook**
   - Create scenario: Custom Webhook → Microsoft 365 Calendar (Create Event)
   - Update webhook URL in Relevance AI API step
   - Reference payload structure in `make-com/webhook_payload.json`

5. **Run the tool** in Relevance AI

---

## Project Structure

```
device-risk-analysis/
├── README.md
├── relevance-ai/
│   ├── python_calculation.py    # Core Python calculation script
│   └── tool_config.yaml         # Full tool step configuration
├── make-com/
│   └── webhook_payload.json     # Calendar webhook payload structure
└── data/
    └── engineer_availability.csv
```

---

## Sample Output

```
1. Device D3750 flagged for preventive maintenance with a failure probability of 0.85.
2. Customer: Bank of Seattle; revenue at risk: $6,900 per hour.
3. Cost of inaction: $38,329.50; cost of prevention: $22,320; net benefit: $16,009.50.
4. Manager has been notified via email with full risk analysis and engineer availability table.
5. Manager has approved the preventive maintenance request.
6. Engineer James Carter has been assigned and notified via email.
7. Customer Bank of Seattle has been notified via email about scheduled maintenance on 21 Mar 2026.
8. Calendar block created for James Carter on 21 Mar 2026 from 9:00 AM to 11:00 AM.
9. Maintenance log record saved to database with timestamp: 2026-03-07 22:00:15.

All automated actions have been completed successfully.
```
