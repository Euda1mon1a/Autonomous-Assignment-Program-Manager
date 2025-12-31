# OVERNIGHT_BURN Metadata Extraction Template

**Purpose:** Guide for extracting structured metadata from reconnaissance files
**Status:** Ready to implement
**Format:** JSON registry + Python extraction scripts

---

## Overview

This template provides the complete metadata structure and extraction logic needed to build the FILE_REGISTRY.json database that powers fast lookups and vector database integration.

---

## Metadata Schema

### Complete File Record

```json
{
  "id": "BACKEND_001",
  "path": "SESSION_1_BACKEND/backend-service-patterns.md",
  "filename": "backend-service-patterns.md",
  "domain": "SESSION_1_BACKEND",
  "type": "patterns",
  "priority": "P1",
  "title": "Backend Service Layer Architecture Patterns Analysis",
  "summary": "Comprehensive analysis of 47 service classes with focus on error handling, async patterns, and N+1 query optimization. Shows 7.5/10 consistency with 267 error handling blocks and 87 eager loading operations.",
  "description_long": "SEARCH_PARTY reconnaissance of backend service layer analyzing 47 service files organized across constraints, resilience, export, batch and other subdirectories. Identifies strong foundational patterns with opportunities for improvement in error handling consistency, async/sync patterns, and database access abstraction.",
  "size_kb": 45.2,
  "word_count": 8342,
  "created_date": "2025-12-30",
  "last_modified": "2025-12-30",
  "status": "complete",
  "content_type": "markdown",
  "language": "en",

  "content_metrics": {
    "headers_count": 12,
    "code_blocks": 24,
    "code_languages": ["python", "sql", "yaml"],
    "tables": 5,
    "images": 0,
    "links_external": 3,
    "links_internal": 8
  },

  "classification": {
    "primary_category": "patterns",
    "secondary_categories": ["architecture", "best-practices"],
    "topics": ["service-layer", "error-handling", "async-await", "n+1-queries", "database-optimization"],
    "technologies": ["fastapi", "sqlalchemy", "asyncio", "pydantic"],
    "methodology": "SEARCH_PARTY (10 lenses)",
    "acgme_relevant": false,
    "security_relevant": false,
    "testing_relevant": true
  },

  "key_content": {
    "findings": [
      "87 eager loading operations showing strong performance awareness",
      "267 error handling blocks but inconsistent severity classification",
      "95 logging statements but missing structured logging in some critical paths",
      "10 direct db.query() calls in services that bypass repositories",
      "ExportFactory, HomeostasisService, SwapExecutor demonstrate excellent cohesion"
    ],
    "findings_count": 5,
    "critical_findings": ["bypass-repositories", "inconsistent-error-handling"],
    "recommendation_count": 8,
    "critical_recommendations": [
      "Consolidate error handling into typed exceptions",
      "Add structured logging to all critical paths",
      "Enforce repository pattern in all services"
    ],
    "action_items": [
      "Implement structured logging framework in critical services",
      "Refactor 10 service classes using direct db.query() to use repository pattern",
      "Create error handling standardization guide",
      "Add async/sync pattern consistency checks to code review"
    ],
    "action_items_count": 4
  },

  "structure": {
    "sections": [
      {
        "level": 1,
        "title": "Executive Summary",
        "subsections": [
          "Key Findings",
          "Architecture Overview"
        ]
      },
      {
        "level": 2,
        "title": "SEARCH_PARTY Analysis: 10 Lenses",
        "subsections": [
          "PERCEPTION",
          "INVESTIGATION",
          "ARCANA",
          "HISTORY",
          "INSIGHT",
          "RELIGION",
          "NATURE",
          "MEDICINE",
          "SURVIVAL",
          "STEALTH"
        ]
      }
    ]
  },

  "keywords": {
    "explicit": [
      "service",
      "architecture",
      "patterns",
      "async",
      "error-handling",
      "n+1-optimization",
      "sqlalchemy",
      "fastapi",
      "repository-pattern",
      "logging"
    ],
    "inferred": [
      "database-performance",
      "code-quality",
      "best-practices",
      "refactoring",
      "consistency"
    ],
    "acgme_terms": [],
    "security_terms": []
  },

  "dependencies": {
    "related_files": [
      {
        "id": "BACKEND_002",
        "filename": "backend-repository-patterns.md",
        "relationship": "complementary",
        "reason": "Shows repository pattern details for implementing recommendation"
      },
      {
        "id": "BACKEND_003",
        "filename": "backend-error-handling.md",
        "relationship": "detailed",
        "reason": "Deep dive on error handling patterns"
      },
      {
        "id": "BACKEND_005",
        "filename": "backend-auth-patterns.md",
        "relationship": "cross-domain",
        "reason": "Auth service patterns"
      },
      {
        "id": "SECURITY_001",
        "filename": "authorization-audit.md",
        "relationship": "cross-domain",
        "reason": "Security implications of service patterns"
      }
    ],
    "referenced_by": [
      "SESSION_1_BACKEND/README.md",
      "MASTER_INDEX.md"
    ],
    "prerequisite_reading": [
      "SESSION_1_BACKEND/README.md",
      "CLAUDE.md (Section: Architecture Patterns)"
    ]
  },

  "quality_metrics": {
    "completeness": 95,
    "clarity": 88,
    "actionability": 92,
    "code_example_quality": 90,
    "citation_accuracy": 85,
    "overall_quality_score": 90
  },

  "usage": {
    "primary_audience": ["backend-developers", "architects"],
    "secondary_audience": ["security-reviewers", "qa-engineers"],
    "use_cases": [
      "Implementing new backend services",
      "Refactoring existing services",
      "Code review",
      "Architectural decisions",
      "Performance optimization"
    ],
    "reading_time_minutes": 25,
    "skill_level_required": "intermediate",
    "frequency_consulted": "high"
  },

  "tags": {
    "domain": "backend",
    "session": 1,
    "priority": "P1",
    "type": "patterns",
    "status": "complete",
    "content_maturity": "production",
    "review_status": "approved"
  },

  "vector_db": {
    "embedding_model": "text-embedding-ada-002",
    "embedding_dimensions": 1536,
    "embedding_created": "2025-12-30T00:00:00Z",
    "embedding_vector": "[0.001, 0.002, ...]",  // Omitted for brevity
    "semantic_neighbors": [
      {
        "id": "BACKEND_002",
        "similarity": 0.92,
        "reason": "Repository patterns are foundational to service layer"
      },
      {
        "id": "TESTING_004",
        "similarity": 0.85,
        "reason": "Testing service layer patterns"
      }
    ]
  }
}
```

---

## Python Extraction Implementation

### Script 1: Core Metadata Extractor

```python
#!/usr/bin/env python3
"""Extract metadata from markdown files."""

import re
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

class MetadataExtractor:
    """Extract structured metadata from reconnaissance documents."""

    def __init__(self, burn_dir: Path):
        self.burn_dir = burn_dir
        self.files = list(burn_dir.glob("SESSION_*/**.md"))

    def extract_from_file(self, file_path: Path) -> Dict:
        """Extract all metadata from a single file."""
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        metadata = {
            "path": str(file_path.relative_to(self.burn_dir)),
            "filename": file_path.name,
            "domain": self._extract_domain(file_path),
            "content_raw": content,
        }

        # Extract basic info
        metadata.update(self._extract_basic_info(content, file_path))

        # Extract content structure
        metadata.update(self._extract_structure(content))

        # Extract key content
        metadata.update(self._extract_key_content(content))

        # Classify and tag
        metadata.update(self._classify_and_tag(metadata))

        # Quality metrics
        metadata.update(self._calculate_quality_metrics(content, metadata))

        return metadata

    def _extract_domain(self, file_path: Path) -> str:
        """Extract domain from path."""
        parts = file_path.parts
        for part in parts:
            if part.startswith("SESSION_"):
                return part
        return "ROOT"

    def _extract_basic_info(self, content: str, file_path: Path) -> Dict:
        """Extract title, summary, date info."""

        # Extract title (first H1)
        title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else file_path.stem

        # Extract executive summary or first paragraph
        summary = self._extract_summary(content)

        # File metrics
        size_kb = file_path.stat().st_size / 1024
        word_count = len(content.split())

        # Dates
        now = datetime.now().isoformat()
        modified_date = datetime.fromtimestamp(
            file_path.stat().st_mtime
        ).isoformat()

        return {
            "title": title,
            "summary": summary,
            "size_kb": size_kb,
            "word_count": word_count,
            "created_date": "2025-12-30",  # Known OVERNIGHT_BURN date
            "last_modified": modified_date,
            "status": "complete",
        }

    def _extract_summary(self, content: str) -> str:
        """Extract 1-3 sentence summary."""
        # Try to find executive summary section
        exec_match = re.search(
            r'## Executive Summary\n\n(.+?)(?:\n##|\Z)',
            content,
            re.DOTALL
        )
        if exec_match:
            summary = exec_match.group(1).split('\n')[0]
            return summary[:200] + "..." if len(summary) > 200 else summary

        # Fallback: first paragraph after title
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('# '):
                # Next non-empty line
                for j in range(i+1, len(lines)):
                    if lines[j].strip() and not lines[j].startswith('#'):
                        return lines[j][:200] + "..." if len(lines[j]) > 200 else lines[j]

        return "No summary available"

    def _extract_structure(self, content: str) -> Dict:
        """Extract document structure."""

        # Count headers by level
        h1s = len(re.findall(r'^# ', content, re.MULTILINE))
        h2s = len(re.findall(r'^## ', content, re.MULTILINE))
        h3s = len(re.findall(r'^### ', content, re.MULTILINE))

        # Extract header titles
        headers = re.findall(r'^#{1,3} (.+)$', content, re.MULTILINE)

        # Count content elements
        code_blocks = re.findall(r'```(\w*)', content)
        code_languages = list(set(code_blocks))
        tables = len(re.findall(r'^\|', content, re.MULTILINE))
        links_external = len(re.findall(r'https?://', content))
        links_internal = len(re.findall(r'\[.+?\]\((?!https?)', content))

        return {
            "content_metrics": {
                "headers_count": h1s + h2s + h3s,
                "code_blocks": len(code_blocks),
                "code_languages": code_languages,
                "tables": tables,
                "links_external": links_external,
                "links_internal": links_internal,
            },
            "structure": {
                "h1_count": h1s,
                "h2_count": h2s,
                "h3_count": h3s,
                "headers": headers,
            }
        }

    def _extract_key_content(self, content: str) -> Dict:
        """Extract findings, recommendations, action items."""

        # Extract findings
        findings = self._extract_findings(content)

        # Extract recommendations
        recommendations = self._extract_recommendations(content)

        # Extract action items (TODO, MUST, SHOULD)
        action_items = self._extract_action_items(content)

        return {
            "key_content": {
                "findings": findings,
                "findings_count": len(findings),
                "recommendation_count": len(recommendations),
                "action_items": action_items,
                "action_items_count": len(action_items),
            }
        }

    def _extract_findings(self, content: str) -> List[str]:
        """Extract key findings."""
        findings = []

        # Look for "Finding" sections
        finding_sections = re.findall(
            r'^#{2,4}\s+.*[Ff]inding.*\n+(.+?)(?=\n##|\Z)',
            content,
            re.DOTALL
        )

        for section in finding_sections:
            # Extract bullet points
            bullets = re.findall(r'^[-*]\s+(.+)$', section, re.MULTILINE)
            findings.extend(bullets[:10])  # Top 10 findings

        return findings[:10]  # Return top 10

    def _extract_recommendations(self, content: str) -> List[str]:
        """Extract recommendations."""
        recs = []

        # Look for recommendations sections
        rec_sections = re.findall(
            r'^#{2,4}\s+.*[Rr]ecommendation.*\n+(.+?)(?=\n##|\Z)',
            content,
            re.DOTALL
        )

        for section in rec_sections:
            bullets = re.findall(r'^[-*]\s+(.+)$', section, re.MULTILINE)
            recs.extend(bullets[:10])

        return recs[:10]

    def _extract_action_items(self, content: str) -> List[str]:
        """Extract action items (TODO, MUST, SHOULD)."""
        items = []

        # Unchecked checkboxes
        items.extend(re.findall(
            r'^[-*] \[ \]\s+(.+)$',
            content,
            re.MULTILINE
        ))

        # Lines with TODO, MUST, SHOULD
        items.extend(re.findall(
            r'^[-*]\s+(?:TODO|MUST|SHOULD):\s+(.+)$',
            content,
            re.MULTILINE | re.IGNORECASE
        ))

        return items[:10]  # Top 10 items

    def _classify_and_tag(self, metadata: Dict) -> Dict:
        """Classify file type and assign tags."""

        filename = metadata["filename"].lower()
        content = metadata["content_raw"].lower()
        domain = metadata["domain"]

        # Determine file type
        if "index" in filename or "navigation" in filename:
            file_type = "index"
        elif "summary" in filename or "quick" in filename:
            file_type = "summary"
        elif "pattern" in filename:
            file_type = "patterns"
        elif "audit" in filename or "validation" in filename:
            file_type = "audit"
        elif "search_party" in filename or "reconnaissance" in filename:
            file_type = "reconnaissance"
        elif "enhanced" in filename or "specification" in filename:
            file_type = "specification"
        elif any(x in filename for x in ["api", "reference", "guide"]):
            file_type = "reference"
        else:
            file_type = "reference"

        # Extract priority
        if "index" in filename or "readme" in filename:
            priority = "P0"
        elif file_type in ["patterns", "audit", "reconnaissance"]:
            priority = "P1"
        elif file_type == "summary":
            priority = "P1" if "quick" not in filename else "P2"
        else:
            priority = "P2"

        # Extract keywords
        keywords = self._extract_keywords(metadata)

        # Technology tags
        technologies = self._extract_technologies(content)

        return {
            "type": file_type,
            "priority": priority,
            "keywords": keywords,
            "classification": {
                "primary_category": file_type,
                "technologies": technologies,
            }
        }

    def _extract_keywords(self, metadata: Dict) -> List[str]:
        """Extract keywords from headers and content."""
        keywords = set()

        # From headers
        for header in metadata["structure"].get("headers", []):
            # Split on common separators
            for word in re.split(r'[:\s-]', header.lower()):
                if len(word) > 3 and word not in ["the", "and", "for", "with"]:
                    keywords.add(word)

        # Domain-specific keywords
        if "acgme" in metadata["content_raw"].lower():
            keywords.add("acgme")
            keywords.add("compliance")

        if "security" in metadata["content_raw"].lower():
            keywords.add("security")
            keywords.add("authorization")

        return sorted(list(keywords))[:15]  # Top 15 keywords

    def _extract_technologies(self, content: str) -> List[str]:
        """Extract technology names mentioned."""
        techs = []

        technology_patterns = {
            "fastapi": r"fastapi",
            "sqlalchemy": r"sqlalchemy",
            "asyncio": r"asyncio|async/await",
            "pydantic": r"pydantic",
            "pytest": r"pytest",
            "react": r"react",
            "typescript": r"typescript",
            "nextjs": r"next\.js",
            "postgresql": r"postgresql|postgres",
            "redis": r"redis",
        }

        for tech, pattern in technology_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                techs.append(tech)

        return techs

    def _calculate_quality_metrics(self, content: str, metadata: Dict) -> Dict:
        """Calculate quality metrics."""

        # Completeness: % of expected sections present
        expected_sections = [
            "executive summary",
            "findings",
            "recommendations",
            "conclusion"
        ]
        found_sections = sum(
            1 for section in expected_sections
            if section in content.lower()
        )
        completeness = (found_sections / len(expected_sections)) * 100

        # Clarity: readability metrics
        # (simplified - just check for good structure)
        has_headers = metadata["content_metrics"]["headers_count"] > 3
        has_examples = metadata["content_metrics"]["code_blocks"] > 0
        has_tables = metadata["content_metrics"]["tables"] > 0
        clarity = (
            (40 if has_headers else 0) +
            (30 if has_examples else 0) +
            (30 if has_tables else 0)
        )

        # Actionability: presence of specific recommendations
        actionability = min(
            90,
            20 + (metadata["key_content"]["action_items_count"] * 10)
        )

        return {
            "quality_metrics": {
                "completeness": completeness,
                "clarity": clarity,
                "actionability": actionability,
                "overall_quality_score": (
                    completeness * 0.3 +
                    clarity * 0.3 +
                    actionability * 0.4
                ) / 100
            }
        }

    def extract_all(self) -> Dict:
        """Extract metadata from all files."""
        all_metadata = {
            "metadata": {
                "total_files": len(self.files),
                "generated_at": datetime.now().isoformat(),
                "version": "1.0"
            },
            "files": []
        }

        for i, file_path in enumerate(self.files, 1):
            print(f"Processing {i}/{len(self.files)}: {file_path.name}")

            metadata = self.extract_from_file(file_path)

            # Add unique ID
            domain = metadata["domain"]
            domain_num = domain.split("_")[1] if "_" in domain else "00"
            metadata["id"] = f"{domain_num}_{i:03d}"

            all_metadata["files"].append(metadata)

        return all_metadata
```

### Script 2: JSON Registry Generator

```python
#!/usr/bin/env python3
"""Generate FILE_REGISTRY.json from extracted metadata."""

import json
from pathlib import Path
from datetime import datetime

def generate_registry(metadata: Dict, output_path: Path) -> None:
    """Generate FILE_REGISTRY.json."""

    # Clean metadata for JSON serialization
    registry = {
        "metadata": metadata["metadata"],
        "summary": {
            "total_files": len(metadata["files"]),
            "by_type": {},
            "by_domain": {},
            "by_priority": {},
        },
        "files": []
    }

    # Build summary statistics
    for file_meta in metadata["files"]:
        file_type = file_meta.get("type", "unknown")
        domain = file_meta.get("domain", "unknown")
        priority = file_meta.get("priority", "P3")

        # Type distribution
        if file_type not in registry["summary"]["by_type"]:
            registry["summary"]["by_type"][file_type] = 0
        registry["summary"]["by_type"][file_type] += 1

        # Domain distribution
        if domain not in registry["summary"]["by_domain"]:
            registry["summary"]["by_domain"][domain] = {
                "count": 0,
                "files": []
            }
        registry["summary"]["by_domain"][domain]["count"] += 1
        registry["summary"]["by_domain"][domain]["files"].append(
            file_meta["filename"]
        )

        # Priority distribution
        if priority not in registry["summary"]["by_priority"]:
            registry["summary"]["by_priority"][priority] = 0
        registry["summary"]["by_priority"][priority] += 1

        # Simplified file entry (omit raw content, full embedding)
        simplified = {
            "id": file_meta.get("id"),
            "filename": file_meta.get("filename"),
            "domain": file_meta.get("domain"),
            "type": file_meta.get("type"),
            "priority": file_meta.get("priority"),
            "title": file_meta.get("title"),
            "summary": file_meta.get("summary"),
            "size_kb": file_meta.get("size_kb"),
            "word_count": file_meta.get("word_count"),
            "keywords": file_meta.get("keywords", []),
            "action_items_count": (
                file_meta.get("key_content", {})
                .get("action_items_count", 0)
            ),
            "quality_score": (
                file_meta.get("quality_metrics", {})
                .get("overall_quality_score", 0)
            ),
        }

        registry["files"].append(simplified)

    # Write JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, default=str)

    print(f"Registry written to: {output_path}")
    print(f"Total files indexed: {registry['metadata']['total_files']}")
    print(f"By type: {registry['summary']['by_type']}")
```

### Script 3: Batch Execution

```python
#!/usr/bin/env python3
"""Main script to extract and register all metadata."""

from pathlib import Path
import json

# Configuration
BURN_DIR = Path(
    "/Users/aaronmontgomery/"
    "Autonomous-Assignment-Program-Manager/"
    ".claude/Scratchpad/OVERNIGHT_BURN"
)
OUTPUT_JSON = BURN_DIR / "FILE_REGISTRY.json"
OUTPUT_MASTER = BURN_DIR / "MASTER_INDEX_AUTO.md"

def main():
    """Execute full extraction and registration pipeline."""

    print("Starting metadata extraction pipeline...")
    print(f"Source: {BURN_DIR}")
    print()

    # Phase 1: Extract
    print("Phase 1: Extracting metadata from all files...")
    extractor = MetadataExtractor(BURN_DIR)
    metadata = extractor.extract_all()

    print(f"Extracted metadata for {len(metadata['files'])} files\n")

    # Phase 2: Generate registry
    print("Phase 2: Generating FILE_REGISTRY.json...")
    generate_registry(metadata, OUTPUT_JSON)
    print(f"Registry saved to: {OUTPUT_JSON}\n")

    # Phase 3: Generate master index (optional)
    print("Phase 3: Generating MASTER_INDEX_AUTO.md...")
    # [Master index generation code here]
    print(f"Master index saved to: {OUTPUT_MASTER}\n")

    print("Pipeline complete!")
    print()
    print("Next steps:")
    print("1. Review FILE_REGISTRY.json for accuracy")
    print("2. Manual enhancement for priority/cross-references")
    print("3. Load into vector database")

if __name__ == "__main__":
    main()
```

---

## File Type Classification Rules

### Index/Navigation (→ Priority P0)

**Patterns:**
- Filename contains: `index`, `INDEX`, `readme`, `README`, `navigation`
- Content contains: "Table of Contents", "Quick Navigation", "Document Index"

**Action:** Mark as priority P0, type "index"

### Summary/Digest (→ Priority P1-2)

**Patterns:**
- Filename contains: `summary`, `SUMMARY`, `quick`, `quick_reference`
- Content contains: "Executive Summary", "TL;DR", "Key Findings"
- Shorter files (<20 KB)

**Action:** Mark as priority P1 if comprehensive, P2 if quick reference

### Pattern/Practice (→ Priority P1)

**Patterns:**
- Filename contains: `-patterns`, `-best`, `-practices`
- Content contains code examples (3+ code blocks)
- Discusses multiple related approaches

**Action:** Mark as priority P1, increment quality score for code examples

### Audit/Assessment (→ Priority P1)

**Patterns:**
- Filename contains: `audit`, `AUDIT`, `validation`, `VALIDATION`, `findings`
- Content contains: "Finding", "Recommendation", "Risk"
- Includes metrics, scoring, or severity levels

**Action:** Mark as priority P1, extract critical findings

### Reconnaissance (→ Priority P1)

**Patterns:**
- Filename contains: `search_party`, `SEARCH_PARTY`, `reconnaissance`, `RECONNAISSANCE`
- Content mentions: SEARCH_PARTY, lenses, methodology
- Includes "Findings", "Recommendations"

**Action:** Mark as priority P1, extract methodology and findings

### Reference/API (→ Priority P1-2)

**Patterns:**
- Filename contains: `-reference`, `-api`, `-spec`, `specification`
- Longer documents (20+ KB) with tables
- Organized sections for different topics

**Action:** Mark as priority P1 for frequently-used items, P2 for specialized

---

## Usage Example

```bash
# 1. Extract metadata
python3 /tmp/extract_metadata_comprehensive.py > extraction.log

# 2. Generate registry
python3 /tmp/generate_registry.py

# 3. Verify output
ls -lh /Users/aaronmontgomery/.../OVERNIGHT_BURN/FILE_REGISTRY.json

# 4. Load into vector DB
python3 /tmp/load_to_vectordb.py
```

---

## Next Steps

1. Implement metadata extraction scripts
2. Run extraction on all OVERNIGHT_BURN files
3. Manual enhancement: cross-references, priority adjustments
4. Generate FILE_REGISTRY.json
5. Test retrieval patterns
6. Load into vector database

See **RAG_INDEXING_PLAN.md** for complete implementation roadmap.

---

**Status:** Template complete, ready for implementation
**Estimated Time:** 2-3 hours for full extraction + verification
