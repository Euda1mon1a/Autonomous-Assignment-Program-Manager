# LaTeX Generation Research

> **Research Date:** 2026-01-28
> **Purpose:** Evaluate Python-to-LaTeX libraries for automated generation of MFRs and clinical reports in the Residency Scheduler

---

## Executive Summary

This research evaluates approaches for incorporating automated LaTeX generation into the Residency Scheduler to streamline production of Memoranda for Record (MFRs) and clinical compliance reports. The project already has robust PDF generation infrastructure using ReportLab; LaTeX would add high-quality typesetting for formal military documents.

### Key Findings

| Category | Recommended Approach | Integration Priority |
|----------|---------------------|---------------------|
| **Template-Based (MFRs)** | Jinja2 + LaTeX templates | ✅ High - Most efficient for standardized forms |
| **Programmatic (Dynamic)** | PyLaTeX | Medium - For complex, data-driven reports |
| **Data Sanitization** | pylatexenc | ✅ High - Critical for OPSEC compliance |
| **Compilation** | latexmk via Docker | Medium - Ensures consistent output |

### Current State

The repository already has:
- **ReportLab PDF generation** - Working, professional reports
- **Jinja2** - Already in requirements (v3.1.6)
- **Export factory pattern** - Extensible for new formats
- **Template manager** - Can be extended for LaTeX templates

**Not present:**
- No LaTeX dependencies
- No LaTeX templates
- No LaTeX compilation toolchain

---

## Part 1: Library Evaluation

### 1.1 PyLaTeX - Programmatic Document Creation

| Attribute | Details |
|-----------|---------|
| **Install** | `pip install pylatex` |
| **Version** | 1.4.2 (stable) |
| **License** | MIT |
| **Maintenance** | Active |

**Key Features:**
- Object-oriented interface for document construction
- Built-in support for tables, figures, sections
- NumPy integration for matrices
- Matplotlib integration for plots
- No raw LaTeX required for basic documents

**Code Example:**
```python
from pylatex import Document, Section, Subsection, Tabular, Command
from pylatex.utils import bold, NoEscape

def generate_compliance_report(data: dict) -> Document:
    doc = Document()
    doc.preamble.append(Command('title', 'ACGME Compliance Report'))
    doc.preamble.append(Command('date', NoEscape(r'\today')))
    doc.append(NoEscape(r'\maketitle'))

    with doc.create(Section('Work Hour Summary')):
        with doc.create(Tabular('|l|c|c|')) as table:
            table.add_hline()
            table.add_row(['Resident', 'Weekly Avg', 'Violations'])
            table.add_hline()
            for resident in data['residents']:
                table.add_row([
                    resident['name'],
                    f"{resident['avg_hours']:.1f}",
                    str(resident['violations'])
                ])
            table.add_hline()

    return doc
```

**Best For:**
- Complex, dynamic reports with data-driven content
- Reports requiring mathematical notation
- Reports with embedded charts/visualizations

**Limitations:**
- Requires LaTeX installation for PDF compilation
- Learning curve for custom document classes

### 1.2 Jinja2 + LaTeX Templates - Template-Based Generation

| Attribute | Details |
|-----------|---------|
| **Install** | Already in requirements |
| **Version** | 3.1.6 |
| **Integration** | Existing template infrastructure |

**Key Features:**
- Complete separation of content and layout
- Easy to maintain military-standard templates
- Non-programmers can update templates
- Faster for standardized forms (MFRs)

**Custom Delimiters for LaTeX:**
```python
import jinja2

latex_jinja_env = jinja2.Environment(
    block_start_string=r'\BLOCK{',
    block_end_string='}',
    variable_start_string=r'\VAR{',
    variable_end_string='}',
    comment_start_string=r'\#{',
    comment_end_string='}',
    line_statement_prefix='%%',
    line_comment_prefix='%#',
    trim_blocks=True,
    autoescape=False,
    loader=jinja2.FileSystemLoader('templates/latex/')
)
```

**MFR Template Example:**
```latex
\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{fancyhdr}

\begin{document}

\begin{center}
\textbf{DEPARTMENT OF THE ARMY} \\
\VAR{unit_name} \\
\VAR{unit_address}
\end{center}

\vspace{0.5in}

\noindent \VAR{office_symbol} \hfill \VAR{date}

\vspace{0.25in}

\noindent MEMORANDUM FOR RECORD

\vspace{0.25in}

\noindent SUBJECT: \VAR{subject}

\vspace{0.25in}

\BLOCK{ for paragraph in paragraphs }
\noindent \VAR{loop.index}. \VAR{paragraph}

\vspace{0.15in}
\BLOCK{ endfor }

\vspace{0.5in}

\noindent \VAR{signature_block}

\end{document}
```

**Best For:**
- Standardized military forms (MFRs, counseling statements)
- Documents with fixed structure but variable content
- Templates maintained by non-developers

### 1.3 pylatexenc - Data Sanitization

| Attribute | Details |
|-----------|---------|
| **Install** | `pip install pylatexenc` |
| **Version** | 2.10 (stable) |
| **Purpose** | Unicode → LaTeX escape conversion |

**Critical for OPSEC:** Handles special characters that could break LaTeX or expose data:

```python
from pylatexenc.latexencode import unicode_to_latex

def sanitize_for_latex(text: str) -> str:
    """
    Sanitize user input for safe LaTeX inclusion.

    Handles:
    - Special characters: & # % $ _ { } ~ ^
    - Unicode characters: accented letters, symbols
    - Potential injection vectors
    """
    return unicode_to_latex(
        text,
        unknown_char_policy='replace',
        unknown_char_warning=True
    )

# Example
raw_input = "Dr. O'Brien's 80% compliance & $5K budget"
safe_latex = sanitize_for_latex(raw_input)
# Result: "Dr. O'Brien's 80\\% compliance \\& \\$5K budget"
```

**Security Considerations:**
- Prevents LaTeX injection attacks
- Handles international characters in names
- Essential for any user-supplied content

### 1.4 Supporting Libraries

| Library | Purpose | Install |
|---------|---------|---------|
| **latexbuild** | Jinja2+LaTeX build system | `pip install latexbuild` |
| **LaGen** | Professional document generation | GitHub only |
| **templatex** | Jinja2 dialect for LaTeX | `pip install templatex` |
| **plasTeX** | LaTeX → XML/HTML conversion | `pip install plastex` |

---

## Part 2: Military MFR Format Requirements

### 2.1 Standard MFR Structure (AR 25-50 Compliant)

```
┌─────────────────────────────────────────────┐
│           DEPARTMENT OF THE ARMY            │
│              [Unit Name]                    │
│           [Unit Address]                    │
├─────────────────────────────────────────────┤
│ [Office Symbol]                    [Date]   │
│                                             │
│ MEMORANDUM FOR RECORD                       │
│                                             │
│ SUBJECT: [Brief Description]                │
│                                             │
│ 1. [Purpose paragraph]                      │
│                                             │
│ 2. [Background/Details]                     │
│                                             │
│ 3. [Findings/Actions]                       │
│                                             │
│ 4. [Recommendations/POC]                    │
│                                             │
│                                             │
│ [Signature Block]                           │
│ [Name/Rank/Title]                           │
│                                             │
│ Encl: [if any]                              │
└─────────────────────────────────────────────┘
```

### 2.2 MFR Types for Residency Scheduler

| MFR Type | Purpose | Trigger |
|----------|---------|---------|
| **Risk Acceptance** | Document approved violations | Defense level change |
| **Safety Concern** | Document patient safety issues | N-2 defense breach |
| **Compliance Report** | ACGME compliance summary | Monthly/Quarterly |
| **Swap Documentation** | Document shift swap decisions | Swap approval |
| **Coverage Exception** | Document emergency coverage | Unplanned absence |

### 2.3 Data Fields Required

```python
@dataclass
class MFRData:
    # Header
    unit_name: str
    unit_address: str
    office_symbol: str
    date: date

    # Content
    subject: str
    paragraphs: list[str]

    # Signature
    signer_name: str
    signer_rank: str
    signer_title: str

    # Optional
    enclosures: list[str] = field(default_factory=list)
    distribution: list[str] = field(default_factory=list)
    classification: str = "UNCLASSIFIED"
```

---

## Part 3: Integration Architecture

### 3.1 Proposed Directory Structure

```
backend/app/
├── services/
│   └── latex/
│       ├── __init__.py
│       ├── generator.py      # LaTeX document generator
│       ├── compiler.py       # PDF compilation service
│       └── sanitizer.py      # pylatexenc wrapper
├── templates/
│   └── latex/
│       ├── mfr_standard.tex      # Standard MFR template
│       ├── mfr_compliance.tex    # ACGME compliance MFR
│       ├── mfr_risk_accept.tex   # Risk acceptance MFR
│       └── report_acgme.tex      # Full ACGME report
```

### 3.2 Integration with Export Factory

```python
# backend/app/services/export/export_factory.py

class ExportFactory:
    """Extended to support LaTeX/PDF generation."""

    @staticmethod
    def get_exporter(format: str) -> BaseExporter:
        exporters = {
            'csv': CSVExporter,
            'json': JSONExporter,
            'xlsx': ExcelExporter,
            'xml': XMLExporter,
            'latex': LaTeXExporter,      # NEW
            'latex-pdf': LaTeXPDFExporter,  # NEW
        }
        return exporters[format]()
```

### 3.3 LaTeX Service Interface

```python
# backend/app/services/latex/generator.py

from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from pylatexenc.latexencode import unicode_to_latex

class LaTeXGenerator:
    """Generate LaTeX documents from templates."""

    def __init__(self, template_dir: Path):
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            block_start_string=r'\BLOCK{',
            block_end_string='}',
            variable_start_string=r'\VAR{',
            variable_end_string='}',
            trim_blocks=True,
            autoescape=False,
        )

    def sanitize(self, text: str) -> str:
        """Sanitize text for safe LaTeX inclusion."""
        return unicode_to_latex(text)

    def render_mfr(self, mfr_data: MFRData) -> str:
        """Render an MFR document."""
        template = self.env.get_template('mfr_standard.tex')

        # Sanitize all string fields
        safe_data = {
            k: self.sanitize(v) if isinstance(v, str) else v
            for k, v in asdict(mfr_data).items()
        }

        return template.render(**safe_data)

    def render_compliance_report(
        self,
        report_data: ComplianceReportData
    ) -> str:
        """Render ACGME compliance report."""
        template = self.env.get_template('report_acgme.tex')
        return template.render(**self._prepare_report_data(report_data))
```

### 3.4 Compilation Options

**Option A: Docker-Based Compilation (Recommended)**
```dockerfile
# Dockerfile.latex
FROM texlive/texlive:latest

WORKDIR /documents
COPY templates/latex /templates

ENTRYPOINT ["latexmk", "-pdf", "-interaction=nonstopmode"]
```

```python
# backend/app/services/latex/compiler.py

import subprocess
from pathlib import Path

class LaTeXCompiler:
    """Compile LaTeX to PDF using Docker."""

    def compile_to_pdf(self, latex_content: str, output_path: Path) -> Path:
        # Write .tex file
        tex_path = output_path.with_suffix('.tex')
        tex_path.write_text(latex_content)

        # Run compilation in Docker
        result = subprocess.run([
            'docker', 'run', '--rm',
            '-v', f'{tex_path.parent}:/documents',
            'residency-latex',
            tex_path.name
        ], capture_output=True)

        if result.returncode != 0:
            raise CompilationError(result.stderr.decode())

        return output_path.with_suffix('.pdf')
```

**Option B: System LaTeX Installation**
```python
def compile_with_latexmk(tex_path: Path) -> Path:
    """Compile using system latexmk."""
    subprocess.run([
        'latexmk', '-pdf', '-interaction=nonstopmode',
        '-output-directory', str(tex_path.parent),
        str(tex_path)
    ], check=True)
    return tex_path.with_suffix('.pdf')
```

---

## Part 4: Implementation Comparison

### 4.1 Approach Comparison Matrix

| Factor | Jinja2 + Templates | PyLaTeX | Current ReportLab |
|--------|-------------------|---------|-------------------|
| **Setup Complexity** | Low | Medium | Already done |
| **Template Maintenance** | Easy (designers) | Hard (developers) | Medium |
| **Output Quality** | ✅ Professional LaTeX | ✅ Professional LaTeX | Good but not LaTeX |
| **Dynamic Content** | Good | Excellent | Excellent |
| **Math/Equations** | ✅ Native LaTeX | ✅ Native LaTeX | Limited |
| **Dependencies** | LaTeX runtime | LaTeX runtime | None |
| **Military Format** | ✅ Exact AR 25-50 | Possible | Custom |
| **Learning Curve** | Low | Medium | Already learned |

### 4.2 Recommended Hybrid Approach

| Document Type | Recommended Method | Rationale |
|---------------|-------------------|-----------|
| **MFRs** | Jinja2 + Templates | Fixed format, easy maintenance |
| **Compliance Reports** | PyLaTeX | Complex tables, dynamic content |
| **Clinical Summaries** | Current ReportLab | Already working, no LaTeX needed |
| **Formal Letters** | Jinja2 + Templates | Standard military format |

---

## Part 5: Security Considerations

### 5.1 OPSEC/PERSEC Compliance

**Input Sanitization (Mandatory):**
```python
# All user-supplied data MUST be sanitized
from pylatexenc.latexencode import unicode_to_latex

FORBIDDEN_LATEX_COMMANDS = [
    r'\input', r'\include', r'\write', r'\read',
    r'\immediate', r'\openout', r'\closeout'
]

def validate_latex_content(content: str) -> bool:
    """Reject content with dangerous LaTeX commands."""
    for cmd in FORBIDDEN_LATEX_COMMANDS:
        if cmd in content:
            raise SecurityError(f"Forbidden command: {cmd}")
    return True
```

**No PII in Templates:**
- Templates stored without real names/assignments
- Data injected at runtime from database
- Generated PDFs stored with restricted permissions

### 5.2 Audit Trail Integration

```python
# Log all document generation
from backend.app.models import ActivityLog

async def generate_mfr_with_audit(
    mfr_data: MFRData,
    generator: LaTeXGenerator,
    user_id: int,
    session: AsyncSession
) -> Path:
    # Generate document
    latex = generator.render_mfr(mfr_data)
    pdf_path = compiler.compile_to_pdf(latex)

    # Create audit log
    log = ActivityLog(
        action="mfr_generated",
        entity_type="document",
        entity_id=mfr_data.subject,
        actor_id=user_id,
        details={
            "mfr_type": mfr_data.subject[:50],
            "classification": mfr_data.classification,
            "pdf_hash": hashlib.sha256(pdf_path.read_bytes()).hexdigest()
        }
    )
    session.add(log)
    await session.commit()

    return pdf_path
```

---

## Part 6: Implementation Roadmap

### Phase 1: Foundation (Low Effort)
1. Add `pylatexenc` to requirements.txt
2. Create `backend/app/services/latex/` directory structure
3. Implement `sanitizer.py` wrapper
4. Create basic MFR template with Jinja2

### Phase 2: Template Library (Medium Effort)
1. Create AR 25-50 compliant MFR template
2. Add ACGME compliance report template
3. Integrate with existing template manager
4. Add to export factory

### Phase 3: Compilation Pipeline (Medium Effort)
1. Create Docker image with LaTeX runtime
2. Implement compilation service
3. Add PDF generation endpoint
4. Integrate with existing report routes

### Phase 4: Production Hardening (Higher Effort)
1. Add comprehensive input validation
2. Implement audit trail integration
3. Add template versioning
4. Create template validation tests

---

## Part 7: Dependencies to Add

### Required (Phase 1)
```txt
# Data sanitization for LaTeX
pylatexenc>=2.10
```

### Optional (Phase 2-3)
```txt
# Programmatic LaTeX generation
pylatex>=1.4.2

# Build automation
latexbuild>=0.4.0
```

### Docker Image (Phase 3)
```dockerfile
# Minimal LaTeX installation for document generation
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    latexmk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /documents
```

---

## Sources

### Core Libraries
- [PyLaTeX Documentation](https://jeltef.github.io/PyLaTeX/current/) - Official PyLaTeX 1.4.2 docs
- [PyLaTeX GitHub](https://github.com/JelteF/PyLaTeX) - Source repository
- [pylatexenc GitHub](https://github.com/phfaist/pylatexenc) - Unicode-to-LaTeX conversion
- [pylatexenc Documentation](https://pylatexenc.readthedocs.io/en/latest/latexencode/) - Encoding documentation

### Jinja2 + LaTeX Integration
- [latexbuild GitHub](https://github.com/pappasam/latexbuild) - Jinja2+LaTeX build system
- [LaGen GitHub](https://github.com/T2F-Labs/LaGen) - Professional LaTeX generation
- [templatex GitHub](https://github.com/dataset-sh/templatex) - Jinja2 dialect for LaTeX
- [Jinja in LaTeX - Thomas Niebler](https://www.thomas-niebler.de/2022/02/02/jinja-in-latex/) - Integration patterns
- [Generating reports with Jinja, LaTeX and Docker](https://www.leospairani.com/blog/2024/04/16/generating-reports-with-jinja-latex-and-docker/) - Docker compilation

### Military Document Standards
- [Army Memorandum Templates](https://www.armywriter.com/memorandum.htm) - AR 25-50 compliant templates
- [Air Force MFR Templates](https://www.airforcewriter.com/mfr.htm) - MFR format guide
- [DoD Correspondence Templates](https://www.esd.whs.mil/CMD/Templates/) - Official DoD templates

### ACGME Documentation
- [ACGME Common Program Requirements Guide](https://www.acgme.org/globalassets/pdfs/guide-to-the-common-program-requirements-residency.pdf) - Compliance documentation
- [ACGME Policies and Procedures](https://www.acgme.org/globalassets/ab_acgmepoliciesprocedures.pdf) - Reporting requirements

---

## Recommendation

**For the Residency Scheduler, the recommended approach is:**

1. **Jinja2 + Templates** for MFRs and standardized military documents
   - Leverages existing Jinja2 dependency
   - Easy for coordinators to maintain templates
   - Exact AR 25-50 compliance achievable

2. **pylatexenc** for data sanitization (mandatory)
   - Critical for OPSEC compliance
   - Handles special characters safely
   - Low integration effort

3. **Keep ReportLab** for current reports
   - Already working and tested
   - No additional dependencies
   - Good enough for internal reports

4. **Add LaTeX only for formal military documents** where exact format compliance matters
   - Risk acceptance MFRs
   - Compliance documentation for external audits
   - Formal correspondence requiring AR 25-50 format

This hybrid approach minimizes new dependencies while gaining LaTeX capabilities where they provide clear value.
