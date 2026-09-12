"""
UI Components and Styling for BankFreeze AI
Provides financial-grade cards, status badges, confidence chips, timelines, and alert banners.
"""

import streamlit as st
from typing import List, Dict, Any, Optional

def inject_custom_css():
    """Inject modern, professional financial case-management styling."""
    st.markdown("""
    <style>
        /* Main Container Styling */
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 95%;
        }

        /* Banner styling */
        .demo-warning-banner {
            background-color: #fff3cd;
            border-left: 5px solid #ffeeba;
            border-radius: 4px;
            padding: 10px 16px;
            margin-bottom: 20px;
            color: #856404;
            font-size: 0.88rem;
            font-weight: 500;
        }

        /* Metric Cards */
        .metric-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 14px 18px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            transition: all 0.2s ease;
        }
        .metric-card:hover {
            border-color: #cbd5e1;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        }
        .metric-label {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .metric-value {
            font-size: 1.6rem;
            font-weight: 700;
            color: #0f172a;
        }

        /* Status Badges */
        .badge {
            display: inline-block;
            padding: 3px 9px;
            font-size: 0.74rem;
            font-weight: 600;
            border-radius: 9999px;
            letter-spacing: 0.03em;
            text-transform: uppercase;
        }
        .badge-info { background-color: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
        .badge-warning { background-color: #fef3c7; color: #b45309; border: 1px solid #fde68a; }
        .badge-danger { background-color: #fee2e2; color: #b91c1c; border: 1px solid #fecaca; }
        .badge-success { background-color: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
        .badge-neutral { background-color: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }

        /* Confidence Chips */
        .chip-high { background-color: #d1fae5; color: #065f46; font-weight: 700; padding: 2px 7px; border-radius: 4px; font-size: 0.75rem; }
        .chip-medium { background-color: #fef3c7; color: #92400e; font-weight: 700; padding: 2px 7px; border-radius: 4px; font-size: 0.75rem; }
        .chip-low { background-color: #fee2e2; color: #991b1b; font-weight: 700; padding: 2px 7px; border-radius: 4px; font-size: 0.75rem; }

        /* Timeline Items */
        .timeline-item {
            border-left: 2px solid #3b82f6;
            padding-left: 15px;
            margin-bottom: 15px;
            position: relative;
        }
        .timeline-item::before {
            content: "";
            position: absolute;
            left: -6px;
            top: 4px;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #3b82f6;
        }
        .timeline-time {
            font-size: 0.75rem;
            color: #94a3b8;
            font-weight: 600;
        }
        .timeline-title {
            font-size: 0.9rem;
            font-weight: 600;
            color: #1e293b;
        }
        .timeline-desc {
            font-size: 0.82rem;
            color: #475569;
        }
    </style>
    """, unsafe_allow_html=True)

def render_disclaimer():
    """Mandatory persistent demo system warning."""
    st.markdown("""
    <div class="demo-warning-banner">
        ⚠️ <strong>PROTOTYPE & DEMO SYSTEM:</strong>
        This system runs in an isolated synthetic demonstration mode. It does <strong>NOT</strong> connect to real banking systems,
        police departments, the 1930 NCRRP portal, or government databases. All adapter queries and sample records are synthetic.
    </div>
    """, unsafe_allow_html=True)

def render_status_badge(status: str) -> str:
    s = str(status).upper()
    if s in ["RESOLVED", "APPROVED", "COMPLETED", "MATCH"]:
        cls = "badge-success"
    elif s in ["NEW", "INFORMATION_RECEIVED", "CASE_ANALYSIS", "BANK_VERIFICATION"]:
        cls = "badge-info"
    elif s in ["WAITING_FOR_INFORMATION", "FOLLOW_UP_REQUIRED", "USER_REVIEW", "ACTION_REQUIRED", "PARTIAL"]:
        cls = "badge-warning"
    elif s in ["ESCALATION_REQUIRED", "CONFLICT_DETECTED", "MISMATCH", "REJECTED", "TOTAL_FREEZE"]:
        cls = "badge-danger"
    else:
        cls = "badge-neutral"
    return f'<span class="badge {cls}">{status}</span>'

def render_confidence_badge(confidence: str) -> str:
    c = str(confidence).upper()
    if c == "HIGH":
        return '<span class="chip-high">CONFIDENCE: HIGH</span>'
    elif c == "MEDIUM":
        return '<span class="chip-medium">CONFIDENCE: MED</span>'
    else:
        return '<span class="chip-low">CONFIDENCE: LOW</span>'

def render_fact_badge(fact_type: str) -> str:
    f = str(fact_type).upper()
    if f == "EXTRACTED":
        return '<span class="badge badge-success">EXTRACTED</span>'
    elif f == "INFERRED":
        return '<span class="badge badge-warning">INFERRED</span>'
    else:
        return '<span class="badge badge-danger">MISSING</span>'

def render_reconciliation_badge(status: str) -> str:
    s = str(status).upper()
    if s == "MATCH":
        return '<span class="badge badge-success">MATCH ✓</span>'
    elif s == "MISMATCH":
        return '<span class="badge badge-danger">MISMATCH ✖</span>'
    elif s == "PARTIAL":
        return '<span class="badge badge-warning">PARTIAL ⚠</span>'
    else:
        return '<span class="badge badge-neutral">MISSING ?</span>'

def render_metric_card(label: str, value: Any, icon: str = ""):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{icon} {label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)
