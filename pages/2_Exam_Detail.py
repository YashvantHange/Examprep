# pages/2_Exam_Detail.py
import streamlit as st
from backend.db import SessionLocal
from backend.crud import get_exam_by_id, list_topics_by_exam, list_exams
st.set_page_config(
    page_title="Exam Detail",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",  # <- collapse sidebar on load
)

st.set_page_config(page_title="Exam Details", page_icon="ℹ️", layout="wide")

# ---------- Helpers ----------
def hydrate_exam_from_id(exam_id: int):
    db = SessionLocal()
    ex = get_exam_by_id(db, exam_id)
    tps = list_topics_by_exam(db, exam_id) if ex else []
    all_exams = list_exams(db, limit=200, offset=0)["items"]
    db.close()
    return ex, tps, all_exams

def exam_insights(title: str):
    t = title.lower()
    if "security+" in t or "security plus" in t:
        return {
            "tagline": "Vendor-neutral baseline cert for modern cybersecurity roles.",
            "why": [
                "Global recognition for foundational security skills.",
                "Covers network security, risk, cryptography, IAM, compliance.",
                "Opens doors to SOC Analyst, Jr. Security Analyst, IT Security Support."
            ],
            "prep": [
                "Study official objectives domain-by-domain; build a revision map.",
                "Practice timed mocks to finish 10–15% faster than limit.",
                "Maintain an error log; revisit weak domains twice a week.",
                "Set up a small lab (VMs/containers) for hands-on: Wireshark, nmap, TLS configs."
            ],
            "strategy": [
                "Sweep for quick wins first; flag time sinks to revisit.",
                "For scenario items, read the last line first, then scan details.",
                "Eliminate two wrong options quickly; make an educated choice.",
                "Leave 2–3 minutes to review marked questions."
            ],
            "resources": [
                "CompTIA Exam Objectives (latest SY0-xxx)",
                "Professor Messer/CertMike videos",
                "OWASP Top 10 quick read (web security contexts)",
                "Practice labs: packet capture, TLS, access control"
            ],
        }
    if "ceh" in t or "ethical hacker" in t:
        return {
            "tagline": "Offensive security focus: recon → exploitation → reporting.",
            "why": [
                "Demonstrates practical attacker mindset for red team roles.",
                "Hands-on with tooling (Nmap, Metasploit, Burp Suite, Hydra).",
                "Valued for Pentester, Red Team, Vulnerability Assessor roles."
            ],
            "prep": [
                "Build a lab (2–3 VMs): target + attacker (Kali) + optional Windows.",
                "Daily reps: scanning (nmap), web vulns (Burp), Linux priv-esc patterns.",
                "Log each technique: command + purpose + typical output signature.",
                "Weekly CTF or HTB boxes to sharpen enumeration discipline."
            ],
            "strategy": [
                "Enumerate systematically: services → versions → likely exploits.",
                "Prioritize misconfig/simple creds before complex chains.",
                "For web items, think input → trust boundary → sink (XSS/SQLi/XXE/SSRF).",
                "Report like a pro: risk, repro steps, fix, and business impact."
            ],
            "resources": [
                "Kali tool docs (nmap, enum4linux, gobuster, sqlmap, msfconsole)",
                "OWASP Testing Guide (web techniques)",
                "Hack The Box / TryHackMe tracks (Beginner → Intermediate)",
                "GTFOBins (priv-esc primitives)"
            ],
        }
    if "aws solutions architect" in t or "aws saa" in t or "solutions architect" in t:
        return {
            "tagline": "Design resilient, secure, cost-optimized architectures on AWS.",
            "why": [
                "High market demand for cloud solution skills.",
                "Validates VPC, EC2, S3, RDS, IAM, Route 53, KMS, WAF patterns.",
                "Bridges DevOps, SysOps, and architecture career paths."
            ],
            "prep": [
                "Master core blueprints: 3-tier VPC, multi-AZ RDS, S3 patterns, ALB/NLB.",
                "Cost models: S3 tiers, EC2 purchasing options, data transfer.",
                "Security: IAM least privilege, KMS, SCPs, WAF, private endpoints.",
                "Hands-on: build/deploy reference stacks; break and harden."
            ],
            "strategy": [
                "For long scenarios: capture requirements (HA, RTO/RPO, latency, cost).",
                "Choose simplest service that meets constraints (avoid over-engineering).",
                "Eliminate answers that violate core guarantees (AZ isolation, durability).",
                "Mind the defaults: SGs stateful, NACLs stateless, S3 11x9’s durability."
            ],
            "resources": [
                "AWS Well-Architected Framework",
                "Official Exam Guide + sample questions",
                "AWS docs for VPC, S3, RDS, IAM, KMS, Route 53, WAF",
                "Hands-on with Console + IaC (CloudFormation/Terraform)"
            ],
        }    
    # --- CompTIA CySA+ (CS0-003) ---
    if "cysa" in t or "cs0-003" in t or "cybersecurity analyst" in t:
        return {
            "tagline": "SOC-focused: detect, investigate, and respond using SIEM & analytics.",
            "domains": [
                ("Security Operations", "≈33%"),
                ("Vulnerability Management", "≈30%"),
                ("Incident Response & Management", "≈20%"),
                ("Reporting & Communication", "≈17%"),
            ],
            "why": [
                "Bridges blue-team skills: threat detection, triage, and response.",
                "Hands-on with SIEM, EDR, vulnerability scanners, and ticketing workflows.",
                "Highly relevant for SOC Analyst / Blue Team roles."
            ],
            "prep": [
                "Practice SIEM queries (KQL/SPL concepts), Alerts → Cases workflow.",
                "Run vuln scans (Nessus/OpenVAS), triage true vs false positives.",
                "Study incident lifecycle: prep → detect → contain → eradicate → recover → lessons learned.",
                "Create IR reports with IOCs, timeline, impact, and remediation."
            ],
            "strategy": [
                "From logs, identify indicators first (IPs, hashes, process paths).",
                "Correlate alerts across sources (host, network, identity).",
                "Prioritize by asset criticality and risk; avoid rabbit holes.",
                "Separate detection evidence from root cause in scenarios."
            ],
            "resources": [
                "CompTIA CySA+ (CS0-003) Exam Objectives",
                "Blue-team labs: HELK/Elastic/Splunk, Sysmon, Zeek",
                "MITRE ATT&CK mapping practice",
                "Vuln management with CVSS & remediation SLAs"
            ],
        }

    # --- CompTIA PenTest+ (PT0-002) ---
    if "pentest+" in t or "pt0-002" in t or "penetration tester" in t:
        return {
            "tagline": "End-to-end ethical hacking: scope → recon → exploit → report.",
            "domains": [
                ("Planning & Scoping", "≈14%"),
                ("Information Gathering & Vulnerability Identification", "≈22%"),
                ("Attacks & Exploits", "≈30%"),
                ("Reporting & Communication", "≈18%"),
                ("Tools & Code Analysis", "≈16%"),
            ],
            "why": [
                "Proves practical offensive skills aligned to real engagements.",
                "Emphasizes methodology, tool fluency, and clean reporting.",
                "Ideal for Junior Pentester / AppSec / Red Team pipeline."
            ],
            "prep": [
                "Scope safely: rules of engagement, legal constraints, success criteria.",
                "Deepen recon: DNS, OSINT, service enum, web dirs, creds sources.",
                "Exploit with discipline: validate, capture evidence, minimize noise.",
                "Practice professional reporting: findings, risk, repro, fix, impact."
            ],
            "strategy": [
                "Follow a clear chain: discovery → vuln → exploit → post-exploit.",
                "For web items, reason input → trust boundary → sink (XSS/SQLi/XXE/SSRF).",
                "Pick the minimal exploit that proves impact; avoid collateral.",
                "Always map to business risk in report-style questions."
            ],
            "resources": [
                "PTES / NIST SP 800-115",
                "OWASP Testing Guide",
                "TryHackMe / Hack The Box (Pentest paths)",
                "Kali tools: nmap, gobuster, wfuzz, Burp Suite, sqlmap, metasploit"
            ],
        }

    # --- AWS Certified Security – Specialty ---
    if ("aws certified security" in t) or ("security – specialty" in t) or ("security specialty" in t):
        return {
            "tagline": "Design and operate secure workloads on AWS at scale.",
            "domains": [
                ("Incident Response", "≈12%"),
                ("Logging & Monitoring", "≈20%"),
                ("Infrastructure Security", "≈26%"),
                ("Identity & Access Management", "≈20%"),
                ("Data Protection", "≈22%"),
            ],
            "why": [
                "Validates deep AWS security patterns (KMS, IAM, GuardDuty, WAF).",
                "High-impact for cloud security engineer & architect roles.",
                "Focus on detective, preventive, and responsive controls."
            ],
            "prep": [
                "Org-wide guardrails: SCPs, IAM boundaries, Config rules.",
                "Encrypt everywhere: KMS CMKs, S3 bucket keys, EBS/RDS encryption.",
                "Centralize logs: CloudTrail, CloudWatch Logs, S3 → Lake → Athena.",
                "IR playbooks with GuardDuty/Macie findings and automation."
            ],
            "strategy": [
                "Identify constraints: isolation, encryption, rotation, zero trust.",
                "Pick the simplest native service that meets the requirement.",
                "Beware of data movement & cross-account implications.",
                "Prefer managed services for scale and consistency."
            ],
            "resources": [
                "AWS Security Pillar (Well-Architected)",
                "AWS Security Workshop content & labs",
                "Docs: KMS, IAM, GuardDuty, Security Hub, Macie, WAF, Detective",
                "Sample questions & re:Invent security sessions"
            ],
        }

    # --- ISC² Certified in Cybersecurity (CC) ---
    if "isc2 cc" in t or "certified in cybersecurity" in t or t.strip() == "cc":
        return {
            "tagline": "Entry-level cybersecurity fundamentals—great first credential.",
            "domains": [
                ("Security Principles", "26%"),
                ("BC/DR/IR", "10%"),
                ("Access Controls", "22%"),
                ("Network Security", "24%"),
                ("Security Operations", "18%"),
            ],
            "why": [
                "Covers core concepts for helpdesk, junior analyst, and IT roles.",
                "Good stepping stone toward Security+ and SSCP/CISSP later.",
                "Recognized as proof of baseline cybersecurity knowledge."
            ],
            "prep": [
                "Learn CIA triad, risk, policy, & governance basics.",
                "Practice access models (RBAC/ABAC), authn vs authz, MFA.",
                "Understand network layers, protocols, and segmentation.",
                "Study incident basics and business continuity principles."
            ],
            "strategy": [
                "Read carefully—many items test precise terminology.",
                "Use elimination and relate options to clear definitions.",
                "Prefer best-practice answers (least privilege, defense-in-depth).",
                "Mind the order: policy → standards → procedures → guidelines."
            ],
            "resources": [
                "ISC² CC Official Study Materials",
                "NIST / ISO quick reads on controls & risk",
                "Glossaries: NIST, CIS Controls",
                "Entry-level practice tests & flashcards"
            ],
        }

    # Default generic (fallback)
    return {
        "tagline": "Boost your mastery with focused practice and a clear strategy.",
        "domains": None,
        "why": [
            "Demonstrates structured problem-solving and up-to-date skills.",
            "Signals commitment and readiness for professional roles."
        ],
        "prep": [
            "Map objectives → resources → checkpoints.",
            "Do timed mocks; maintain an error log; revisit weak topics."
        ],
        "strategy": [
            "Quick wins first; flag hard items; review at the end.",
            "Use elimination; make an informed choice when unsure."
        ],
        "resources": [
            "Official objectives/blueprints",
            "High-quality video/course series",
            "Hands-on labs aligned to domains"
        ],
    }


def stat_card(label: str, value: str):
    with st.container(border=True):
        st.markdown(f"**{label}**")
        st.markdown(f"<h3 style='margin:0'>{value}</h3>", unsafe_allow_html=True)

def pill(text: str):
    st.markdown(f"<div style='display:inline-block;padding:6px 10px;border-radius:999px;border:1px solid #e5e7eb;margin:4px 6px 0 0'>{text}</div>", unsafe_allow_html=True)

# ---------- Resolve exam ----------
qp = st.query_params
exam_id_param = qp.get("exam_id")

exam_obj, topics, all_exams = (None, [], [])
if exam_id_param and str(exam_id_param).isdigit():
    exam_obj, topics, all_exams = hydrate_exam_from_id(int(exam_id_param))
else:
    st.title("ℹ️ Exam Details")
    st.info("Pick an exam to view details.")
    db = SessionLocal()
    data = list_exams(db, limit=200, offset=0)
    all_exams = data["items"]
    db.close()
    if not all_exams:
        st.warning("No exams found. Please seed data first.")
        st.stop()
    choices = {f"{e.title} ({e.category})": e.id for e in all_exams}
    chosen = st.selectbox("Select an exam", options=list(choices.keys()))
    if chosen:
        st.query_params["exam_id"] = str(choices[chosen])
        st.rerun()

if not exam_obj:
    st.stop()

# ---------- Other Exams on Top ----------
others = [e for e in all_exams if e.id != exam_obj.id]
if others:
    st.subheader("🗂️ Switch to Another Exam")
    cols = st.columns(3)
    for i, e in enumerate(others):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"### {e.title}")
                st.caption(f"Category: **{getattr(e, 'category', 'General')}** · Difficulty: **{getattr(e, 'difficulty', 'Medium')}** · Time: **{getattr(e, 'time_limit', 60)} min**")
                st.write((e.description or "")[:120] + ("…" if e.description and len(e.description) > 120 else ""))
                if st.button("View details", key=f"view_{e.id}"):
                    st.query_params["exam_id"] = str(e.id)
                    st.rerun()

# ---------- Current Exam Detail ----------
exam = {
    "id": exam_obj.id,
    "title": exam_obj.title,
    "category": getattr(exam_obj, "category", "General"),
    "difficulty": getattr(exam_obj, "difficulty", "Medium"),
    "time_limit": getattr(exam_obj, "time_limit", 60),
    "description": getattr(exam_obj, "description", "") or "",
}
ins = exam_insights(exam["title"])

st.title(f"ℹ️ {exam['title']} — Exam Details")
st.caption(f"Your guide to ace this certification.")

with st.container(border=True):
    c1, c2, c3, c4 = st.columns([2,1,1,1])
    with c1:
        st.subheader(exam["title"])
        st.write(exam["description"] or "No description available yet.")
        st.caption(ins["tagline"])
    with c2:
        stat_card("Category", exam["category"])
    with c3:
        stat_card("Difficulty", exam["difficulty"])
    with c4:
        stat_card("Duration", f"{exam['time_limit']} min")

# Topics
st.subheader("📂 Topics Covered")
if topics:
    cols = st.columns(3)
    for i, t in enumerate(topics):
        with cols[i % 3]:
            pill(t.name)
else:
    st.info("Topics will be updated soon.")

# Why / Prep / Strategy / Resources
st.subheader("🎯 Why take this exam?")
for item in ins["why"]:
    st.markdown(f"- {item}")

st.subheader("🛠️ Preparation Tips")
for item in ins["prep"]:
    st.markdown(f"- {item}")

st.subheader("✅ Passing Strategy")
for item in ins["strategy"]:
    st.markdown(f"- {item}")

st.subheader("📚 Suggested Resources")
for item in ins["resources"]:
    st.markdown(f"- {item}")

st.markdown("---")
cta1, cta2 = st.columns(2)
with cta1:
    if st.button("⚙️ Configure This Exam"):
        st.session_state["exam_selected"] = exam
        st.switch_page("pages/7_Configure_Exam.py")
with cta2:
    if st.button("🏠 Back to Home"):
        st.query_params.pop("exam_id", None)
        st.switch_page("app.py")
