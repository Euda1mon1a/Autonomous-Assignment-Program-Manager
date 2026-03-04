# MCP Server Specification - Residency Scheduler

> **Version:** 1.0.0
> **Last Updated:** 2025-12-19
> **Purpose:** Model Context Protocol (MCP) server specification for exposing scheduling functionality to AI assistants

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Authentication](#authentication)
4. [Resources](#resources)
5. [Tools](#tools)
6. [Prompts](#prompts)
7. [Error Handling](#error-handling)
8. [Implementation Guide](#implementation-guide)
9. [Security Considerations](#security-considerations)
10. [Testing Strategy](#testing-strategy)

---

## Overview

### Purpose

This MCP server exposes the Residency Scheduler's scheduling, resilience, and analytics capabilities to AI assistants through a standardized protocol. It enables:

- **Read-only access** to schedule data, health metrics, and analytics
- **Action execution** for schedule validation, swap feasibility, and generation
- **Decision support** through contingency analysis and conflict resolution

### Scope

**Included:**
- Schedule viewing and analysis
- Constraint validation
- Swap feasibility checking
- Resilience health monitoring
- Workload and fairness analytics
- Schedule generation coordination

**Excluded:**
- Patient data (handled by MyEvaluations)
- Direct database manipulation
- User management
- ACGME compliance tracking (delegated to MyEvaluations)

### Protocol Version

- **MCP Version:** 2024-11-05
- **Server Name:** `residency-scheduler-mcp`
- **Server Version:** `1.0.0`

---

## Architecture

### System Design

```
┌─────────────────────────────────────────────────────────┐
│                    AI Assistant                         │
│                  (Claude Desktop)                       │
└──────────────────────┬──────────────────────────────────┘
                       │ MCP Protocol
                       │ (HTTP/SSE)
┌──────────────────────▼──────────────────────────────────┐
│              MCP Server (Python)                        │
│  ┌─────────────────────────────────────────────────┐   │
│  │  MCP Protocol Handler                           │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  Resource Providers                             │   │
│  │  - Schedule Provider                            │   │
│  │  - Resilience Provider                          │   │
│  │  - Analytics Provider                           │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  Tool Handlers                                  │   │
│  │  - Validation Handler                           │   │
│  │  - Swap Handler                                 │   │
│  │  - Contingency Handler                          │   │
│  │  - Generation Handler                           │   │
│  └─────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/WebSocket
┌──────────────────────▼──────────────────────────────────┐
│           FastAPI Backend                               │
│  - /api/v1/schedules                                    │
│  - /api/v1/resilience                                   │
│  - /api/v1/analytics                                    │
│  - /api/v1/swaps                                        │
└─────────────────────────────────────────────────────────┘
```

### Communication Flow

1. **Client Request** → MCP Protocol (JSON-RPC 2.0)
2. **MCP Server** → Authenticate & Validate
3. **MCP Server** → Call FastAPI Backend (HTTP/REST)
4. **FastAPI Backend** → Execute business logic
5. **FastAPI Backend** → Return response
6. **MCP Server** → Transform to MCP format
7. **MCP Server** → Return to client

---

## Authentication

### Authentication Flow

All requests must include a valid JWT token in the `Authorization` header when the MCP server calls the FastAPI backend.

#### JWT Token Structure

```json
{
  "sub": "user_id_123",
  "email": "coordinator@hospital.mil",
  "role": "COORDINATOR",
  "exp": 1734630000,
  "iat": 1734626400
}
```

#### Role-Based Access Control

| Resource/Tool | Required Role | Notes |
|--------------|---------------|-------|
| `schedule://current` | Any authenticated user | Read-only |
| `schedule://person/{id}` | COORDINATOR, ADMIN, or self | Privacy protection |
| `schedule://blocks` | Any authenticated user | Reference data |
| `resilience://health` | COORDINATOR, ADMIN | System monitoring |
| `analytics://fairness` | COORDINATOR, ADMIN | Metrics access |
| `analytics://workload` | COORDINATOR, ADMIN | Metrics access |
| `validate_schedule` | COORDINATOR, ADMIN | Action |
| `check_swap_feasibility` | FACULTY, COORDINATOR, ADMIN | Action |
| `analyze_contingency` | COORDINATOR, ADMIN | Action |
| `suggest_resolution` | COORDINATOR, ADMIN | Action |
| `generate_schedule` | COORDINATOR, ADMIN | Privileged action |

### Configuration

The MCP server reads credentials from environment variables:

```bash
# MCP Server Configuration
MCP_SERVER_PORT=3000
MCP_SERVER_HOST=localhost
MCP_TRANSPORT=http  # or sse

# Backend API Configuration
BACKEND_API_URL=http://localhost:8000
BACKEND_API_KEY=<secret_api_key>

# JWT Configuration
JWT_SECRET_KEY=<secret_key>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
```

---

## Resources

Resources represent **read-only** data sources accessible through the MCP protocol.

### 1. `schedule://current`

**Description:** Current academic year schedule with all assignments.

**URI Template:** `schedule://current`

**JSON Schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "uri": {
      "type": "string",
      "const": "schedule://current"
    },
    "name": {
      "type": "string",
      "const": "Current Academic Year Schedule"
    },
    "description": {
      "type": "string",
      "const": "Complete schedule for the current academic year with all assignments"
    },
    "mimeType": {
      "type": "string",
      "const": "application/json"
    }
  },
  "required": ["uri", "name", "description", "mimeType"]
}
```

**Response Schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "academic_year": {
      "type": "string",
      "pattern": "^\\d{4}-\\d{4}$",
      "example": "2024-2025"
    },
    "start_date": {
      "type": "string",
      "format": "date",
      "example": "2024-07-01"
    },
    "end_date": {
      "type": "string",
      "format": "date",
      "example": "2025-06-30"
    },
    "total_blocks": {
      "type": "integer",
      "example": 730
    },
    "assignments": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/Assignment"
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "generated_at": {
          "type": "string",
          "format": "date-time"
        },
        "total_assignments": {
          "type": "integer"
        },
        "unique_persons": {
          "type": "integer"
        },
        "compliance_status": {
          "type": "string",
          "enum": ["COMPLIANT", "VIOLATIONS", "UNKNOWN"]
        }
      }
    }
  },
  "definitions": {
    "Assignment": {
      "type": "object",
      "properties": {
        "id": {
          "type": "string",
          "format": "uuid"
        },
        "person_id": {
          "type": "string",
          "format": "uuid"
        },
        "person_name": {
          "type": "string"
        },
        "person_role": {
          "type": "string",
          "enum": ["FACULTY", "RESIDENT", "RN", "LPN", "MSA"]
        },
        "block_id": {
          "type": "string",
          "format": "uuid"
        },
        "block_date": {
          "type": "string",
          "format": "date"
        },
        "block_session": {
          "type": "string",
          "enum": ["AM", "PM"]
        },
        "rotation_id": {
          "type": "string",
          "format": "uuid"
        },
        "rotation_name": {
          "type": "string"
        },
        "hours": {
          "type": "number",
          "minimum": 0,
          "maximum": 12
        }
      },
      "required": [
        "id",
        "person_id",
        "person_name",
        "person_role",
        "block_id",
        "block_date",
        "block_session",
        "rotation_id",
        "rotation_name",
        "hours"
      ]
    }
  },
  "required": [
    "academic_year",
    "start_date",
    "end_date",
    "total_blocks",
    "assignments",
    "metadata"
  ]
}
```

**Example Response:**

```json
{
  "academic_year": "2024-2025",
  "start_date": "2024-07-01",
  "end_date": "2025-06-30",
  "total_blocks": 730,
  "assignments": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "person_id": "p1234567-89ab-cdef-0123-456789abcdef",
      "person_name": "Dr. Jane Smith",
      "person_role": "FACULTY",
      "block_id": "b1234567-89ab-cdef-0123-456789abcdef",
      "block_date": "2024-07-01",
      "block_session": "AM",
      "rotation_id": "r1234567-89ab-cdef-0123-456789abcdef",
      "rotation_name": "Clinic",
      "hours": 4.0
    }
  ],
  "metadata": {
    "generated_at": "2024-06-15T10:30:00Z",
    "total_assignments": 5840,
    "unique_persons": 20,
    "compliance_status": "COMPLIANT"
  }
}
```

---

### 2. `schedule://person/{id}`

**Description:** Schedule for a specific person (faculty or resident).

**URI Template:** `schedule://person/{id}`

**URI Parameters:**
- `id` (string, required): UUID of the person

**JSON Schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "uri": {
      "type": "string",
      "pattern": "^schedule://person/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    },
    "name": {
      "type": "string"
    },
    "description": {
      "type": "string"
    },
    "mimeType": {
      "type": "string",
      "const": "application/json"
    }
  },
  "required": ["uri", "name", "description", "mimeType"]
}
```

**Response Schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "person": {
      "type": "object",
      "properties": {
        "id": {
          "type": "string",
          "format": "uuid"
        },
        "name": {
          "type": "string"
        },
        "email": {
          "type": "string",
          "format": "email"
        },
        "role": {
          "type": "string",
          "enum": ["FACULTY", "RESIDENT", "RN", "LPN", "MSA"]
        },
        "pgy_level": {
          "type": "integer",
          "minimum": 1,
          "maximum": 3,
          "description": "Post-Graduate Year level (residents only)"
        }
      },
      "required": ["id", "name", "email", "role"]
    },
    "assignments": {
      "type": "array",
      "items": {
        "$ref": "schedule://current#/definitions/Assignment"
      }
    },
    "statistics": {
      "type": "object",
      "properties": {
        "total_hours": {
          "type": "number"
        },
        "avg_hours_per_week": {
          "type": "number"
        },
        "total_clinic_hours": {
          "type": "number"
        },
        "total_inpatient_hours": {
          "type": "number"
        },
        "total_procedure_hours": {
          "type": "number"
        },
        "days_off": {
          "type": "integer"
        },
        "longest_stretch_without_day_off": {
          "type": "integer"
        }
      }
    },
    "compliance": {
      "type": "object",
      "properties": {
        "is_compliant": {
          "type": "boolean"
        },
        "violations": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "rule": {
                "type": "string",
                "enum": ["80_HOUR_RULE", "1_IN_7_RULE", "SUPERVISION_RATIO"]
              },
              "description": {
                "type": "string"
              },
              "severity": {
                "type": "string",
                "enum": ["WARNING", "ERROR", "CRITICAL"]
              },
              "date_range": {
                "type": "object",
                "properties": {
                  "start": {
                    "type": "string",
                    "format": "date"
                  },
                  "end": {
                    "type": "string",
                    "format": "date"
                  }
                }
              }
            }
          }
        }
      }
    }
  },
  "required": ["person", "assignments", "statistics", "compliance"]
}
```

**Example Response:**

```json
{
  "person": {
    "id": "p1234567-89ab-cdef-0123-456789abcdef",
    "name": "Dr. Jane Smith",
    "email": "jane.smith@hospital.mil",
    "role": "FACULTY"
  },
  "assignments": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "person_id": "p1234567-89ab-cdef-0123-456789abcdef",
      "person_name": "Dr. Jane Smith",
      "person_role": "FACULTY",
      "block_id": "b1234567-89ab-cdef-0123-456789abcdef",
      "block_date": "2024-07-01",
      "block_session": "AM",
      "rotation_id": "r1234567-89ab-cdef-0123-456789abcdef",
      "rotation_name": "Clinic",
      "hours": 4.0
    }
  ],
  "statistics": {
    "total_hours": 1920.0,
    "avg_hours_per_week": 40.0,
    "total_clinic_hours": 960.0,
    "total_inpatient_hours": 480.0,
    "total_procedure_hours": 480.0,
    "days_off": 104,
    "longest_stretch_without_day_off": 6
  },
  "compliance": {
    "is_compliant": true,
    "violations": []
  }
}
```

---

### 3. `schedule://blocks`

**Description:** Block definitions for the academic year (AM/PM sessions).

**URI Template:** `schedule://blocks`

**JSON Schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "uri": {
      "type": "string",
      "const": "schedule://blocks"
    },
    "name": {
      "type": "string",
      "const": "Block Definitions"
    },
    "description": {
      "type": "string",
      "const": "All scheduling blocks (AM/PM sessions) for the academic year"
    },
    "mimeType": {
      "type": "string",
      "const": "application/json"
    }
  },
  "required": ["uri", "name", "description", "mimeType"]
}
```

**Response Schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "academic_year": {
      "type": "string",
      "pattern": "^\\d{4}-\\d{4}$"
    },
    "total_blocks": {
      "type": "integer",
      "const": 730
    },
    "blocks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "format": "uuid"
          },
          "date": {
            "type": "string",
            "format": "date"
          },
          "session": {
            "type": "string",
            "enum": ["AM", "PM"]
          },
          "day_of_week": {
            "type": "string",
            "enum": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
          },
          "is_holiday": {
            "type": "boolean"
          },
          "is_weekend": {
            "type": "boolean"
          },
          "typical_hours": {
            "type": "number",
            "enum": [4.0, 0.0]
          }
        },
        "required": ["id", "date", "session", "day_of_week", "is_holiday", "is_weekend", "typical_hours"]
      }
    }
  },
  "required": ["academic_year", "total_blocks", "blocks"]
}
```

**Example Response:**

```json
{
  "academic_year": "2024-2025",
  "total_blocks": 730,
  "blocks": [
    {
      "id": "b1234567-89ab-cdef-0123-456789abcdef",
      "date": "2024-07-01",
      "session": "AM",
      "day_of_week": "Monday",
      "is_holiday": false,
      "is_weekend": false,
      "typical_hours": 4.0
    },
    {
      "id": "b2234567-89ab-cdef-0123-456789abcdef",
      "date": "2024-07-01",
      "session": "PM",
      "day_of_week": "Monday",
      "is_holiday": false,
      "is_weekend": false,
      "typical_hours": 4.0
    }
  ]
}
```

---

### 4. `resilience://health`

**Description:** Current resilience framework health status.

**URI Template:** `resilience://health`

**JSON Schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "uri": {
      "type": "string",
      "const": "resilience://health"
    },
    "name": {
      "type": "string",
      "const": "Resilience Health Status"
    },
    "description": {
      "type": "string",
      "const": "Current system health status from resilience framework"
    },
    "mimeType": {
      "type": "string",
      "const": "application/json"
    }
  },
  "required": ["uri", "name", "description", "mimeType"]
}
```

**Response Schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "overall_status": {
      "type": "string",
      "enum": ["GREEN", "YELLOW", "ORANGE", "RED", "BLACK"],
      "description": "Defense in depth safety level"
    },
    "checked_at": {
      "type": "string",
      "format": "date-time"
    },
    "metrics": {
      "type": "object",
      "properties": {
        "utilization_rate": {
          "type": "number",
          "minimum": 0,
          "maximum": 1,
          "description": "Current system utilization (0.0 - 1.0)"
        },
        "available_capacity": {
          "type": "number",
          "description": "Available hours before 80% threshold"
        },
        "n_minus_1_vulnerable": {
          "type": "boolean",
          "description": "System vulnerable to single person loss"
        },
        "n_minus_2_vulnerable": {
          "type": "boolean",
          "description": "System vulnerable to two person loss"
        },
        "critical_positions": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "person_id": {
                "type": "string",
                "format": "uuid"
              },
              "person_name": {
                "type": "string"
              },
              "impact_score": {
                "type": "number",
                "minimum": 0,
                "maximum": 1
              },
              "reason": {
                "type": "string"
              }
            }
          }
        }
      }
    },
    "alerts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "severity": {
            "type": "string",
            "enum": ["INFO", "WARNING", "ERROR", "CRITICAL"]
          },
          "message": {
            "type": "string"
          },
          "timestamp": {
            "type": "string",
            "format": "date-time"
          }
        }
      }
    },
    "recommendations": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  },
  "required": ["overall_status", "checked_at", "metrics", "alerts", "recommendations"]
}
```

**Example Response:**

```json
{
  "overall_status": "YELLOW",
  "checked_at": "2024-12-19T14:30:00Z",
  "metrics": {
    "utilization_rate": 0.78,
    "available_capacity": 160.0,
    "n_minus_1_vulnerable": true,
    "n_minus_2_vulnerable": false,
    "critical_positions": [
      {
        "person_id": "p1234567-89ab-cdef-0123-456789abcdef",
        "person_name": "Dr. Jane Smith",
        "impact_score": 0.85,
        "reason": "Only faculty member qualified for advanced procedures"
      }
    ]
  },
  "alerts": [
    {
      "severity": "WARNING",
      "message": "System approaching 80% utilization threshold",
      "timestamp": "2024-12-19T14:30:00Z"
    },
    {
      "severity": "WARNING",
      "message": "N-1 contingency failure: Loss of Dr. Jane Smith would create coverage gaps",
      "timestamp": "2024-12-19T14:30:00Z"
    }
  ],
  "recommendations": [
    "Cross-train additional faculty for advanced procedures",
    "Review schedule to reduce utilization before peak season",
    "Consider hiring additional qualified personnel"
  ]
}
```

---

### 5. `analytics://fairness`

**Description:** Fairness distribution metrics across all personnel.

**URI Template:** `analytics://fairness`

**JSON Schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "uri": {
      "type": "string",
      "const": "analytics://fairness"
    },
    "name": {
      "type": "string",
      "const": "Fairness Distribution Metrics"
    },
    "description": {
      "type": "string",
      "const": "Statistical analysis of workload fairness across personnel"
    },
    "mimeType": {
      "type": "string",
      "const": "application/json"
    }
  },
  "required": ["uri", "name", "description", "mimeType"]
}
```

**Response Schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "calculated_at": {
      "type": "string",
      "format": "date-time"
    },
    "overall_fairness_score": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "0 = perfectly unfair, 1 = perfectly fair"
    },
    "by_role": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "mean_hours": {
            "type": "number"
          },
          "median_hours": {
            "type": "number"
          },
          "std_dev": {
            "type": "number"
          },
          "min_hours": {
            "type": "number"
          },
          "max_hours": {
            "type": "number"
          },
          "gini_coefficient": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "0 = perfect equality, 1 = perfect inequality"
          }
        }
      }
    },
    "by_rotation": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "mean_assignments": {
            "type": "number"
          },
          "median_assignments": {
            "type": "number"
          },
          "std_dev": {
            "type": "number"
          },
          "fairness_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 1
          }
        }
      }
    },
    "outliers": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "person_id": {
            "type": "string",
            "format": "uuid"
          },
          "person_name": {
            "type": "string"
          },
          "role": {
            "type": "string"
          },
          "total_hours": {
            "type": "number"
          },
          "deviation_from_mean": {
            "type": "number"
          },
          "z_score": {
            "type": "number"
          }
        }
      }
    }
  },
  "required": ["calculated_at", "overall_fairness_score", "by_role", "by_rotation", "outliers"]
}
```

**Example Response:**

```json
{
  "calculated_at": "2024-12-19T14:30:00Z",
  "overall_fairness_score": 0.87,
  "by_role": {
    "FACULTY": {
      "mean_hours": 1920.0,
      "median_hours": 1900.0,
      "std_dev": 120.5,
      "min_hours": 1760.0,
      "max_hours": 2080.0,
      "gini_coefficient": 0.08
    },
    "RESIDENT": {
      "mean_hours": 2080.0,
      "median_hours": 2080.0,
      "std_dev": 60.2,
      "min_hours": 2000.0,
      "max_hours": 2160.0,
      "gini_coefficient": 0.04
    }
  },
  "by_rotation": {
    "Clinic": {
      "mean_assignments": 146.0,
      "median_assignments": 145.0,
      "std_dev": 8.3,
      "fairness_score": 0.92
    },
    "Inpatient": {
      "mean_assignments": 73.0,
      "median_assignments": 72.0,
      "std_dev": 6.1,
      "fairness_score": 0.88
    }
  },
  "outliers": [
    {
      "person_id": "p1234567-89ab-cdef-0123-456789abcdef",
      "person_name": "Dr. John Doe",
      "role": "FACULTY",
      "total_hours": 2080.0,
      "deviation_from_mean": 160.0,
      "z_score": 1.33
    }
  ]
}
```

---

### 6. `analytics://workload`

**Description:** Workload metrics per person with trend analysis.

**URI Template:** `analytics://workload`

**JSON Schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "uri": {
      "type": "string",
      "const": "analytics://workload"
    },
    "name": {
      "type": "string",
      "const": "Workload Metrics"
    },
    "description": {
      "type": "string",
      "const": "Detailed workload metrics and trends per person"
    },
    "mimeType": {
      "type": "string",
      "const": "application/json"
    }
  },
  "required": ["uri", "name", "description", "mimeType"]
}
```

**Response Schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "calculated_at": {
      "type": "string",
      "format": "date-time"
    },
    "time_period": {
      "type": "object",
      "properties": {
        "start_date": {
          "type": "string",
          "format": "date"
        },
        "end_date": {
          "type": "string",
          "format": "date"
        }
      }
    },
    "workload_by_person": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "person_id": {
            "type": "string",
            "format": "uuid"
          },
          "person_name": {
            "type": "string"
          },
          "role": {
            "type": "string"
          },
          "total_hours": {
            "type": "number"
          },
          "avg_hours_per_week": {
            "type": "number"
          },
          "peak_week_hours": {
            "type": "number"
          },
          "min_week_hours": {
            "type": "number"
          },
          "consecutive_days_worked": {
            "type": "integer"
          },
          "total_weekend_shifts": {
            "type": "integer"
          },
          "burnout_risk_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "0 = low risk, 1 = high risk"
          },
          "trend": {
            "type": "string",
            "enum": ["INCREASING", "STABLE", "DECREASING"]
          }
        }
      }
    },
    "summary": {
      "type": "object",
      "properties": {
        "total_staff": {
          "type": "integer"
        },
        "high_burnout_risk_count": {
          "type": "integer"
        },
        "avg_hours_per_person": {
          "type": "number"
        },
        "max_consecutive_days": {
          "type": "integer"
        }
      }
    }
  },
  "required": ["calculated_at", "time_period", "workload_by_person", "summary"]
}
```

**Example Response:**

```json
{
  "calculated_at": "2024-12-19T14:30:00Z",
  "time_period": {
    "start_date": "2024-07-01",
    "end_date": "2024-12-19"
  },
  "workload_by_person": [
    {
      "person_id": "p1234567-89ab-cdef-0123-456789abcdef",
      "person_name": "Dr. Jane Smith",
      "role": "FACULTY",
      "total_hours": 1120.0,
      "avg_hours_per_week": 44.8,
      "peak_week_hours": 60.0,
      "min_week_hours": 32.0,
      "consecutive_days_worked": 6,
      "total_weekend_shifts": 8,
      "burnout_risk_score": 0.35,
      "trend": "STABLE"
    }
  ],
  "summary": {
    "total_staff": 20,
    "high_burnout_risk_count": 2,
    "avg_hours_per_person": 1120.0,
    "max_consecutive_days": 6
  }
}
```

---

## Tools

Tools represent **actions** that can be performed through the MCP protocol.

### 1. `validate_schedule`

**Description:** Validate a schedule against all constraints (ACGME rules, staffing requirements, etc.).

**Input Schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "schedule_id": {
      "type": "string",
      "format": "uuid",
      "description": "ID of schedule to validate (optional, defaults to current)"
    },
    "validation_rules": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "80_HOUR_RULE",
          "1_IN_7_RULE",
          "SUPERVISION_RATIO",
          "MINIMUM_STAFFING",
          "CREDENTIAL_REQUIREMENTS",
          "ALL"
        ]
      },
      "default": ["ALL"]
    },
    "strict_mode": {
      "type": "boolean",
      "description": "If true, fail on any warning (not just errors)",
      "default": false
    }
  }
}
```

**Output Schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "is_valid": {
      "type": "boolean"
    },
    "validated_at": {
      "type": "string",
      "format": "date-time"
    },
    "schedule_id": {
      "type": "string",
      "format": "uuid"
    },
    "rules_checked": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "violations": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "rule": {
            "type": "string"
          },
          "severity": {
            "type": "string",
            "enum": ["WARNING", "ERROR", "CRITICAL"]
          },
          "message": {
            "type": "string"
          },
          "affected_person_id": {
            "type": "string",
            "format": "uuid"
          },
          "affected_person_name": {
            "type": "string"
          },
          "date_range": {
            "type": "object",
            "properties": {
              "start": {
                "type": "string",
                "format": "date"
              },
              "end": {
                "type": "string",
                "format": "date"
              }
            }
          },
          "details": {
            "type": "object",
            "additionalProperties": true
          }
        }
      }
    },
    "warnings": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "rule": {
            "type": "string"
          },
          "message": {
            "type": "string"
          },
          "affected_person_id": {
            "type": "string",
            "format": "uuid"
          }
        }
      }
    },
    "summary": {
      "type": "object",
      "properties": {
        "total_violations": {
          "type": "integer"
        },
        "critical_count": {
          "type": "integer"
        },
        "error_count": {
          "type": "integer"
        },
        "warning_count": {
          "type": "integer"
        }
      }
    }
  },
  "required": ["is_valid", "validated_at", "schedule_id", "rules_checked", "violations", "warnings", "summary"]
}
```

**Example Request:**

```json
{
  "name": "validate_schedule",
  "arguments": {
    "schedule_id": "s1234567-89ab-cdef-0123-456789abcdef",
    "validation_rules": ["80_HOUR_RULE", "1_IN_7_RULE"],
    "strict_mode": false
  }
}
```

**Example Response:**

```json
{
  "content": [
    {
      "type": "text",
      "text": "Schedule validation completed with 1 violation found."
    },
    {
      "type": "resource",
      "resource": {
        "uri": "validation://result/v1234567",
        "mimeType": "application/json",
        "text": JSON.stringify({
          "is_valid": false,
          "validated_at": "2024-12-19T14:30:00Z",
          "schedule_id": "s1234567-89ab-cdef-0123-456789abcdef",
          "rules_checked": ["80_HOUR_RULE", "1_IN_7_RULE"],
          "violations": [
            {
              "rule": "80_HOUR_RULE",
              "severity": "ERROR",
              "message": "Person exceeds 80 hours in 4-week period",
              "affected_person_id": "p1234567-89ab-cdef-0123-456789abcdef",
              "affected_person_name": "Dr. Jane Smith",
              "date_range": {
                "start": "2024-07-01",
                "end": "2024-07-28"
              },
              "details": {
                "total_hours": 84.5,
                "excess_hours": 4.5
              }
            }
          ],
          "warnings": [],
          "summary": {
            "total_violations": 1,
            "critical_count": 0,
            "error_count": 1,
            "warning_count": 0
          }
        })
      }
    }
  ]
}
```

**Error Responses:**

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Schedule validation could not be completed",
    "details": {
      "reason": "Schedule not found",
      "schedule_id": "s1234567-89ab-cdef-0123-456789abcdef"
    }
  }
}
```

---

### 2. `check_swap_feasibility`

**Description:** Pre-validate if a swap request is feasible before submission.

**Input Schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "swap_type": {
      "type": "string",
      "enum": ["ONE_TO_ONE", "ABSORB"],
      "description": "Type of swap to check"
    },
    "requester_id": {
      "type": "string",
      "format": "uuid",
      "description": "Person requesting the swap"
    },
    "block_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "description": "Blocks to be swapped",
      "minItems": 1
    },
    "target_person_id": {
      "type": "string",
      "format": "uuid",
      "description": "Target person for ONE_TO_ONE swaps"
    },
    "reason": {
      "type": "string",
      "maxLength": 500,
      "description": "Reason for swap request"
    }
  },
  "required": ["swap_type", "requester_id", "block_ids"],
  "dependencies": {
    "swap_type": {
      "oneOf": [
        {
          "properties": {
            "swap_type": {
              "const": "ONE_TO_ONE"
            }
          },
          "required": ["target_person_id"]
        },
        {
          "properties": {
            "swap_type": {
              "const": "ABSORB"
            }
          }
        }
      ]
    }
  }
}
```

**Output Schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "is_feasible": {
      "type": "boolean"
    },
    "checked_at": {
      "type": "string",
      "format": "date-time"
    },
    "swap_preview": {
      "type": "object",
      "properties": {
        "requester": {
          "type": "object",
          "properties": {
            "person_id": {
              "type": "string",
              "format": "uuid"
            },
            "person_name": {
              "type": "string"
            },
            "current_hours_this_week": {
              "type": "number"
            },
            "hours_after_swap": {
              "type": "number"
            }
          }
        },
        "target": {
          "type": "object",
          "properties": {
            "person_id": {
              "type": "string",
              "format": "uuid"
            },
            "person_name": {
              "type": "string"
            },
            "current_hours_this_week": {
              "type": "number"
            },
            "hours_after_swap": {
              "type": "number"
            }
          }
        }
      }
    },
    "compliance_check": {
      "type": "object",
      "properties": {
        "is_compliant": {
          "type": "boolean"
        },
        "violations": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "rule": {
                "type": "string"
              },
              "affected_person": {
                "type": "string",
                "enum": ["REQUESTER", "TARGET", "BOTH"]
              },
              "message": {
                "type": "string"
              }
            }
          }
        }
      }
    },
    "suggestions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "candidate_id": {
            "type": "string",
            "format": "uuid"
          },
          "candidate_name": {
            "type": "string"
          },
          "compatibility_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 1
          },
          "reason": {
            "type": "string"
          }
        }
      }
    },
    "blocking_reasons": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Reasons why swap cannot proceed"
    }
  },
  "required": ["is_feasible", "checked_at", "compliance_check"]
}
```

**Example Request:**

```json
{
  "name": "check_swap_feasibility",
  "arguments": {
    "swap_type": "ONE_TO_ONE",
    "requester_id": "p1234567-89ab-cdef-0123-456789abcdef",
    "block_ids": ["b1234567-89ab-cdef-0123-456789abcdef"],
    "target_person_id": "p2234567-89ab-cdef-0123-456789abcdef",
    "reason": "Family emergency - need to cover Monday AM shift"
  }
}
```

**Example Response:**

```json
{
  "content": [
    {
      "type": "text",
      "text": "Swap feasibility check completed. Swap is feasible with no compliance violations."
    },
    {
      "type": "resource",
      "resource": {
        "uri": "swap://feasibility/sf1234567",
        "mimeType": "application/json",
        "text": JSON.stringify({
          "is_feasible": true,
          "checked_at": "2024-12-19T14:30:00Z",
          "swap_preview": {
            "requester": {
              "person_id": "p1234567-89ab-cdef-0123-456789abcdef",
              "person_name": "Dr. Jane Smith",
              "current_hours_this_week": 40.0,
              "hours_after_swap": 36.0
            },
            "target": {
              "person_id": "p2234567-89ab-cdef-0123-456789abcdef",
              "person_name": "Dr. John Doe",
              "current_hours_this_week": 36.0,
              "hours_after_swap": 40.0
            }
          },
          "compliance_check": {
            "is_compliant": true,
            "violations": []
          },
          "blocking_reasons": []
        })
      }
    }
  ]
}
```

---

### 3. `analyze_contingency`

**Description:** Perform N-1/N-2 contingency analysis to identify vulnerabilities.

**Input Schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "analysis_type": {
      "type": "string",
      "enum": ["N_MINUS_1", "N_MINUS_2", "BOTH"],
      "default": "BOTH"
    },
    "scenario": {
      "type": "object",
      "properties": {
        "simulated_losses": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "person_id": {
                "type": "string",
                "format": "uuid"
              },
              "start_date": {
                "type": "string",
                "format": "date"
              },
              "end_date": {
                "type": "string",
                "format": "date"
              },
              "reason": {
                "type": "string",
                "enum": ["DEPLOYMENT", "TDY", "MEDICAL", "LEAVE", "OTHER"]
              }
            },
            "required": ["person_id", "start_date", "end_date", "reason"]
          }
        }
      },
      "description": "Optional: Simulate specific loss scenarios"
    },
    "include_mitigation_strategies": {
      "type": "boolean",
      "default": true,
      "description": "Include suggested mitigation strategies in response"
    }
  }
}
```

**Output Schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "analyzed_at": {
      "type": "string",
      "format": "date-time"
    },
    "analysis_type": {
      "type": "string",
      "enum": ["N_MINUS_1", "N_MINUS_2", "BOTH"]
    },
    "n_minus_1_result": {
      "type": "object",
      "properties": {
        "is_vulnerable": {
          "type": "boolean"
        },
        "critical_persons": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "person_id": {
                "type": "string",
                "format": "uuid"
              },
              "person_name": {
                "type": "string"
              },
              "role": {
                "type": "string"
              },
              "impact_score": {
                "type": "number",
                "minimum": 0,
                "maximum": 1
              },
              "affected_blocks": {
                "type": "integer"
              },
              "unique_qualifications": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              }
            }
          }
        }
      }
    },
    "n_minus_2_result": {
      "type": "object",
      "properties": {
        "is_vulnerable": {
          "type": "boolean"
        },
        "critical_pairs": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "person_1_id": {
                "type": "string",
                "format": "uuid"
              },
              "person_1_name": {
                "type": "string"
              },
              "person_2_id": {
                "type": "string",
                "format": "uuid"
              },
              "person_2_name": {
                "type": "string"
              },
              "combined_impact_score": {
                "type": "number",
                "minimum": 0,
                "maximum": 1
              },
              "affected_blocks": {
                "type": "integer"
              }
            }
          }
        }
      }
    },
    "mitigation_strategies": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "strategy": {
            "type": "string"
          },
          "priority": {
            "type": "string",
            "enum": ["HIGH", "MEDIUM", "LOW"]
          },
          "estimated_impact": {
            "type": "string"
          },
          "implementation_complexity": {
            "type": "string",
            "enum": ["LOW", "MEDIUM", "HIGH"]
          }
        }
      }
    }
  },
  "required": ["analyzed_at", "analysis_type"]
}
```

**Example Request:**

```json
{
  "name": "analyze_contingency",
  "arguments": {
    "analysis_type": "BOTH",
    "include_mitigation_strategies": true
  }
}
```

**Example Response:**

```json
{
  "content": [
    {
      "type": "text",
      "text": "Contingency analysis completed. System is vulnerable to single person loss (N-1)."
    },
    {
      "type": "resource",
      "resource": {
        "uri": "contingency://analysis/ca1234567",
        "mimeType": "application/json",
        "text": JSON.stringify({
          "analyzed_at": "2024-12-19T14:30:00Z",
          "analysis_type": "BOTH",
          "n_minus_1_result": {
            "is_vulnerable": true,
            "critical_persons": [
              {
                "person_id": "p1234567-89ab-cdef-0123-456789abcdef",
                "person_name": "Dr. Jane Smith",
                "role": "FACULTY",
                "impact_score": 0.85,
                "affected_blocks": 146,
                "unique_qualifications": ["Advanced Procedures", "ICU Coverage"]
              }
            ]
          },
          "n_minus_2_result": {
            "is_vulnerable": false,
            "critical_pairs": []
          },
          "mitigation_strategies": [
            {
              "strategy": "Cross-train Dr. John Doe for Advanced Procedures",
              "priority": "HIGH",
              "estimated_impact": "Reduces N-1 vulnerability by 70%",
              "implementation_complexity": "MEDIUM"
            },
            {
              "strategy": "Hire additional qualified faculty member",
              "priority": "HIGH",
              "estimated_impact": "Eliminates N-1 vulnerability",
              "implementation_complexity": "HIGH"
            }
          ]
        })
      }
    }
  ]
}
```

---

### 4. `suggest_resolution`

**Description:** Get AI-powered suggestions for resolving schedule conflicts.

**Input Schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "conflict_type": {
      "type": "string",
      "enum": [
        "UNDERSTAFFED",
        "OVERSTAFFED",
        "COMPLIANCE_VIOLATION",
        "SWAP_NEEDED",
        "COVERAGE_GAP",
        "CREDENTIAL_MISMATCH"
      ]
    },
    "affected_blocks": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "description": "Blocks affected by the conflict"
    },
    "affected_persons": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "description": "Persons affected by the conflict"
    },
    "constraints": {
      "type": "object",
      "properties": {
        "must_maintain_compliance": {
          "type": "boolean",
          "default": true
        },
        "prefer_minimal_changes": {
          "type": "boolean",
          "default": true
        },
        "available_persons": {
          "type": "array",
          "items": {
            "type": "string",
            "format": "uuid"
          },
          "description": "Limit suggestions to these persons"
        }
      }
    },
    "max_suggestions": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10,
      "default": 5
    }
  },
  "required": ["conflict_type", "affected_blocks"]
}
```

**Output Schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "generated_at": {
      "type": "string",
      "format": "date-time"
    },
    "conflict_summary": {
      "type": "object",
      "properties": {
        "type": {
          "type": "string"
        },
        "severity": {
          "type": "string",
          "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        },
        "description": {
          "type": "string"
        }
      }
    },
    "suggestions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string"
          },
          "title": {
            "type": "string"
          },
          "description": {
            "type": "string"
          },
          "confidence_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 1
          },
          "actions": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "action_type": {
                  "type": "string",
                  "enum": ["REASSIGN", "SWAP", "ADD_COVERAGE", "REMOVE_ASSIGNMENT"]
                },
                "block_id": {
                  "type": "string",
                  "format": "uuid"
                },
                "from_person_id": {
                  "type": "string",
                  "format": "uuid"
                },
                "to_person_id": {
                  "type": "string",
                  "format": "uuid"
                }
              }
            }
          },
          "impact": {
            "type": "object",
            "properties": {
              "persons_affected": {
                "type": "integer"
              },
              "blocks_changed": {
                "type": "integer"
              },
              "maintains_compliance": {
                "type": "boolean"
              },
              "estimated_effort": {
                "type": "string",
                "enum": ["LOW", "MEDIUM", "HIGH"]
              }
            }
          },
          "pros": {
            "type": "array",
            "items": {
              "type": "string"
            }
          },
          "cons": {
            "type": "array",
            "items": {
              "type": "string"
            }
          }
        }
      }
    }
  },
  "required": ["generated_at", "conflict_summary", "suggestions"]
}
```

**Example Request:**

```json
{
  "name": "suggest_resolution",
  "arguments": {
    "conflict_type": "COVERAGE_GAP",
    "affected_blocks": ["b1234567-89ab-cdef-0123-456789abcdef"],
    "constraints": {
      "must_maintain_compliance": true,
      "prefer_minimal_changes": true
    },
    "max_suggestions": 3
  }
}
```

**Example Response:**

```json
{
  "content": [
    {
      "type": "text",
      "text": "Generated 3 suggestions for resolving coverage gap. Best option: Reassign Dr. John Doe to Monday AM shift."
    },
    {
      "type": "resource",
      "resource": {
        "uri": "resolution://suggestions/rs1234567",
        "mimeType": "application/json",
        "text": JSON.stringify({
          "generated_at": "2024-12-19T14:30:00Z",
          "conflict_summary": {
            "type": "COVERAGE_GAP",
            "severity": "HIGH",
            "description": "Monday AM clinic shift has no assigned faculty member"
          },
          "suggestions": [
            {
              "id": "sug_001",
              "title": "Reassign Dr. John Doe",
              "description": "Move Dr. John Doe from admin duties to clinic coverage for this shift",
              "confidence_score": 0.92,
              "actions": [
                {
                  "action_type": "REASSIGN",
                  "block_id": "b1234567-89ab-cdef-0123-456789abcdef",
                  "to_person_id": "p2234567-89ab-cdef-0123-456789abcdef"
                }
              ],
              "impact": {
                "persons_affected": 1,
                "blocks_changed": 1,
                "maintains_compliance": true,
                "estimated_effort": "LOW"
              },
              "pros": [
                "Minimal changes required",
                "Dr. Doe is qualified and available",
                "Maintains ACGME compliance"
              ],
              "cons": [
                "Shifts admin work to another day"
              ]
            }
          ]
        })
      }
    }
  ]
}
```

---

### 5. `generate_schedule`

**Description:** Trigger schedule generation with specified constraints and parameters.

**Input Schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "academic_year": {
      "type": "string",
      "pattern": "^\\d{4}-\\d{4}$",
      "description": "Academic year for schedule (e.g., 2024-2025)"
    },
    "start_date": {
      "type": "string",
      "format": "date"
    },
    "end_date": {
      "type": "string",
      "format": "date"
    },
    "generation_mode": {
      "type": "string",
      "enum": ["FULL", "PARTIAL", "OPTIMIZATION"],
      "default": "FULL",
      "description": "FULL = generate entire schedule, PARTIAL = fill gaps, OPTIMIZATION = improve existing"
    },
    "constraints": {
      "type": "object",
      "properties": {
        "enforce_acgme_compliance": {
          "type": "boolean",
          "default": true
        },
        "target_utilization": {
          "type": "number",
          "minimum": 0,
          "maximum": 1,
          "default": 0.75,
          "description": "Target utilization rate (default 75% for resilience)"
        },
        "prioritize_fairness": {
          "type": "boolean",
          "default": true
        },
        "respect_preferences": {
          "type": "boolean",
          "default": true
        },
        "locked_assignments": {
          "type": "array",
          "items": {
            "type": "string",
            "format": "uuid"
          },
          "description": "Assignment IDs that cannot be changed"
        }
      }
    },
    "async": {
      "type": "boolean",
      "default": true,
      "description": "If true, return immediately with job ID; if false, wait for completion"
    }
  },
  "required": ["academic_year", "start_date", "end_date"]
}
```

**Output Schema (Async Mode):**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "job_id": {
      "type": "string",
      "format": "uuid"
    },
    "status": {
      "type": "string",
      "enum": ["QUEUED", "RUNNING", "COMPLETED", "FAILED"]
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "estimated_completion": {
      "type": "string",
      "format": "date-time"
    },
    "progress": {
      "type": "object",
      "properties": {
        "percent_complete": {
          "type": "integer",
          "minimum": 0,
          "maximum": 100
        },
        "current_step": {
          "type": "string"
        },
        "total_steps": {
          "type": "integer"
        }
      }
    },
    "status_url": {
      "type": "string",
      "format": "uri",
      "description": "URL to poll for job status"
    }
  },
  "required": ["job_id", "status", "created_at", "status_url"]
}
```

**Output Schema (Sync Mode - Completed):**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "schedule_id": {
      "type": "string",
      "format": "uuid"
    },
    "status": {
      "type": "string",
      "const": "COMPLETED"
    },
    "generated_at": {
      "type": "string",
      "format": "date-time"
    },
    "statistics": {
      "type": "object",
      "properties": {
        "total_assignments": {
          "type": "integer"
        },
        "total_persons": {
          "type": "integer"
        },
        "total_blocks": {
          "type": "integer"
        },
        "utilization_rate": {
          "type": "number"
        },
        "fairness_score": {
          "type": "number",
          "minimum": 0,
          "maximum": 1
        },
        "compliance_status": {
          "type": "string",
          "enum": ["COMPLIANT", "VIOLATIONS"]
        }
      }
    },
    "validation_results": {
      "$ref": "#/definitions/ValidationResults"
    },
    "generation_time_seconds": {
      "type": "number"
    }
  },
  "definitions": {
    "ValidationResults": {
      "type": "object",
      "properties": {
        "is_valid": {
          "type": "boolean"
        },
        "violations": {
          "type": "array",
          "items": {
            "type": "object"
          }
        }
      }
    }
  },
  "required": ["schedule_id", "status", "generated_at", "statistics", "validation_results"]
}
```

**Example Request:**

```json
{
  "name": "generate_schedule",
  "arguments": {
    "academic_year": "2024-2025",
    "start_date": "2024-07-01",
    "end_date": "2025-06-30",
    "generation_mode": "FULL",
    "constraints": {
      "enforce_acgme_compliance": true,
      "target_utilization": 0.75,
      "prioritize_fairness": true,
      "respect_preferences": true
    },
    "async": true
  }
}
```

**Example Response (Async):**

```json
{
  "content": [
    {
      "type": "text",
      "text": "Schedule generation job queued successfully. Use the status URL to check progress."
    },
    {
      "type": "resource",
      "resource": {
        "uri": "generation://job/gj1234567",
        "mimeType": "application/json",
        "text": JSON.stringify({
          "job_id": "gj1234567-89ab-cdef-0123-456789abcdef",
          "status": "QUEUED",
          "created_at": "2024-12-19T14:30:00Z",
          "estimated_completion": "2024-12-19T14:35:00Z",
          "progress": {
            "percent_complete": 0,
            "current_step": "Initializing",
            "total_steps": 5
          },
          "status_url": "http://localhost:8000/api/v1/schedules/generation/jobs/gj1234567"
        })
      }
    }
  ]
}
```

---

## Prompts

MCP servers can expose prompts to guide users through common workflows.

### 1. `review_schedule`

**Description:** Comprehensive schedule review workflow.

**Arguments:**

```json
{
  "schedule_id": {
    "type": "string",
    "description": "Schedule ID to review (optional, defaults to current)"
  },
  "focus_areas": {
    "type": "array",
    "items": {
      "type": "string",
      "enum": ["compliance", "fairness", "resilience", "workload"]
    },
    "description": "Areas to focus review on"
  }
}
```

**Prompt Template:**

```
Please review the schedule {schedule_id} with focus on {focus_areas}.

Steps:
1. Fetch the current schedule using schedule://current
2. Run validation using validate_schedule
3. Check resilience health using resilience://health
4. Review fairness metrics using analytics://fairness
5. Identify any critical issues or violations
6. Suggest improvements using suggest_resolution if needed

Provide a comprehensive summary including:
- Overall health status
- Critical violations (if any)
- Fairness assessment
- Resilience vulnerabilities
- Recommended actions
```

### 2. `plan_swap`

**Description:** Guided workflow for planning a schedule swap.

**Arguments:**

```json
{
  "requester_id": {
    "type": "string",
    "description": "Person requesting the swap"
  },
  "reason": {
    "type": "string",
    "description": "Reason for swap request"
  }
}
```

**Prompt Template:**

```
Help {requester_id} plan a schedule swap for the following reason: {reason}

Steps:
1. Fetch the requester's schedule using schedule://person/{requester_id}
2. Ask which specific blocks they want to swap
3. Use check_swap_feasibility to validate the proposed swap
4. If not feasible, review suggestions for compatible swap partners
5. Present options with pros/cons
6. Guide through swap submission if user confirms

Be conversational and helpful throughout the process.
```

### 3. `assess_vulnerability`

**Description:** Comprehensive vulnerability assessment workflow.

**Prompt Template:**

```
Conduct a comprehensive vulnerability assessment of the current schedule.

Steps:
1. Check resilience health using resilience://health
2. Run contingency analysis using analyze_contingency (N-1 and N-2)
3. Review workload distribution using analytics://workload
4. Identify high burnout risk personnel
5. Assess critical positions and single points of failure

Provide:
- Risk summary (overall health status)
- Critical vulnerabilities
- High-priority mitigation strategies
- Long-term recommendations

Format the response as an executive summary suitable for leadership review.
```

---

## Error Handling

### Error Response Format

All errors follow the JSON-RPC 2.0 error format:

```json
{
  "jsonrpc": "2.0",
  "id": "request_id",
  "error": {
    "code": -32000,
    "message": "Human-readable error message",
    "data": {
      "error_type": "VALIDATION_ERROR",
      "details": {},
      "timestamp": "2024-12-19T14:30:00Z",
      "request_id": "req_1234567"
    }
  }
}
```

### Error Codes

| Code | Type | Description |
|------|------|-------------|
| -32700 | Parse Error | Invalid JSON received |
| -32600 | Invalid Request | JSON-RPC format invalid |
| -32601 | Method Not Found | Tool/resource not found |
| -32602 | Invalid Params | Invalid parameters |
| -32603 | Internal Error | Server internal error |
| -32000 | Authentication Failed | Invalid or missing JWT token |
| -32001 | Authorization Failed | Insufficient permissions |
| -32002 | Resource Not Found | Schedule/person/block not found |
| -32003 | Validation Error | Input validation failed |
| -32004 | Constraint Violation | Business rule violation |
| -32005 | Generation Failed | Schedule generation error |
| -32006 | Backend Unavailable | FastAPI backend unreachable |

### Example Error Responses

**Authentication Failed:**

```json
{
  "error": {
    "code": -32000,
    "message": "Authentication failed: Invalid JWT token",
    "data": {
      "error_type": "AUTHENTICATION_ERROR",
      "details": {
        "reason": "Token expired"
      },
      "timestamp": "2024-12-19T14:30:00Z"
    }
  }
}
```

**Resource Not Found:**

```json
{
  "error": {
    "code": -32002,
    "message": "Schedule not found",
    "data": {
      "error_type": "NOT_FOUND",
      "details": {
        "resource_type": "schedule",
        "resource_id": "s1234567-89ab-cdef-0123-456789abcdef"
      },
      "timestamp": "2024-12-19T14:30:00Z"
    }
  }
}
```

**Validation Error:**

```json
{
  "error": {
    "code": -32003,
    "message": "Validation failed",
    "data": {
      "error_type": "VALIDATION_ERROR",
      "details": {
        "field": "swap_type",
        "message": "swap_type is required for ONE_TO_ONE swaps",
        "value": null
      },
      "timestamp": "2024-12-19T14:30:00Z"
    }
  }
}
```

---

## Implementation Guide

### Technology Stack

**MCP Server:**
- **Language:** Python 3.11+
- **Framework:** `mcp` Python SDK
- **Transport:** HTTP or Server-Sent Events (SSE)
- **HTTP Client:** `httpx` (async)
- **Validation:** `pydantic` v2

**Dependencies:**

```python
# pyproject.toml or requirements.txt
mcp>=0.1.0
httpx>=0.25.0
pydantic>=2.5.0
python-jose>=3.3.0  # JWT handling
python-dotenv>=1.0.0
```

### Project Structure

```
mcp-server/
├── src/
│   ├── __init__.py
│   ├── server.py              # Main MCP server entry point
│   ├── config.py              # Configuration management
│   ├── auth.py                # JWT authentication
│   ├── resources/             # Resource providers
│   │   ├── __init__.py
│   │   ├── schedule.py
│   │   ├── resilience.py
│   │   └── analytics.py
│   ├── tools/                 # Tool handlers
│   │   ├── __init__.py
│   │   ├── validate.py
│   │   ├── swap.py
│   │   ├── contingency.py
│   │   ├── resolution.py
│   │   └── generation.py
│   ├── prompts/               # Prompt templates
│   │   ├── __init__.py
│   │   └── workflows.py
│   ├── backend/               # FastAPI backend client
│   │   ├── __init__.py
│   │   └── client.py
│   └── schemas/               # Pydantic schemas
│       ├── __init__.py
│       ├── resources.py
│       └── tools.py
├── tests/
│   ├── test_resources.py
│   ├── test_tools.py
│   └── test_auth.py
├── .env.example
├── pyproject.toml
└── README.md
```

### Core Implementation

**1. Main Server (`server.py`):**

```python
"""MCP server for Residency Scheduler."""
import asyncio
from mcp.server import Server
from mcp.server.http import http_server

from .resources.schedule import ScheduleResource
from .resources.resilience import ResilienceResource
from .resources.analytics import AnalyticsResource
from .tools.validate import ValidateTool
from .tools.swap import SwapTool
from .tools.contingency import ContingencyTool
from .tools.resolution import ResolutionTool
from .tools.generation import GenerationTool
from .prompts.workflows import WorkflowPrompts
from .config import get_settings


async def main():
    """Run the MCP server."""
    settings = get_settings()

    server = Server("residency-scheduler-mcp")

    # Register resources
    schedule_resource = ScheduleResource(settings)
    resilience_resource = ResilienceResource(settings)
    analytics_resource = AnalyticsResource(settings)

    server.register_resource(schedule_resource)
    server.register_resource(resilience_resource)
    server.register_resource(analytics_resource)

    # Register tools
    validate_tool = ValidateTool(settings)
    swap_tool = SwapTool(settings)
    contingency_tool = ContingencyTool(settings)
    resolution_tool = ResolutionTool(settings)
    generation_tool = GenerationTool(settings)

    server.register_tool(validate_tool)
    server.register_tool(swap_tool)
    server.register_tool(contingency_tool)
    server.register_tool(resolution_tool)
    server.register_tool(generation_tool)

    # Register prompts
    workflow_prompts = WorkflowPrompts()
    server.register_prompts(workflow_prompts)

    # Run server with HTTP transport
    async with http_server(host="0.0.0.0", port=8080) as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
```

**2. Configuration (`config.py`):**

```python
"""Configuration management."""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # MCP Server
    mcp_server_name: str = "residency-scheduler-mcp"
    mcp_server_version: str = "1.0.0"

    # Backend API
    backend_api_url: str = "http://localhost:8000"
    backend_api_timeout: int = 30

    # JWT Authentication
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30

    # Feature flags
    enable_cache: bool = True
    cache_ttl_seconds: int = 300

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

**3. Backend Client (`backend/client.py`):**

```python
"""FastAPI backend client."""
import httpx
from typing import Any, Dict, Optional
from .config import Settings
from .auth import get_jwt_token


class BackendClient:
    """HTTP client for FastAPI backend."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = settings.backend_api_url
        self.timeout = settings.backend_api_timeout

    async def _get_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def get(
        self,
        endpoint: str,
        token: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make GET request to backend."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = await self._get_headers(token)
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()

    async def post(
        self,
        endpoint: str,
        data: Dict[str, Any],
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make POST request to backend."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = await self._get_headers(token)
            response = await client.post(
                f"{self.base_url}{endpoint}",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
```

**4. Resource Provider Example (`resources/schedule.py`):**

```python
"""Schedule resource provider."""
from mcp.server.models import Resource
from typing import List
from ..backend.client import BackendClient
from ..config import Settings


class ScheduleResource:
    """Provides schedule resources."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = BackendClient(settings)

    async def list_resources(self) -> List[Resource]:
        """List available schedule resources."""
        return [
            Resource(
                uri="schedule://current",
                name="Current Academic Year Schedule",
                description="Complete schedule for the current academic year",
                mimeType="application/json"
            ),
            Resource(
                uri="schedule://blocks",
                name="Block Definitions",
                description="All scheduling blocks (AM/PM sessions)",
                mimeType="application/json"
            )
        ]

    async def read_resource(self, uri: str, token: str) -> Dict[str, Any]:
        """Read a schedule resource."""
        if uri == "schedule://current":
            return await self.client.get("/api/v1/schedules/current", token=token)

        elif uri == "schedule://blocks":
            return await self.client.get("/api/v1/blocks", token=token)

        elif uri.startswith("schedule://person/"):
            person_id = uri.split("/")[-1]
            return await self.client.get(
                f"/api/v1/schedules/person/{person_id}",
                token=token
            )

        else:
            raise ValueError(f"Unknown resource URI: {uri}")
```

**5. Tool Handler Example (`tools/validate.py`):**

```python
"""Schedule validation tool."""
from mcp.server.models import Tool
from pydantic import BaseModel, Field
from typing import List, Optional
from ..backend.client import BackendClient
from ..config import Settings


class ValidateScheduleInput(BaseModel):
    """Input schema for validate_schedule tool."""

    schedule_id: Optional[str] = Field(
        None,
        description="ID of schedule to validate"
    )
    validation_rules: List[str] = Field(
        default=["ALL"],
        description="Rules to validate"
    )
    strict_mode: bool = Field(
        default=False,
        description="Fail on warnings"
    )


class ValidateTool:
    """Schedule validation tool handler."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = BackendClient(settings)

    def get_tool_definition(self) -> Tool:
        """Get tool definition for MCP."""
        return Tool(
            name="validate_schedule",
            description="Validate a schedule against all constraints",
            inputSchema=ValidateScheduleInput.model_json_schema()
        )

    async def execute(
        self,
        arguments: ValidateScheduleInput,
        token: str
    ) -> Dict[str, Any]:
        """Execute schedule validation."""
        response = await self.client.post(
            "/api/v1/schedules/validate",
            data=arguments.model_dump(),
            token=token
        )
        return response
```

### FastAPI Backend Endpoints

The MCP server requires these endpoints on the FastAPI backend:

```python
# backend/app/api/routes/mcp.py
"""MCP-specific API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import AsyncSession
from typing import List

from app.api.deps import get_current_user, get_db
from app.schemas.mcp import (
    CurrentScheduleResponse,
    PersonScheduleResponse,
    BlocksResponse,
    ResilienceHealthResponse,
    FairnessMetricsResponse,
    WorkloadMetricsResponse,
    ValidateScheduleRequest,
    ValidateScheduleResponse,
    CheckSwapFeasibilityRequest,
    CheckSwapFeasibilityResponse,
    AnalyzeContingencyRequest,
    AnalyzeContingencyResponse,
    SuggestResolutionRequest,
    SuggestResolutionResponse,
    GenerateScheduleRequest,
    GenerateScheduleResponse
)

router = APIRouter(prefix="/api/v1/mcp", tags=["mcp"])


@router.get("/schedules/current", response_model=CurrentScheduleResponse)
async def get_current_schedule(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get current academic year schedule."""
    # Implementation
    pass


@router.get("/schedules/person/{person_id}", response_model=PersonScheduleResponse)
async def get_person_schedule(
    person_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get schedule for specific person."""
    # Implementation
    pass


@router.get("/blocks", response_model=BlocksResponse)
async def get_blocks(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all block definitions."""
    # Implementation
    pass


@router.get("/resilience/health", response_model=ResilienceHealthResponse)
async def get_resilience_health(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get resilience framework health status."""
    # Implementation
    pass


@router.get("/analytics/fairness", response_model=FairnessMetricsResponse)
async def get_fairness_metrics(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get fairness distribution metrics."""
    # Implementation
    pass


@router.get("/analytics/workload", response_model=WorkloadMetricsResponse)
async def get_workload_metrics(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get workload metrics per person."""
    # Implementation
    pass


@router.post("/schedules/validate", response_model=ValidateScheduleResponse)
async def validate_schedule(
    request: ValidateScheduleRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Validate schedule against constraints."""
    # Implementation
    pass


@router.post("/swaps/check-feasibility", response_model=CheckSwapFeasibilityResponse)
async def check_swap_feasibility(
    request: CheckSwapFeasibilityRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Check if swap request is feasible."""
    # Implementation
    pass


@router.post("/resilience/analyze-contingency", response_model=AnalyzeContingencyResponse)
async def analyze_contingency(
    request: AnalyzeContingencyRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Perform N-1/N-2 contingency analysis."""
    # Implementation
    pass


@router.post("/conflicts/suggest-resolution", response_model=SuggestResolutionResponse)
async def suggest_resolution(
    request: SuggestResolutionRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get AI-powered conflict resolution suggestions."""
    # Implementation
    pass


@router.post("/schedules/generate", response_model=GenerateScheduleResponse)
async def generate_schedule(
    request: GenerateScheduleRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Trigger schedule generation."""
    # Implementation
    pass
```

### Client Configuration

**Claude Desktop Configuration (`claude_desktop_config.json`):**

```json
{
  "mcpServers": {
    "residency-scheduler": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "env": {
        "BACKEND_API_URL": "http://localhost:8000",
        "JWT_SECRET_KEY": "your-secret-key-here"
      }
    }
  }
}
```

---

## Security Considerations

### 1. Authentication

- **All requests** to the MCP server must authenticate via JWT
- Tokens should be short-lived (30 minutes default)
- Implement token refresh mechanism for long-running sessions

### 2. Authorization

- **Role-based access control** enforced on every resource/tool
- Resources check user permissions before returning data
- Tools validate user role before executing actions

### 3. Data Privacy

- **No PHI** exposed through MCP server (delegated to MyEvaluations)
- Person names are returned, but no SSN, DOB, or medical information
- Audit log all MCP requests for compliance

### 4. Input Validation

- **All inputs** validated using Pydantic schemas
- Prevent injection attacks (SQL, command, path traversal)
- Sanitize error messages to avoid information leakage

### 5. Rate Limiting

- Implement rate limiting on expensive operations:
  - `generate_schedule`: 1 request per 5 minutes
  - `analyze_contingency`: 10 requests per hour
  - `validate_schedule`: 30 requests per hour

### 6. Transport Security

- Use **TLS/SSL** for all backend API communication
- Consider MCP SSE transport for web-based clients
- HTTP transport for local Claude Desktop usage

---

## Testing Strategy

### Unit Tests

Test each component in isolation:

```python
# tests/test_resources.py
import pytest
from mcp_server.resources.schedule import ScheduleResource


@pytest.mark.asyncio
async def test_list_schedule_resources(settings):
    """Test listing schedule resources."""
    resource = ScheduleResource(settings)
    resources = await resource.list_resources()

    assert len(resources) >= 2
    assert any(r.uri == "schedule://current" for r in resources)
    assert any(r.uri == "schedule://blocks" for r in resources)


@pytest.mark.asyncio
async def test_read_current_schedule(settings, mock_backend_client):
    """Test reading current schedule resource."""
    resource = ScheduleResource(settings)
    resource.client = mock_backend_client

    data = await resource.read_resource("schedule://current", token="test-token")

    assert "academic_year" in data
    assert "assignments" in data
    assert data["metadata"]["compliance_status"] in ["COMPLIANT", "VIOLATIONS"]
```

### Integration Tests

Test MCP server with real FastAPI backend:

```python
# tests/test_integration.py
import pytest
from mcp.client import Client


@pytest.mark.integration
async def test_validate_schedule_tool(mcp_client, test_token):
    """Test validate_schedule tool end-to-end."""
    result = await mcp_client.call_tool(
        "validate_schedule",
        arguments={
            "validation_rules": ["80_HOUR_RULE"],
            "strict_mode": False
        },
        token=test_token
    )

    assert result["is_valid"] in [True, False]
    assert "violations" in result
    assert "summary" in result
```

### Load Tests

Test MCP server performance:

```python
# tests/test_load.py
import asyncio
import pytest


@pytest.mark.load
async def test_concurrent_resource_reads(mcp_client, test_token):
    """Test concurrent resource reads."""
    tasks = [
        mcp_client.read_resource("schedule://current", token=test_token)
        for _ in range(100)
    ]

    results = await asyncio.gather(*tasks)

    assert len(results) == 100
    assert all(r["academic_year"] == "2024-2025" for r in results)
```

---

## Future Enhancements

### Phase 2 Features

1. **Real-time Subscriptions**
   - Subscribe to schedule changes
   - Live resilience health updates
   - Notification stream for violations

2. **Advanced Analytics Resources**
   - `analytics://burnout-risk` - Predictive burnout analysis
   - `analytics://trends` - Historical trend data
   - `analytics://forecasting` - Workload forecasting

3. **Additional Tools**
   - `optimize_rotation_balance` - Balance rotation assignments
   - `generate_coverage_report` - Export coverage reports
   - `simulate_scenario` - What-if scenario modeling

4. **Batch Operations**
   - Bulk swap validation
   - Multi-person schedule queries
   - Batch conflict resolution

5. **Caching Layer**
   - Redis-backed resource caching
   - Invalidation on schedule updates
   - Configurable TTL per resource type

---

## Appendix

### A. Complete Environment Variables

```bash
# MCP Server Configuration
MCP_SERVER_NAME=residency-scheduler-mcp
MCP_SERVER_VERSION=1.0.0
MCP_SERVER_PORT=3000
MCP_SERVER_HOST=localhost
MCP_TRANSPORT=http  # or sse

# Backend API Configuration
BACKEND_API_URL=http://localhost:8000
BACKEND_API_TIMEOUT=30

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-minimum-32-characters
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Feature Flags
ENABLE_CACHE=true
CACHE_TTL_SECONDS=300

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### B. API Endpoint Summary

| Resource/Tool | Method | Endpoint |
|---------------|--------|----------|
| `schedule://current` | GET | `/api/v1/mcp/schedules/current` |
| `schedule://person/{id}` | GET | `/api/v1/mcp/schedules/person/{id}` |
| `schedule://blocks` | GET | `/api/v1/mcp/blocks` |
| `resilience://health` | GET | `/api/v1/mcp/resilience/health` |
| `analytics://fairness` | GET | `/api/v1/mcp/analytics/fairness` |
| `analytics://workload` | GET | `/api/v1/mcp/analytics/workload` |
| `validate_schedule` | POST | `/api/v1/mcp/schedules/validate` |
| `check_swap_feasibility` | POST | `/api/v1/mcp/swaps/check-feasibility` |
| `analyze_contingency` | POST | `/api/v1/mcp/resilience/analyze-contingency` |
| `suggest_resolution` | POST | `/api/v1/mcp/conflicts/suggest-resolution` |
| `generate_schedule` | POST | `/api/v1/mcp/schedules/generate` |

### C. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-12-19 | Initial specification |

---

**Document Status:** Draft
**Review Required:** Yes
**Approver:** Technical Lead, Security Officer

**Next Steps:**
1. Review specification with stakeholders
2. Create implementation tickets
3. Set up development environment
4. Begin FastAPI endpoint implementation
5. Develop MCP server core
6. Write comprehensive tests
7. Security review
8. Documentation review
9. Deployment planning
