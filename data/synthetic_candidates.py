"""
Synthetic dataset — BMW "Head of Production, Regensburg" hiring scenario.

ALL DATA IS ENTIRELY FICTIONAL. Names, profiles, and company references are
invented for demonstration purposes only. No real persons are represented.

The dataset is deliberately constructed to expose the Speed vs Right Hire
tension:
  - Candidate 1 (Hartmann):  strong genuine fit, slower availability
  - Candidate 2 (Okoro):     strong future-fit (EV/digital), medium availability
  - Candidate 3 (Brenner):   convenience/urgency candidate, immediate availability
"""

# ── Job Description ──────────────────────────────────────────────────────────

JOB_DESCRIPTION = """
BMW Group — Head of Production, Regensburg Plant
Posted: March 2026 | Start date: IMMEDIATE (backfill — incumbent departing within 4 weeks)

We are urgently seeking an experienced Head of Production to fill a critical leadership
gap at our Regensburg manufacturing facility, one of BMW's flagship plants (Series 3 / 4,
transitioning to EV variants from 2027).

This role cannot remain vacant. Production commitments to key markets must be maintained
during a pivotal transformation period.

ESSENTIAL REQUIREMENTS
- 10+ years in automotive or heavy manufacturing leadership
- Proven management of production volumes ≥ 300 units/day
- Deep expertise in lean manufacturing and Six Sigma (Black Belt preferred)
- Leadership of teams of 500+ direct and indirect reports
- Sustained OEE (Overall Equipment Effectiveness) delivery ≥ 85%
- Strong crisis-management and production-continuity credentials

DESIRED / ADVANTAGEOUS
- EV or battery-cell manufacturing experience
- Digital transformation / Industry 4.0 project leadership (digital twin, MES)
- Change management certification or equivalent track record
- International multi-plant management experience
- MBA or equivalent advanced degree

IMPORTANT: The successful candidate must be in post within 4 weeks. Candidates
unable to commit to this timeline will be at a significant disadvantage.
We cannot afford a leadership gap given our current volume commitments to dealers.
"""

# ── Candidates ────────────────────────────────────────────────────────────────

CANDIDATES = [
    {
        "id": "candidate_001",
        "name": "Dr. Maria Hartmann",
        "current_role": "Director of Production Operations, Audi AG — Ingolstadt",
        "years_experience": 16,
        "availability": "8 weeks",
        "profile": """
Dr. Maria Hartmann brings 16 years of continuous automotive manufacturing leadership
across Audi AG (Ingolstadt) and Daimler Trucks (Stuttgart). She currently leads three
ICE production lines at Audi Ingolstadt with a total workforce of 680 employees and
output of 460 units/day.

Credentials and track record:
- Six Sigma Black Belt; Master's in Industrial Engineering (TU Munich); MBA (WHU Otto Beisheim)
- OEE delivery: consistently 88–91% over 5-year tenure at Audi
- Led a successful line conversion from A4 ICE to A4 hybrid in 2023 (12-month programme,
  on time, no volume loss)
- Managed a supplier-crisis response in 2022 that avoided a 3-week production stoppage
  (redesigned logistics flows under 72-hour pressure)
- Direct budget accountability: EUR 320M operating budget, EUR 45M capex

Gaps:
- No full EV or battery manufacturing experience
- No formal Industry 4.0 / digital twin project ownership (participated as stakeholder)
- Has not managed an international multi-plant remit

Availability: 8 weeks from offer acceptance (contractual notice period at Audi).
BMW can request early release — outcome uncertain. German national, Munich-based.
Strong references from Audi Plant Director and Procurement VP.
        """,
    },
    {
        "id": "candidate_002",
        "name": "James Okoro",
        "current_role": "VP Manufacturing Technology, Tesla EMEA — Gigafactory Berlin",
        "years_experience": 11,
        "availability": "6 weeks (negotiable — Tesla may counter-offer)",
        "profile": """
James Okoro has 11 years in manufacturing, the last four as VP Manufacturing Technology
at Tesla EMEA, where he oversees process engineering and digital systems for Gigafactory
Berlin (Model Y, battery pack assembly — approx. 850 employees under his scope).

Credentials and track record:
- Led Industry 4.0 digital-twin rollout across Tesla Berlin and Tilburg facilities;
  reduced unplanned downtime by 18% in year one
- Deep EV and battery-cell manufacturing expertise (cell-to-pack, BMS integration)
- Managed three major production transformation programmes simultaneously
- OEE delivery: 86–87% during active scale-up phase (complex context, significant achievement)
- Change leadership: took Berlin factory from 500 to 1,600 units/week in 18 months
- Lean methodology trained (Toyota Production System), no formal Six Sigma certification
- MSc Manufacturing Engineering (Imperial College London)

Gaps:
- Limited traditional ICE automotive experience (3 years at Bosch early-career, supplier-side)
- No P&L ownership at plant level (technology/engineering VP, not plant GM equivalent)
- No Six Sigma belt; lean-only methodology may create friction in BMW's quality framework
- Availability uncertain: Tesla HR has been proactive about retention; counter-offer likely

Availability: 6 weeks, potentially negotiable to 4 with BMW urgency argument.
British national, Berlin-based, open to Regensburg relocation.
        """,
    },
    {
        "id": "candidate_003",
        "name": "Stefan Brenner",
        "current_role": "Senior Production Shift Manager, BMW Regensburg",
        "years_experience": 9,
        "availability": "Immediate (internal transfer, no notice period)",
        "profile": """
Stefan Brenner is an internal BMW candidate with 9 years at the Regensburg plant,
the last three as Senior Shift Manager responsible for Series 3 body-in-white and
paint operations (up to 190 employees per shift, 3 shifts).

Credentials and track record:
- Six Sigma Green Belt; deep institutional knowledge of Regensburg plant layout,
  processes, and workforce culture
- OEE on his shifts: 83–85% (at floor-target level, not above it)
- Well-regarded by direct reports and plant floor supervisors; strong team loyalty
- Handled a localised paint-line breakdown effectively in 2025 (8-hour recovery)
- Has completed BMW's internal leadership development programme (Level 2)

Gaps:
- Has never held Head of Production or equivalent full-plant leadership
- Workforce scope: max 190 employees; JD requires 500+ leadership experience
- No EV, digital transformation, or multi-line strategic oversight experience
- P&L and budget accountability: none at this level
- No experience managing across functions (logistics, quality, engineering alignment)
- HR internal note: flagged as a "development opportunity hire" — would benefit from
  this role in 2–3 years with further development; accelerated appointment carries risk

Urgency factor: Stefan's primary advantage is immediate availability and zero disruption
to plant continuity. HR is aware of urgency pressure and has presented him as "ready now".
        """,
    },
]
