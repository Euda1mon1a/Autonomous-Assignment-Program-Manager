# Google AI Studio Prompt: N-1/N-2 Contingency Visualization

Copy everything below the line into Google AI Studio with "Create a React app with Three.js" or similar.

---

## Context

I'm building a medical residency scheduling system for TAMC Family Medicine Residency Program. We need to visualize **N-1 and N-2 contingency analysis** - borrowed from power grid engineering where:

- **N-1**: System must survive the loss of any single component (any 1 faculty member absent)
- **N-2**: System must survive the loss of any two components (any 2 faculty members absent)

This is critical for workforce resilience planning. Program coordinators need to see "what breaks if Dr. X is out sick?"

## The Data

**10 Full-Time Faculty** (outer ring):
```javascript
const FACULTY = [
  { id: 'F1', name: 'Dr. Alpha', specialty: 'FM Clinic Lead', capacity: 5, critical: true },
  { id: 'F2', name: 'Dr. Beta', specialty: 'FM Clinic', capacity: 4, critical: false },
  { id: 'F3', name: 'Dr. Gamma', specialty: 'Inpatient Director', capacity: 4, critical: true },
  { id: 'F4', name: 'Dr. Delta', specialty: 'Inpatient', capacity: 4, critical: false },
  { id: 'F5', name: 'Dr. Epsilon', specialty: 'OB Lead', capacity: 3, critical: true },
  { id: 'F6', name: 'Dr. Zeta', specialty: 'OB', capacity: 3, critical: false },
  { id: 'F7', name: 'Dr. Eta', specialty: 'Pediatrics', capacity: 4, critical: false },
  { id: 'F8', name: 'Dr. Theta', specialty: 'Geriatrics', capacity: 4, critical: false },
  { id: 'F9', name: 'Dr. Iota', specialty: 'Sports Medicine', capacity: 3, critical: false },
  { id: 'F10', name: 'Dr. Kappa', specialty: 'Urgent Care Lead', capacity: 4, critical: true },
];
```

**24 Residents** (inner area) - each has:
- Primary supervisor (main faculty)
- Backup supervisor (coverage if primary absent)
- PGY level (1, 2, or 3)

Generate realistic supervision assignments where:
- Each faculty supervises 2-5 residents as primary
- Backup supervisors are different from primary
- Critical faculty (Lead roles) should supervise more residents

## Visualization Requirements

### Layout
- **3D scene** with Three.js
- Faculty as **large spheres** arranged in an outer circle (radius ~10)
- Residents as **smaller spheres** in inner area
- **Connection lines** from residents to their supervisors:
  - Blue solid line = primary supervisor (active)
  - Gray dashed line = backup supervisor (standby)
  - Yellow line = backup activated (when primary removed)
  - Red pulsing = no coverage (both supervisors removed)

### Interactivity
- **Click faculty** to toggle their removal (simulate absence)
- **N-1 Mode**: Only allow removing 1 faculty at a time
- **N-2 Mode**: Allow removing up to 2 faculty
- **Hover** on any node shows tooltip with details
- **OrbitControls** for camera rotation/zoom

### Metrics Panel (show real-time)
1. **Coverage Rate**: % of residents with at least one supervisor
2. **Supervision Gaps**: Count of residents with NO supervisor
3. **Overloaded Faculty**: Count of faculty exceeding capacity
4. **At-Risk Residents**: Count on backup-only supervision

### Status Banner
- 🟢 Green: "System Nominal - Full Redundancy"
- 🟡 Yellow: "WARNING - Degraded coverage, X on backup"
- 🔴 Red: "CRITICAL - X residents without supervision"

### Visual Feedback
- Removed faculty: gray, smaller, dimmed
- Active faculty: blue, glowing
- Covered residents: green
- Backup-only residents: yellow
- Uncovered residents: red, pulsing animation

## Tech Stack
- React 18 with TypeScript
- Three.js via @react-three/fiber and @react-three/drei
- Tailwind CSS for UI panels
- No external API calls - all data local

## Style
- Dark theme (bg: #0a0a0f)
- Glassmorphism panels with backdrop blur
- Color palette: Blue (#3b82f6), Green (#22c55e), Yellow (#eab308), Red (#ef4444)
- Clean, military-grade aesthetic

## Key Insight to Visualize

The most valuable insight is showing **cascade risk**:
- Some faculty are "critical nodes" - removing them causes more residents to lose coverage
- Some faculty pairs are "correlated risk" - if both are out, a whole rotation collapses
- The visualization should make it obvious which faculty are indispensable

## Output

A single-page React application that:
1. Renders the 3D network graph
2. Allows clicking faculty to simulate absences
3. Shows real-time impact on supervision coverage
4. Clearly distinguishes N-1 (any single loss) from N-2 (any pair loss)
5. Helps program coordinators answer: "Are we resilient enough?"
