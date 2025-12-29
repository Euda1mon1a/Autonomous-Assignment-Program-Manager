# Scheduling System Policies

## Overview

The Residency Scheduler is a comprehensive scheduling system designed to create and manage medical residency schedules while ensuring ACGME compliance, maintaining coverage requirements, and supporting resident well-being. This document outlines the core policies and operational procedures for the scheduling system.

## Block Structure

### Academic Year Organization

The academic year is organized into discrete time blocks that form the foundation of the scheduling system.

**Academic Year Structure:**
- **Duration:** 365 days (366 in leap years)
- **Total Blocks:** 730 blocks per academic year
- **Block Definition:** Each day is divided into AM and PM sessions
  - **AM Session:** Morning shift (typically 7:00 AM - 7:00 PM)
  - **PM Session:** Evening/night shift (typically 7:00 PM - 7:00 AM)

### Block Numbering

Blocks are numbered sequentially from the start of the academic year:
- **Day 1, AM:** Block 1
- **Day 1, PM:** Block 2
- **Day 2, AM:** Block 3
- **Day 2, PM:** Block 4
- And so on through Day 365, PM (Block 730)

This numbering system allows for precise assignment tracking and schedule generation.

### Block Duration Standards

While most blocks follow the standard 12-hour AM/PM pattern, certain rotations may have different scheduling patterns:
- **Standard Clinical Blocks:** 12 hours (AM or PM)
- **Call Blocks:** May extend 24+ hours (subject to ACGME 28-hour maximum)
- **Half-Day Blocks:** Used for clinics, conferences, or administrative time
- **Off Blocks:** Vacation, conference leave, or scheduled days off

## Rotation Types and Templates

### Core Rotation Categories

The system supports multiple rotation types that define the nature of resident assignments:

**1. Inpatient Rotations**
- General medicine wards
- Subspecialty inpatient services (cardiology, pulmonary, etc.)
- Intensive care units (ICU, CCU)
- Typically require 24/7 coverage with shift or call structure

**2. Outpatient Clinic Rotations**
- Continuity clinic (longitudinal primary care)
- Subspecialty clinics
- Typically scheduled during standard business hours
- May be half-day blocks

**3. Procedure Rotations**
- Endoscopy, bronchoscopy, cardiac catheterization
- Operating room time
- Scheduled blocks with specific procedural goals

**4. Conference and Education**
- Didactic conferences
- Grand rounds
- Simulation training
- Board review sessions
- Protected educational time (cannot be displaced by clinical duties)

**5. Night Float**
- Dedicated overnight coverage rotation
- Typically 1-2 week blocks
- Residents work only night shifts during this period
- Facilitates ACGME compliance by consolidating night work

**6. Elective Rotations**
- Resident-selected experiences
- Subspecialty exploration
- Research time
- Away rotations at other institutions

### Rotation Templates

Each rotation type has a predefined template that specifies:
- **Block pattern:** Which AM/PM blocks are typically assigned
- **Duration:** Standard length (e.g., 4 weeks for most rotations)
- **Coverage requirements:** Minimum number of residents needed
- **Supervision requirements:** Faculty-to-resident ratios
- **Educational goals:** Competencies to be achieved

Templates ensure consistency while allowing flexibility for individual resident needs.

## Assignment Rules

### Assignment Structure

An **assignment** is the fundamental unit of the schedule, consisting of:
- **Person:** The resident or faculty member being assigned
- **Block(s):** The time period(s) for the assignment
- **Rotation:** The clinical or educational activity

### Assignment Validation

Before an assignment is finalized, the system validates:

**1. ACGME Compliance:**
- Will this assignment cause the resident to exceed 80 hours/week (4-week average)?
- Does the resident have 1 day off in 7 (4-week average)?
- Is there adequate rest between shifts (minimum 10 hours)?
- Does this assignment comply with PGY-specific restrictions?

**2. Schedule Conflicts:**
- Is the resident already assigned to another rotation during these blocks?
- Are there overlapping commitments (conferences, mandatory training)?
- Does this create double-booking situations?

**3. Coverage Requirements:**
- Does this maintain minimum staffing levels for the rotation?
- Are supervision ratios maintained?
- Is there adequate backup coverage?

**4. Credential Requirements:**
- Does the resident have required certifications (BLS, ACLS, etc.)?
- Are immunizations current?
- Has required training been completed (HIPAA, etc.)?

### Progressive Responsibility

Assignments respect the principle of progressive responsibility:
- **PGY-1:** More structured schedules, enhanced supervision, limited autonomy
- **PGY-2:** Increasing independence, more complex patients, teaching responsibilities
- **PGY-3+:** Near-autonomous practice, mentorship roles, leadership opportunities

The scheduling system tracks PGY level and adjusts assignment rules accordingly.

## Coverage Requirements

### Minimum Staffing Levels

Each rotation and clinical area has defined minimum coverage requirements:

**Inpatient Services:**
- **Day coverage:** Minimum 1 resident per 8-10 patients
- **Night coverage:** Minimum 1 overnight resident per 15-20 patients
- **ICU coverage:** Minimum 1 resident per 6-8 patients (higher acuity)

**Outpatient Clinics:**
- **Primary care clinic:** 1-2 residents per half-day session
- **Subspecialty clinic:** Variable based on volume and complexity
- **Procedure clinics:** 1 resident per attending physician

**Emergency Coverage:**
- **Weekend coverage:** Minimum same as weekday for inpatient services
- **Holiday coverage:** Reduced but adequate staffing (typically 75% of weekday)
- **Call coverage:** Always at least one resident on-call for admissions

### Coverage Gap Prevention

The system actively prevents coverage gaps through:

**1. Real-Time Gap Detection:**
- Identifies blocks where coverage falls below minimum requirements
- Alerts schedulers before gaps occur
- Suggests residents who could fill the gap without ACGME violations

**2. Automated Conflict Resolution:**
- When a resident requests time off, system checks for coverage impact
- Automatically suggests replacements from available residents
- Ensures replacements don't violate duty hour limits

**3. Contingency Planning:**
- N-1 analysis: Can the schedule survive if one resident is unavailable?
- N-2 analysis: Can critical services maintain coverage with two residents out?
- Identifies vulnerable periods where contingency planning is needed

## Schedule Change Procedures

### Types of Schedule Changes

**1. Planned Changes (>2 Weeks Notice):**
- Conference attendance
- Planned vacation
- Board examinations
- Interview days
- Request submitted through scheduling system
- Requires program director approval
- Automatically checks coverage impact

**2. Short-Notice Changes (2-14 Days):**
- Personal emergencies
- Sick leave
- Family obligations
- Requires chief resident and program director approval
- May trigger automatic swap matching to find replacement

**3. Emergency Changes (<48 Hours):**
- Medical emergencies
- Family emergencies
- Acute illness
- Immediate coverage needed
- Chief resident coordinates emergency coverage
- System logs all emergency changes for compliance tracking

### Change Request Process

**Step 1: Submit Request**
- Resident logs into scheduling system
- Selects dates/blocks requiring change
- Provides reason and classification (planned/short-notice/emergency)
- Submits for review

**Step 2: Coverage Check**
- System automatically validates coverage impact
- If coverage is adequate, request goes to approval queue
- If coverage is insufficient, system suggests swap options or alerts schedulers

**Step 3: Approval Workflow**
- **Planned changes:** Reviewed by program coordinator, approved by program director
- **Short-notice:** Reviewed by chief resident and program director
- **Emergency:** Chief resident immediately notified, coordinates coverage

**Step 4: Schedule Update**
- Approved changes are immediately reflected in the published schedule
- All affected parties receive automated notifications
- Updated schedule is available in real-time through web and mobile interfaces

### Schedule Publication Timeline

**Standard Schedule Publication:**
- **4-6 weeks in advance:** Core rotation schedules published
- **2-3 weeks in advance:** Call schedules and weekend coverage finalized
- **1 week in advance:** Final adjustments and confirmations
- **Changes after publication:** Require formal change request and approval

**Block Schedule Publication:**
- Each academic year is divided into ~13 blocks (4-week rotations)
- Block schedules published at least 6 weeks before block start
- Allows residents to plan personal commitments around schedule

## Rotation Balancing

### Equitable Distribution

The scheduling system ensures fair distribution of:

**1. Night Float Assignments:**
- All residents rotate through night float equally over the academic year
- Typically 2-4 blocks per year per resident
- Distributed to avoid consecutive night float blocks

**2. Weekend Coverage:**
- Weekend call distributed evenly across all residents
- Tracked over rolling 3-month periods
- No resident should have significantly more weekends than peers

**3. Holiday Coverage:**
- Major holidays (Christmas, New Year's, Thanksgiving) rotated annually
- No resident should work the same holiday multiple years in a row
- System tracks multi-year holiday assignments

**4. Desirable vs. Less Desirable Rotations:**
- Popular electives distributed fairly
- Less desirable rotations (night float, heavy call) balanced across residents
- Preferences considered but equity prioritized

### Preference Accommodation

The system collects and considers resident preferences:
- **Elective preferences:** Residents rank desired electives
- **Vacation preferences:** Preferred vacation blocks submitted in advance
- **Educational goals:** Rotations aligned with career interests when possible

However, preferences are balanced against:
- Coverage requirements
- Educational curriculum requirements
- ACGME compliance
- Equitable distribution principles

## Special Considerations

### Parental Leave

- Up to 6 weeks of parental leave available per ACGME guidelines
- Does not count against vacation time
- Coverage planned well in advance
- Rotations adjusted to ensure graduation requirements met

### Military Deployments and TDY

For military medical residency programs:
- TDY (Temporary Duty) assignments tracked separately
- Deployment coverage planned with backup residents
- System alerts when military obligations impact schedule
- Alternative coverage arranged in advance

### Research Time

- Protected research time scheduled as rotation blocks
- Typically for residents in research tracks
- Does not count toward clinical duty hours
- Scheduled to minimize disruption to clinical coverage

### Away Rotations

- External rotations at other institutions
- Require program director approval
- Coordinated with receiving program
- Count toward educational requirements but not local coverage

## Schedule Visibility and Access

### Web and Mobile Access

Residents and faculty can access schedules through:
- **Web interface:** Full schedule view with calendar interface
- **Mobile app:** On-the-go schedule checking and notifications
- **Calendar sync:** Export to personal calendars (Google, Outlook, Apple)
- **Real-time updates:** Schedule changes appear immediately

### Privacy and Security

- Role-based access control: Users see schedules relevant to their role
- Audit trails: All schedule changes logged with user and timestamp
- Data encryption: Protected health information (PHI) safeguarded
- Compliance: HIPAA-compliant data handling

## Contact for Schedule Issues

### Schedule Coordinators

**For Routine Questions:**
- Program Coordinator: Primary contact for schedule questions
- Email: [program-coordinator]@[institution]
- Office hours: Monday-Friday, 8:00 AM - 5:00 PM
- Response time: Within 1 business day

**For Urgent Issues:**
- Chief Resident: After-hours and urgent coverage issues
- Contact: [chief-resident-phone]
- Available: 24/7 for urgent matters
- Response time: Within 2 hours

**For System Technical Issues:**
- IT Support: System access, login problems, technical errors
- Email: [it-support]@[institution]
- Help desk: [phone number]
- Available: Monday-Friday, 7:00 AM - 7:00 PM

### Escalation Path

1. **First contact:** Program Coordinator (routine) or Chief Resident (urgent)
2. **Escalation:** Program Director (unresolved issues, policy questions)
3. **Final escalation:** Department Chair (appeals, policy exceptions)

## Continuous Improvement

The scheduling system is continuously improved based on:
- Resident feedback surveys (annual and post-rotation)
- Program director review of schedule efficiency
- Analysis of ACGME compliance trends
- Technology updates and feature enhancements

Residents are encouraged to provide feedback on scheduling policies and suggest improvements through the annual program evaluation process.
