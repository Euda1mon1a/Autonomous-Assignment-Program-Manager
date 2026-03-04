# Onboarding & Offboarding Playbook

**Purpose:** Comprehensive guide for onboarding new residents and faculty, provisioning access, training, and offboarding procedures.

**Target Audience:** Program Coordinators, HR Administrators, IT Support, Department Leadership

**Last Updated:** 2025-12-31

---

## Table of Contents

1. [Overview](#overview)
2. [New Resident Onboarding](#new-resident-onboarding)
3. [New Faculty Onboarding](#new-faculty-onboarding)
4. [System Access Provisioning](#system-access-provisioning)
5. [Training Checklist](#training-checklist)
6. [Offboarding Procedures](#offboarding-procedures)
7. [Quick Reference](#quick-reference)

---

## Overview

### Onboarding Timeline

```
RESIDENT ONBOARDING TIMELINE

3 MONTHS BEFORE START DATE:
- Accept interview completion
- Initiate credentialing
- Order workspace setup
- Plan orientation schedule

1 MONTH BEFORE:
- Finalize credentialing
- Complete background check
- Set up IT accounts
- Prepare welcome packet

2 WEEKS BEFORE:
- Complete system setup
- Assign mentor
- Schedule orientation
- Prepare rotation schedule

1 WEEK BEFORE:
- Final verification
- Welcome communication
- Parking/facilities setup
- Emergency contact update

DAY 1:
- Welcome and check-in
- Facilities tour
- ID badge pickup
- Account activation
- First rotation assignment

WEEK 1-2:
- System training
- Compliance training
- Clinical orientation
- Team introductions

MONTH 1:
- Initial performance check-in
- Address any issues
- Confirm comfort level
- Ongoing support

---

FACULTY ONBOARDING TIMELINE

4 WEEKS BEFORE START:
- Finalize credentials
- Complete credentialing
- Initiate privileging
- Order workspace

2 WEEKS BEFORE:
- Set up IT accounts
- Assign supervisor
- Schedule orientation
- Prepare materials

1 WEEK BEFORE:
- Account activation
- Welcome communication
- Facility setup
- Emergency contact update

DAY 1:
- Welcome meeting
- Facilities tour
- System access verification
- Administrative briefing
- Role expectations review

WEEK 1:
- System training (scheduling, swaps)
- Compliance training
- Supervision responsibilities review
- Team introduction

MONTH 1:
- Follow-up check-in
- Address questions
- Evaluate readiness
- Ongoing support
```

---

## New Resident Onboarding

### Pre-Arrival (4-12 Weeks Before)

#### Step 1: Credentialing Initiation

```bash
# POST: Create resident credentialing record
curl -X POST http://localhost:8000/api/admin/persons/resident \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Smith",
    "email": "john.smith@hospital.edu",
    "phone": "+1-808-555-0123",
    "start_date": "2026-07-01",
    "pgy_level": 1,
    "specialty": "Internal Medicine",
    "status": "pre_arrival"
  }'

# Response includes: resident_id (e.g., PGY1-001)
```

**Credentialing Checklist:**

```
RESIDENT CREDENTIALING CHECKLIST

Resident: _________________
Start Date: _________________
PGY Level: _________________

EDUCATION:
☐ Medical school diploma received
☐ License verification (state medical board)
☐ USMLE/COMLEX transcripts obtained
☐ Medical school transcripts on file

BACKGROUND:
☐ Background check ordered
☐ Background check cleared
☐ Drug screening ordered
☐ Drug screening clear
☐ Immunization records received

HOSPITAL CREDENTIALING:
☐ Hospital credentialing application complete
☐ References submitted
☐ Malpractice history verified
☐ Privileging initiated
☐ Privileging approved
☐ DEA registration (if applicable)

TRAINING:
☐ BLS certification (current)
☐ ACLS certification (current)
☐ PALS certification (for pediatrics, if applicable)
☐ Online compliance training assigned
☐ HIPAA training assigned

DOCUMENTATION:
☐ Complete form I-9
☐ W-4 tax form
☐ Emergency contacts on file
☐ Direct deposit information
☐ Health insurance elections

Status: ☐ COMPLETE ☐ PENDING ITEMS

Items pending: [List]
Expected completion: [Dates]

Verified By: _________________________ Date: __________
```

#### Step 2: IT Account Setup

```bash
# Create IT accounts 2 weeks before arrival

# 1. Create email account
# Contact: IT Department
# Account: [firstname.lastname@hospital.edu]
# Forward to personal email until start date

# 2. Create system login credentials
# Username: [pgy1_001]
# Initial password: [Generated secure password]
# Sent via secure channel to personal email

# 3. Set up phone extension
# Request from: Facilities/Communications
# Extension: [Assigned]
# Shared voicemail setup

# 4. Order badge/access card
# Request from: Security
# Include photo ID
# Set access groups:
#   - Clinical areas
#   - Resident lounge
#   - Call rooms
#   - Computer labs
```

**IT Setup Checklist:**

```
RESIDENT IT SETUP CHECKLIST

Resident: _________________
Start Date: _________________

EMAIL ACCOUNT:
☐ Email account created
☐ Initial password set
☐ Forwarding configured
☐ Signature template installed
☐ Security training sent

VPN/REMOTE ACCESS:
☐ VPN account created
☐ VPN client installed
☐ Two-factor authentication configured
☐ Remote desktop access enabled

SYSTEM ACCOUNTS:
☐ Hospital system account created
☐ EMR access granted
☐ Scheduling system access granted
☐ Portal access granted
☐ Training documentation access granted

SECURITY:
☐ Security policy review sent
☐ Password requirements explained
☐ Multi-factor authentication setup
☐ Data security training scheduled
☐ HIPAA training assigned

HARDWARE:
☐ Computer/laptop allocated
☐ Phone assigned
☐ Badge/access card ordered
☐ Parking permit issued
☐ Supplies ordered (desk, chair, etc.)

CONTACT INFORMATION:
☐ Personal email: [________]
☐ Personal phone: [________]
☐ Emergency contact name: [________]
☐ Emergency contact phone: [________]
☐ Address: [________]

Status: ☐ COMPLETE ☐ IN PROGRESS

Completed By: _________________________ Date: __________
```

### Arrival Week (Day 1-5)

#### Step 1: Welcome and Check-In

```bash
# On Day 1, complete welcome activities

cat > day_1_schedule.txt << 'EOF'
RESIDENT DAY 1 SCHEDULE

Arrival Time: 7:00 AM

7:00-7:15 AM: Meet Program Coordinator
- Welcome package handoff
- Schedule review
- Question answering

7:15-7:30 AM: Facilities Tour
- Office/workspace
- Call rooms
- Parking
- Cafeteria
- Bathrooms

7:30-8:00 AM: Badge & Access Setup
- Pick up badge
- Test access at key locations
- Phone activation
- Parking permit verification

8:00-9:00 AM: IT Systems Training
- Email setup
- Portal login
- Scheduling system demo
- Document access
- Printer/copier setup

9:00-10:00 AM: Administrative Briefing
- Program expectations
- Duty hour policies
- Compliance requirements
- Contact procedures
- Emergency protocols

10:00-11:00 AM: Meet Supervising Faculty
- Introduction
- Role expectations
- Communication channels
- On-call procedures
- Question time

11:00-12:00 PM: Peer Mentor Introduction
- Welcome from peer
- Informal guidance
- Social activities overview
- Questions welcome

12:00-1:00 PM: Lunch with Team
- Meet other residents and faculty
- Informal discussion
- Building relationships

1:00-2:00 PM: Clinical Orientation
- Venue tour (wards, clinics, procedures area)
- Key staff introductions
- Equipment familiarization
- Workflow overview

2:00-3:00 PM: Schedule Review
- First month assignments
- Rotation expectations
- Coverage assignments
- Questions addressed

3:00-4:00 PM: Compliance Training
- HIPAA training (completion)
- Workplace safety
- Harassment/discrimination policy
- Incident reporting
- Q&A

4:00-5:00 PM: Free Time
- Settle in
- Final questions
- Tomorrow preparation

MATERIALS PROVIDED:
- Welcome packet with key contacts
- Parking permit
- ID badge
- System login credentials
- Program schedule
- Duty hour policy
- Compliance documentation
EOF

# Execute Day 1 activities according to schedule
```

#### Step 2: Account Activation

```bash
# Activate all accounts for new resident

# POST: Activate system access
curl -X POST http://localhost:8000/api/admin/persons/PGY1-001/activate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "activation_date": "2026-07-01",
    "initial_assignments": true,
    "send_welcome_email": true,
    "assign_mentor": "PGY2-003"
  }'

# Activate portal access
curl -X POST http://localhost:8000/api/admin/portal/activate-user \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "PGY1-001",
    "role": "resident",
    "permissions": [
      "view_own_schedule",
      "request_swaps",
      "view_announcements",
      "access_resources"
    ]
  }'
```

**Day 1 Verification Checklist:**

```
RESIDENT DAY 1 COMPLETION CHECKLIST

Resident: _________________
Date: _________________

WELCOME ACTIVITIES:
☐ Program coordinator introduction
☐ Facilities tour completed
☐ Welcome packet distributed
☐ ID badge received and activated
☐ Parking permit issued
☐ Office/workspace assigned

SYSTEM ACCESS:
☐ Email account accessible
☐ Portal login works
☐ Scheduling system accessible
☐ Hospital system accessible
☐ VPN working (if needed)
☐ Phone activated

INFORMATION PROVIDED:
☐ Program orientation materials
☐ Duty hour policy reviewed
☐ Compliance requirements explained
☐ Emergency procedures reviewed
☐ Schedule reviewed and confirmed
☐ First assignment confirmed

PEOPLE INTRODUCTIONS:
☐ Program director met
☐ Faculty supervisor met
☐ Peer mentor assigned
☐ Team members introduced
☐ Administrative staff met
☐ Clinical staff introduced

ADMINISTRATIVE:
☐ Emergency contacts updated
☐ Insurance information collected
☐ Tax/payroll forms processed
☐ HIPAA training acknowledged
☐ System orientation completed
☐ Questions answered

RESIDENT FEEDBACK:
Comfort level: [1-10]
Questions remaining: [List]
Concerns: [List]
Next day preparation: [Noted]

Status: ☐ COMPLETE ☐ ISSUES

Issues to address:
[List any gaps]

Coordinator Signature: _________________________ Date: __________
Resident Acknowledgment: _________________________ Date: __________
```

### First Month (Week 1-4)

#### Step 1: System Training

```bash
# Comprehensive system training during first week

cat > system_training_plan.txt << 'EOF'
RESIDENT SYSTEM TRAINING PLAN

Week 1: Fundamental Training

Day 1: Scheduling System Overview
- Access and navigation
- View personal schedule
- Understand block structure
- Identify rotation assignments
- Locate support resources

Day 2: Portal Features
- Dashboard overview
- Document access
- Announcements
- Contact directory
- Personal profile management

Day 3: Schedule Features
- View detailed schedule
- Understand rotation types
- Holiday/leave dates
- Call schedule
- Coverage information

Day 4: Swap System Introduction
- How to request swaps
- Swap rules and restrictions
- Approval process
- Submit first swap request (practice)
- Understand swap policies

Day 5: Reporting and Resources
- Access educational resources
- View program announcements
- Access procedure manuals
- Find reference materials
- Contact procedures

Week 2: Advanced Features

Day 1: Work Hour Tracking
- How hours are calculated
- View personal work hours
- Understand 80-hour rule
- Report duty hour concerns
- When to escalate

Day 2: Leave and Time Off
- Request leave/vacation
- Understand approval process
- Emergency leave procedures
- How leave affects schedule
- Timeline for requests

Day 3: Performance and Feedback
- Access performance reviews (when available)
- Understand evaluation process
- Provide feedback channel
- Goal setting
- Development planning

Day 4: Support and Help
- Where to find help
- Contacting coordinator
- Escalation procedures
- Off-hours support
- Emergency protocols

Day 5: Policies and Compliance
- Review key policies
- ACGME requirements
- Supervision expectations
- On-call procedures
- Safety protocols

DELIVERABLES:
- Resident completes all trainings
- Resident can navigate system independently
- Resident knows how to request help
- Resident understands policies
- Resident demonstrates competency
EOF

# Track training completion
curl -X POST http://localhost:8000/api/admin/training/track \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resident_id": "PGY1-001",
    "training_module": "scheduling_system",
    "completion_date": "2026-07-03",
    "status": "complete"
  }'
```

#### Step 2: Compliance Training

```bash
# Mandatory compliance training (MUST complete before starting)

cat > compliance_training_required.txt << 'EOF'
MANDATORY COMPLIANCE TRAINING

All residents must complete BEFORE first clinical day:

1. HIPAA Training (45 minutes)
   - Patient privacy rules
   - Data protection
   - Confidentiality requirements
   - Violation reporting
   - Assessment: Online quiz (80% pass required)

2. Blood-borne Pathogens (30 minutes)
   - Exposure risks
   - Prevention measures
   - Exposure protocols
   - Post-exposure procedures
   - Assessment: Certificate upon completion

3. Workplace Safety (30 minutes)
   - Fire safety
   - Emergency evacuation
   - Equipment safety
   - Chemical safety
   - Assessment: Quiz

4. Anti-Harassment/Discrimination (20 minutes)
   - Definitions and examples
   - Reporting procedures
   - Prohibited conduct
   - Resources available
   - Assessment: Acknowledgment form

5. Security Awareness (15 minutes)
   - Password management
   - Phishing awareness
   - Data protection
   - Reporting breaches
   - Assessment: Quiz

6. Substance Abuse Policy (15 minutes)
   - Program policies
   - Screening procedures
   - Reporting requirements
   - Treatment resources
   - Assessment: Acknowledgment

7. ACGME Requirements (30 minutes)
   - Work hour rules
   - Rest requirements
   - Supervision standards
   - Duty hour violations reporting
   - Assessment: Quiz

Total Training Time: ~3 hours
Deadline: Before first clinical assignment
Tracking: LMS system automatically records completion
EOF

# Assign training to resident
curl -X POST http://localhost:8000/api/admin/compliance/assign-training \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resident_id": "PGY1-001",
    "training_set": "new_resident_mandatory",
    "due_date": "2026-07-01",
    "send_reminder": true
  }'
```

**Month 1 Progress Checklist:**

```
RESIDENT FIRST MONTH PROGRESS CHECKLIST

Resident: _________________
Start Date: _________________
Check-in Date: _________________

FIRST WEEK:
☐ Completed Day 1 orientation
☐ Settled into workspace
☐ Met all key personnel
☐ Completed system training
☐ Commenced first clinical rotation

SECOND WEEK:
☐ Comfortable with schedule system
☐ Comfortable with rotation expectations
☐ Met faculty mentor regularly
☐ Peer mentor relationship established
☐ No significant issues

THIRD WEEK:
☐ Clinical performance progressing
☐ Asking appropriate questions
☐ Requesting feedback actively
☐ Understands duty hour policies
☐ No compliance concerns

FOURTH WEEK:
☐ Settling into routine
☐ Demonstrating competency
☐ Building team relationships
☐ Comfortable asking for help
☐ Ready for ongoing development

TRAINING COMPLETED:
☐ System training complete
☐ Compliance training complete
☐ Clinical orientation complete
☐ Rotation-specific training complete

SUPPORT PROVIDED:
☐ Peer mentor assigned and active
☐ Faculty supervision adequate
☐ Coordinator available and responsive
☐ Questions addressed promptly
☐ No unresolved concerns

RESIDENT COMFORT LEVEL:
Rate 1-10: [_]

Overall Comments:
[Notes on progress, concerns, strengths]

Next Steps:
- Continue routine support
- Schedule monthly check-in for month 2
- Continue monitoring adjustment
- Address any emerging issues

Coordinator Signature: _________________________ Date: __________
```

---

## New Faculty Onboarding

### Pre-Arrival (4 Weeks Before)

#### Step 1: Credentialing

```bash
# POST: Create faculty credentialing record
curl -X POST http://localhost:8000/api/admin/persons/faculty \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane.doe@hospital.edu",
    "phone": "+1-808-555-0456",
    "start_date": "2026-07-01",
    "title": "Associate Professor",
    "specialty": "Internal Medicine",
    "prior_supervision_experience": true,
    "status": "pre_arrival"
  }'
```

**Faculty Credentialing Checklist:**

```
FACULTY CREDENTIALING CHECKLIST

Faculty: _________________
Start Date: _________________
Title: _________________
Specialty: _________________

PROFESSIONAL CREDENTIALS:
☐ Medical degree verified
☐ State medical license current
☐ Board certification current
☐ Specialty license (if applicable)
☐ Proof of insurance (malpractice)

HOSPITAL CREDENTIALING:
☐ Credentialing application complete
☐ References submitted
☐ Curriculum vitae on file
☐ Malpractice history disclosed
☐ Privileging initiated
☐ Privileging approved
☐ DEA registration (if applicable)
☐ Medicare/Medicaid enrollment

TRAINING & CERTIFICATIONS:
☐ BLS certification (current)
☐ ACLS certification (if needed)
☐ Teaching certificate or course (if available)
☐ Supervision training (program-specific)
☐ HIPAA training assigned
☐ Compliance training assigned

TEACHING QUALIFICATIONS:
☐ Prior teaching experience documented
☐ Teaching philosophy reviewed
☐ Course load capacity confirmed
☐ Committee assignments identified
☐ Mentoring approach discussed

Status: ☐ COMPLETE ☐ PENDING

Pending items: [List]
Expected completion: [Dates]

Verified By: _________________________ Date: __________
```

#### Step 2: IT & Workspace Setup

```bash
# Same IT account creation as residents, plus:

# 1. Faculty-specific email
# Account: [fname.lname@hospital.edu]
# Shared resource calendar access

# 2. System administrative access
# Scheduling system admin access (if needed)
# Report generation access
# Staff management access

# 3. Workspace preparation
# Office assignment
# Parking space
# Phone extension
# Computer/laptop
```

### Arrival Week

#### Step 1: Welcome and Orientation

```bash
cat > faculty_day_1_schedule.txt << 'EOF'
FACULTY DAY 1 SCHEDULE

Arrival Time: 8:00 AM

8:00-8:30 AM: Program Director Welcome
- Introduction and program overview
- Expectations and priorities
- Teaching philosophy discussion
- Questions answered

8:30-9:00 AM: Administrative Briefing
- Benefits overview
- Payroll and HR procedures
- Parking and facilities
- Key contacts
- Emergency procedures

9:00-10:00 AM: IT & Systems Setup
- Email and communications
- Scheduling system access
- Administrative system access
- Report generation
- Data access permissions

10:00-11:00 AM: Curriculum Overview
- Program goals and competencies
- Rotation descriptions
- Teaching responsibilities
- Assessment procedures
- Educational resources

11:00-12:00 PM: Supervision Training
- ACGME supervision requirements
- Faculty supervision ratios
- Duty hour monitoring
- When to intervene
- Documentation requirements

12:00-1:00 PM: Lunch with Faculty
- Meet other faculty
- Informal discussion
- Program culture
- Networking

1:00-2:00 PM: Resident Introductions
- Meet residents in program
- Understand resident cohort
- Teaching assignments
- Mentoring opportunities

2:00-3:00 PM: Clinical Setting Tour
- Clinical venues
- Procedure areas
- Teaching spaces
- Key staff introductions
- Workflow overview

3:00-4:00 PM: Policies & Compliance
- Program policies
- HIPAA training
- Workplace safety
- Harassment policies
- Incident reporting

4:00-5:00 PM: Office Setup & Free Time
- Workspace orientation
- Technology setup
- Phone configuration
- Schedule confirmation

MATERIALS PROVIDED:
- Faculty handbook
- Program curriculum
- Resident roster with photos
- Supervision guidelines
- Contact directory
- Policy documentation
EOF
```

#### Step 2: Account Activation

```bash
# POST: Activate faculty access
curl -X POST http://localhost:8000/api/admin/persons/FAC-001/activate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "activation_date": "2026-07-01",
    "role": "faculty",
    "permissions": [
      "view_all_schedules",
      "approve_swaps",
      "manage_assignments",
      "view_reports",
      "access_admin_features"
    ],
    "assign_supervising_faculty": "FAC-002",
    "send_welcome_email": true
  }'
```

### First Month Training

#### Step 1: Supervision Training

```bash
# Critical training for faculty supervising residents

cat > supervision_training.txt << 'EOF'
FACULTY SUPERVISION TRAINING

ACGME Requirements:
- Faculty must understand duty hour rules
- Faculty responsible for monitoring resident work hours
- Faculty must prevent violations
- Faculty must escalate concerns appropriately

Key Topics:

1. Duty Hour Rules (30 min)
   - 80-hour weekly limit
   - 1-in-7 rest requirement
   - Maximum daily/on-call hours
   - Averaging rules
   - Exception procedures

2. Supervision Ratios (20 min)
   - PGY1: 1 faculty to 2 residents
   - PGY2+: 1 faculty to 4 residents
   - Educational value requirements
   - Graduated responsibility
   - Direct vs. indirect supervision

3. Monitoring Work Hours (30 min)
   - System tools for tracking
   - Weekly review procedures
   - Trend analysis
   - Red flags to watch for
   - Intervention procedures

4. Problem Resolution (30 min)
   - When to step in
   - How to address violations
   - Documentation requirements
   - Escalation procedures
   - Supporting resident well-being

5. Fatigue Mitigation (20 min)
   - Signs of fatigue
   - Impact on learning
   - Impact on safety
   - Mitigation strategies
   - Resource availability

Total Time: ~2 hours
Completion: Required within first month
Assessment: Certification of completion
Ongoing: Annual refresher required
EOF

# Assign supervision training
curl -X POST http://localhost:8000/api/admin/training/assign \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "faculty_id": "FAC-001",
    "training_module": "faculty_supervision",
    "due_date": "2026-08-01",
    "send_reminder": true
  }'
```

#### Step 2: System Training

```bash
# Faculty-specific system training

cat > faculty_system_training.txt << 'EOF'
FACULTY SYSTEM TRAINING

Week 1: Schedule Management

Session 1: Scheduling System Overview
- Dashboard and reports
- View resident schedules
- View block assignments
- Coverage analysis
- Performance metrics

Session 2: Swap Approval
- Swap request process
- Approval workflows
- Compliance checking
- Deny procedures
- Documentation

Session 3: Administrative Functions
- Resident management
- Data entry
- Error correction
- Report generation
- Communication tools

Week 2: Supervision and Monitoring

Session 1: Work Hour Tracking
- Dashboard access
- Weekly review procedures
- Trend analysis
- Red flags
- Escalation procedures

Session 2: Compliance Verification
- ACGME rule checking
- Violation identification
- Root cause analysis
- Remediation procedures
- Documentation

Session 3: Resident Support
- Performance review process
- Feedback provision
- Coaching procedures
- Addressing concerns
- Escalation paths

DELIVERABLES:
- Faculty can navigate system independently
- Faculty understands supervision responsibilities
- Faculty knows how to monitor resident hours
- Faculty knows escalation procedures
- Faculty certified in system competency

Training Record: Maintained in system
Completion Certificate: Issued upon completion
EOF
```

**Month 1 Faculty Checklist:**

```
FACULTY FIRST MONTH CHECKLIST

Faculty: _________________
Start Date: _________________

ORIENTATION COMPLETE:
☐ Program orientation completed
☐ Supervision training completed
☐ System training completed
☐ All policies reviewed
☐ Compliance training completed

RELATIONSHIPS ESTABLISHED:
☐ Met program director regularly
☐ Connected with other faculty
☐ Introduced to residents
☐ Established communication channels
☐ Know key administrative staff

RESPONSIBILITIES UNDERSTOOD:
☐ Teaching assignments confirmed
☐ Supervision assignments confirmed
☐ Committee assignments (if any) confirmed
☐ On-call schedule (if applicable) established
☐ Office hours/availability established

SYSTEM COMPETENCY:
☐ Can view resident schedules
☐ Can process swap approvals
☐ Can monitor work hours
☐ Can generate reports
☐ Can access administrative functions

SUPPORT PROVIDED:
☐ Mentor faculty assigned
☐ Questions answered promptly
☐ Administrative support responsive
☐ Technical support available
☐ Teaching resources provided

RESIDENT FEEDBACK:
Resident satisfaction: [Initial assessment]
Teaching quality: [Initial assessment]
Supervision appropriateness: [Initial assessment]

Next Steps:
- Continue regular check-ins with PD
- Attend faculty development sessions
- Establish regular supervision schedule
- Plan first formal resident evaluation

Signature: _________________________ Date: __________
```

---

## System Access Provisioning

### Access Control Matrix

```
USER ROLE ACCESS MATRIX

RESIDENT:
- View own schedule: YES
- View other resident schedules: NO
- View faculty schedules: NO
- Request swaps: YES
- Approve swaps: NO
- View compliance reports: Limited (own data only)
- Export data: NO
- Modify schedule: NO
- Generate reports: NO

FACULTY:
- View own schedule: YES
- View assigned resident schedules: YES
- View all resident schedules: Limited
- Request swaps: YES
- Approve swaps: YES (for assigned residents)
- View compliance reports: YES (assigned residents)
- Export data: YES (limited)
- Modify schedule: Limited (swap approvals)
- Generate reports: YES (basic)

COORDINATOR:
- View all schedules: YES
- View all persons: YES
- Request swaps: YES
- Approve swaps: YES
- Process schedule changes: YES
- View all reports: YES
- Export data: YES
- Modify schedule: YES (with approval)
- Generate reports: YES

PROGRAM DIRECTOR:
- View all schedules: YES
- View all persons: YES
- Approve major changes: YES
- View compliance reports: YES
- Export data: YES
- Modify schedule: YES
- Generate reports: YES
- Admin functions: YES
- User management: YES

IT ADMIN:
- System access: YES
- User management: YES
- Backup/restore: YES
- Log access: YES
- Database access: YES
- System configuration: YES
- Security functions: YES
- Audit trails: YES
```

### Access Provisioning Process

```bash
# 1. Create user account
curl -X POST http://localhost:8000/api/admin/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "pgy1_001",
    "email": "john.smith@hospital.edu",
    "role": "resident",
    "person_id": "PGY1-001",
    "force_password_change": true,
    "send_welcome_email": true
  }'

# 2. Assign role-specific permissions
curl -X POST http://localhost:8000/api/admin/users/pgy1_001/permissions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "permissions": [
      "schedule:view:own",
      "swaps:request",
      "reports:view:limited",
      "portal:access"
    ]
  }'

# 3. Verify access works
# Send test login link to user
# User logs in and confirms access
```

**Access Provisioning Checklist:**

```
SYSTEM ACCESS PROVISIONING CHECKLIST

New Person: _________________
Start Date: _________________
Role: [Resident/Faculty/Coordinator]

ACCOUNT CREATION:
☐ Username created
☐ Email account set up
☐ Initial password generated
☐ Welcome email sent
☐ Login verified

ROLE ASSIGNMENT:
☐ Primary role assigned
☐ Secondary roles assigned (if any)
☐ Permissions granted
☐ Restrictions applied (if any)
☐ Access level documented

SYSTEM ACCESS:
☐ Portal login works
☐ Scheduling system accessible
☐ Can view assigned schedules
☐ Can access resources
☐ Can use appropriate functions

SECURITY:
☐ Multi-factor authentication set up (if required)
☐ VPN access configured (if needed)
☐ Security policies acknowledged
☐ Password requirements explained
☐ Security training completed

VERIFICATION:
☐ Can login successfully
☐ Can navigate system
☐ Can access required data
☐ Appropriate restrictions in place
☐ No unauthorized access

DOCUMENTATION:
☐ Access logged in system
☐ Person record updated
☐ Supervisor notified
☐ IT records updated
☐ Archives maintained

Status: ☐ COMPLETE ☐ PENDING

Issues: [List any problems]

Verified By: _________________________ Date: __________
```

---

## Training Checklist

### Mandatory Training Completion

**All new persons must complete:**

```
MANDATORY TRAINING FOR ALL NEW PERSONS

1. HIPAA Training (Online)
   Duration: 45 minutes
   Assessment: Quiz (80% required)
   Deadline: Before first work day
   ☐ Completed

2. Security Awareness (Online)
   Duration: 30 minutes
   Assessment: Quiz
   Deadline: Day 1
   ☐ Completed

3. Anti-Harassment/Discrimination (Online)
   Duration: 20 minutes
   Assessment: Acknowledgment
   Deadline: Day 1
   ☐ Completed

4. Workplace Safety (Online or In-person)
   Duration: 30 minutes
   Assessment: Quiz
   Deadline: Day 1
   ☐ Completed

5. System Training
   Duration: 2-3 hours
   Assessment: Practical demonstration
   Deadline: Week 1
   ☐ Completed

6. Program Orientation
   Duration: 4-6 hours
   Assessment: Q&A
   Deadline: Week 1
   ☐ Completed

7. Compliance Policy Review
   Duration: 2 hours
   Assessment: Acknowledgment
   Deadline: Week 1
   ☐ Completed

TRACKING:
- Residents: Learning Management System tracks
- Faculty: Learning Management System tracks
- Coordinators: HR tracks

CERTIFICATION:
- All required trainings must be completed
- Certificate issued upon completion
- Record maintained in personnel file
- Annual refresher required (some trainings)
```

---

## Offboarding Procedures

### Notification and Planning (2 Weeks Before Departure)

```bash
# Initiate offboarding process

# POST: Create offboarding record
curl -X POST http://localhost:8000/api/admin/offboarding \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "PGY1-001",
    "last_day": "2027-06-30",
    "reason": "graduation",
    "next_assignment": "Fellowship program XYZ"
  }'

cat > offboarding_checklist.txt << 'EOF'
OFFBOARDING CHECKLIST

Person: _________________
Last Day: _________________
Reason: [Graduation/Resignation/Transfer]

2 WEEKS BEFORE DEPARTURE:

Administrative:
☐ Notify HR of departure
☐ Document final employment status
☐ Process final paycheck setup
☐ Benefits information provided
☐ COBRA information provided

Clinical:
☐ Complete all required signouts
☐ Ensure patient care continuity
☐ Transfer patient panels (if applicable)
☐ Complete all documentation
☐ Submit final evaluations

Schedule & Assignments:
☐ Notify scheduler of departure
☐ Remove from future rotation assignments
☐ Identify coverage for remaining assignments
☐ Update call schedule
☐ Update on-call assignments

1 WEEK BEFORE:

Systems & Access:
☐ Plan system access removal
☐ Identify data access to revoke
☐ IT notified of departure
☐ Email forwarding configured
☐ Document retention planned

Financial:
☐ Parking permit returned
☐ Badge/access card collected plan
☐ Equipment return plan
☐ Final expense reimbursements processed
☐ Tax documents prepared

Transition:
☐ Knowledge transfer plan created
☐ Successor identified (if applicable)
☐ Documentation prepared
☐ Procedures documented
☐ Contact information updated

FINAL DAY:

Morning:
☐ Final sign-out from clinical areas
☐ Complete all work
☐ Patient handoffs documented
☐ Office cleaned out
☐ Personal items packed

Final Hour:
☐ IT systems disabled
☐ Badge/access card collected
☐ Equipment returned
☐ Final check-out with coordinator
☐ Parking permit returned

Administrative Completion:
☐ Personnel file closed
☐ Final paycheck issued
☐ Benefits termination processed
☐ Forwarding address updated
☐ References provided (if appropriate)

AFTER DEPARTURE:

Within 1 Week:
☐ System accounts disabled
☐ Email account deactivated
☐ Access revoked completely
☐ VPN access removed
☐ Portal access disabled

Within 1 Month:
☐ Final evaluation completed
☐ References letter (if requested) provided
☐ Alumni record created
☐ Records archived
☐ Exit survey sent

STATUS: ☐ COMPLETE

Completed By: _________________________ Date: __________
EOF
```

### System Access Removal

```bash
# Remove all system access on final day

# 1. Disable all accounts
curl -X POST http://localhost:8000/api/admin/users/PGY1-001/disable \
  -H "Authorization: Bearer $TOKEN"

# 2. Revoke all permissions
curl -X POST http://localhost:8000/api/admin/users/PGY1-001/revoke-permissions \
  -H "Authorization: Bearer $TOKEN"

# 3. Expire/revoke credentials
# - Password reset
# - Session termination
# - Token revocation
# - API key removal

# 4. Update person status
curl -X PATCH http://localhost:8000/api/admin/persons/PGY1-001 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "departed",
    "departure_date": "2027-06-30"
  }'

# 5. Archive person record
curl -X POST http://localhost:8000/api/admin/persons/PGY1-001/archive \
  -H "Authorization: Bearer $TOKEN"
```

### Schedule Cleanup

```bash
# Remove departed person from future assignments

# POST: Remove from remaining rotations
curl -X POST http://localhost:8000/api/admin/schedule/remove-person \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "PGY1-001",
    "effective_date": "2027-06-30",
    "action": "remove_from_schedule",
    "reassign_to": "coverage_pool"
  }'

# Verify removal
curl -X GET http://localhost:8000/api/assignments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "PGY1-001",
    "after_date": "2027-06-30"
  }'

# Should return: No assignments found
```

**Final Status Verification:**

```
OFFBOARDING VERIFICATION CHECKLIST

Person: _________________
Departure Date: _________________

SYSTEM ACCESS REMOVED:
☐ Portal account disabled
☐ Email access removed
☐ System access revoked
☐ VPN access disabled
☐ API keys revoked
☐ Session tokens expired
☐ Device access revoked

SCHEDULE CLEAN:
☐ All future assignments removed
☐ Coverage reassigned
☐ Call schedule updated
☐ Rotations vacated
☐ No residual assignments

DATA HANDLED:
☐ Personal data secured
☐ Work product archived
☐ Patient data transferred
☐ Documentation complete
☐ Records retained per policy

FINAL ITEMS:
☐ Equipment returned
☐ Badge collected
☐ Keys collected
☐ Documents provided
☐ Exit performed

STATUS: ☐ OFFBOARDING COMPLETE

If issues: [Describe]
Resolution: [How handled]

Completed By: _________________________ Date: __________
```

---

## Quick Reference

### Key Contacts

```
ONBOARDING/OFFBOARDING CONTACTS

Program Director: [Name] [Phone] [Email]
Program Coordinator: [Name] [Phone] [Email]
HR Manager: [Name] [Phone] [Email]
IT Help Desk: [Phone] [Email]
Facilities: [Phone] [Email]
Security/Badges: [Phone] [Email]
Payroll: [Phone] [Email]
Benefits: [Phone] [Email]
```

### Key Forms

```
IMPORTANT FORMS & DOCUMENTS

Before Arrival:
- Credentialing application
- Background check forms
- IT account request
- Parking permit request
- Badge/access application

Day 1 (Have Available):
- Welcome packet
- Parking permit
- Badge/access card
- IT credentials
- Schedule confirmation

Ongoing:
- Training completion records
- Performance evaluations
- Leave requests
- Swap requests
- Schedule changes

At Departure:
- Final paycheck information
- COBRA documentation
- Reference letters
- Alumni record
- Exit survey
```

### Key Dates

```
KEY ONBOARDING DATES

Resident Cycle:
- June 1: Final applicants identified
- June 15: Credentialing begins
- July 1: Start date (first day)
- July 31: First month evaluation

Faculty Hiring:
- January: Recruitment begins
- March: Interviews
- April: Offers
- June 1: Expected start (varies)
```

---

**Document Version:** 1.0
**Last Updated:** 2025-12-31
**Owner:** Human Resources / Program Administration
**Review Cycle:** Annual or as needed
