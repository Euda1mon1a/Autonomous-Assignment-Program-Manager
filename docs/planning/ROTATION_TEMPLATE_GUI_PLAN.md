# Rotation Template GUI Implementation Plan

> **Created:** 2025-12-30
> **Goal:** Build intuitive GUI for managing rotation templates with support for split rotations, weekly grid editing, and scheduling preferences
> **Scope:** Backend model extensions + Frontend components + Integration

---

## Executive Summary

This plan implements a comprehensive rotation template management GUI that enables program coordinators to:

1. **Visually configure weekly patterns** using a 7×2 (days × AM/PM) grid editor
2. **Define rotation types** (Regular, Split, Mirrored Split) with first-class support
3. **Allocate half-days** between FM clinic, specialty, electives, and academics
4. **Set scheduling preferences** (soft constraints) separate from ACGME rules (hard constraints)
5. **Toggle inpatient/outpatient modes** with appropriate constraint defaults

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ROTATION TEMPLATE GUI STACK                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FRONTEND (Next.js 14 + React 18 + TailwindCSS)                            │
│  ─────────────────────────────────────────────────                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │ WeeklyGridEditor│  │SplitRotationCfg │  │ PreferencePanel │            │
│  │     (7×2)       │  │ (mirror toggle) │  │ (soft constraints)│           │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘            │
│           │                    │                    │                      │
│           └────────────────────┼────────────────────┘                      │
│                                ▼                                           │
│                    ┌─────────────────────┐                                 │
│                    │RotationTemplateEditor│  (Main Container)              │
│                    └──────────┬──────────┘                                 │
│                               │                                            │
│  ─────────────────────────────┼─────────────────────────────────────────   │
│                               ▼                                            │
│  API LAYER (TanStack Query + REST)                                         │
│  ─────────────────────────────────────────────────                         │
│  useRotationTemplate() → POST/PUT /api/rotation-templates                  │
│  useWeeklyPattern()    → GET/PUT /api/rotation-templates/{id}/pattern      │
│  usePreferences()      → GET/PUT /api/rotation-templates/{id}/preferences  │
│                               │                                            │
│  ─────────────────────────────┼─────────────────────────────────────────   │
│                               ▼                                            │
│  BACKEND (FastAPI + SQLAlchemy 2.0)                                        │
│  ─────────────────────────────────────────────────                         │
│  ┌─────────────────────────────────────────────────────────────┐          │
│  │  RotationTemplate (extended)                                 │          │
│  │  ├── pattern_type: regular | split | mirrored               │          │
│  │  ├── setting_type: inpatient | outpatient                   │          │
│  │  └── paired_template_id: UUID (for splits)                  │          │
│  ├─────────────────────────────────────────────────────────────┤          │
│  │  WeeklyPattern (new)                                        │          │
│  │  ├── rotation_template_id: FK                               │          │
│  │  ├── day_of_week: 0-6                                       │          │
│  │  ├── time_of_day: AM | PM                                   │          │
│  │  └── activity_type: string                                  │          │
│  ├─────────────────────────────────────────────────────────────┤          │
│  │  RotationPreference (new)                                   │          │
│  │  ├── rotation_template_id: FK                               │          │
│  │  ├── preference_type: string                                │          │
│  │  ├── weight: low | medium | high                            │          │
│  │  └── config_json: dict                                      │          │
│  └─────────────────────────────────────────────────────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Backend Model Extensions

**Duration Estimate:** Medium complexity
**Dependencies:** None

### 1.1 New Enums

**File:** `backend/app/models/enums.py` (create or extend)

```python
from enum import Enum

class RotationPatternType(str, Enum):
    """Type of rotation scheduling pattern."""
    REGULAR = "regular"           # Full block, single activity
    SPLIT = "split"               # Two activities, fixed sequence
    MIRRORED_SPLIT = "mirrored"   # Two cohorts swap mid-block
    ALTERNATING = "alternating"   # A/B week pattern

class RotationSettingType(str, Enum):
    """Clinical setting for the rotation."""
    INPATIENT = "inpatient"       # 7-day coverage, ward-based
    OUTPATIENT = "outpatient"     # Weekday clinic, AM/PM flexible

class PreferenceWeight(str, Enum):
    """Weight for soft scheduling preferences."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    REQUIRED = "required"  # Soft but strongly enforced
```

### 1.2 Extend RotationTemplate Model

**File:** `backend/app/models/rotation_template.py`

```python
# Add new columns to existing RotationTemplate class

# Pattern configuration
pattern_type: Mapped[str] = mapped_column(
    String(20),
    default="regular",
    comment="regular, split, mirrored, alternating"
)

setting_type: Mapped[str] = mapped_column(
    String(20),
    default="outpatient",
    comment="inpatient or outpatient"
)

# For split rotations - link to paired template
paired_template_id: Mapped[Optional[UUID]] = mapped_column(
    ForeignKey("rotation_templates.id"),
    nullable=True,
    comment="For split rotations, the other half"
)

# Split configuration
split_day: Mapped[Optional[int]] = mapped_column(
    Integer,
    nullable=True,
    comment="Day in block where split occurs (1-28)"
)

is_mirror_primary: Mapped[bool] = mapped_column(
    Boolean,
    default=True,
    comment="For mirrored splits, is this the primary pattern?"
)

# Relationships
paired_template: Mapped[Optional["RotationTemplate"]] = relationship(
    "RotationTemplate",
    remote_side=[id],
    uselist=False
)

weekly_patterns: Mapped[list["WeeklyPattern"]] = relationship(
    "WeeklyPattern",
    back_populates="rotation_template",
    cascade="all, delete-orphan"
)

preferences: Mapped[list["RotationPreference"]] = relationship(
    "RotationPreference",
    back_populates="rotation_template",
    cascade="all, delete-orphan"
)
```

### 1.3 New WeeklyPattern Model

**File:** `backend/app/models/weekly_pattern.py` (new file)

```python
"""Weekly pattern slots for rotation templates."""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.rotation_template import RotationTemplate


class WeeklyPattern(Base):
    """
    Defines a single slot in a 7x2 weekly grid for a rotation template.

    Each rotation template can have up to 14 slots (7 days × 2 time periods).
    This enables visual editing of weekly patterns in the GUI.
    """
    __tablename__ = "weekly_patterns"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    rotation_template_id: Mapped[UUID] = mapped_column(
        ForeignKey("rotation_templates.id", ondelete="CASCADE"),
        index=True
    )

    # Grid position (0=Sunday, 6=Saturday)
    day_of_week: Mapped[int] = mapped_column(
        Integer,
        comment="0=Sunday, 1=Monday, ..., 6=Saturday"
    )

    # Time slot
    time_of_day: Mapped[str] = mapped_column(
        String(2),
        comment="AM or PM"
    )

    # Activity assigned to this slot
    activity_type: Mapped[str] = mapped_column(
        String(50),
        comment="fm_clinic, specialty, elective, conference, off"
    )

    # Optional: link to specific sub-rotation template
    linked_template_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("rotation_templates.id"),
        nullable=True,
        comment="Optional link to a specific activity template"
    )

    # Metadata
    is_protected: Mapped[bool] = mapped_column(
        default=False,
        comment="True for slots that cannot be changed (e.g., Wed AM conference)"
    )

    notes: Mapped[str | None] = mapped_column(String(200), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    rotation_template: Mapped["RotationTemplate"] = relationship(
        back_populates="weekly_patterns"
    )

    __table_args__ = (
        # Unique constraint: one slot per day/time per template
        {"postgresql_partition_by": None},  # Future: consider partitioning
    )

    def __repr__(self) -> str:
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        return f"<WeeklyPattern {days[self.day_of_week]} {self.time_of_day}: {self.activity_type}>"
```

### 1.4 New RotationPreference Model

**File:** `backend/app/models/rotation_preference.py` (new file)

```python
"""Soft scheduling preferences for rotation templates."""
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.rotation_template import RotationTemplate


class RotationPreference(Base):
    """
    Soft scheduling preferences (constraints) for rotation templates.

    Unlike ACGME rules which are hard constraints, preferences are
    optimization objectives that the scheduler tries to satisfy.

    Preference Types:
    - full_day_grouping: Prefer AM+PM of same activity
    - consecutive_specialty: Group specialty sessions together
    - avoid_isolated: Penalty for single orphaned half-days
    - preferred_days: Prefer specific activities on specific days
    - avoid_friday_pm: Leave Friday PM open for travel
    """
    __tablename__ = "rotation_preferences"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    rotation_template_id: Mapped[UUID] = mapped_column(
        ForeignKey("rotation_templates.id", ondelete="CASCADE"),
        index=True
    )

    # Preference identification
    preference_type: Mapped[str] = mapped_column(
        String(50),
        comment="Type of preference: full_day_grouping, consecutive_specialty, etc."
    )

    # Weight determines solver priority
    weight: Mapped[str] = mapped_column(
        String(20),
        default="medium",
        comment="low, medium, high, required"
    )

    # Flexible configuration as JSON
    config_json: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        comment="Type-specific configuration parameters"
    )

    # Is this preference currently active?
    is_active: Mapped[bool] = mapped_column(default=True)

    # Description for UI display
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    rotation_template: Mapped["RotationTemplate"] = relationship(
        back_populates="preferences"
    )

    def __repr__(self) -> str:
        return f"<RotationPreference {self.preference_type} ({self.weight})>"


# Preference type constants with default configs
PREFERENCE_DEFAULTS = {
    "full_day_grouping": {
        "description": "Prefer full days when possible (AM+PM same activity)",
        "default_weight": "medium",
        "config_schema": {}
    },
    "consecutive_specialty": {
        "description": "Group specialty sessions consecutively",
        "default_weight": "high",
        "config_schema": {"min_consecutive": 2}
    },
    "avoid_isolated": {
        "description": "Avoid single isolated half-day sessions",
        "default_weight": "low",
        "config_schema": {"penalty_multiplier": 1.5}
    },
    "preferred_days": {
        "description": "Prefer specific activities on specific days",
        "default_weight": "medium",
        "config_schema": {
            "activity": "fm_clinic",
            "days": [1, 2, 5]  # Mon, Tue, Fri
        }
    },
    "avoid_friday_pm": {
        "description": "Keep Friday PM open as travel buffer",
        "default_weight": "low",
        "config_schema": {}
    },
    "balance_weekly": {
        "description": "Distribute activities evenly across the week",
        "default_weight": "medium",
        "config_schema": {"max_same_per_day": 1}
    }
}
```

### 1.5 Alembic Migration

**File:** `backend/alembic/versions/xxxx_add_rotation_template_gui_models.py`

```python
"""Add rotation template GUI models

Revision ID: xxxx
Revises: [previous]
Create Date: 2025-12-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'xxxx_rotation_gui'
down_revision = '[previous_revision]'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extend rotation_templates table
    op.add_column('rotation_templates', sa.Column(
        'pattern_type', sa.String(20), nullable=False, server_default='regular'
    ))
    op.add_column('rotation_templates', sa.Column(
        'setting_type', sa.String(20), nullable=False, server_default='outpatient'
    ))
    op.add_column('rotation_templates', sa.Column(
        'paired_template_id', postgresql.UUID(as_uuid=True), nullable=True
    ))
    op.add_column('rotation_templates', sa.Column(
        'split_day', sa.Integer(), nullable=True
    ))
    op.add_column('rotation_templates', sa.Column(
        'is_mirror_primary', sa.Boolean(), nullable=False, server_default='true'
    ))

    # Add foreign key for paired template
    op.create_foreign_key(
        'fk_rotation_template_paired',
        'rotation_templates', 'rotation_templates',
        ['paired_template_id'], ['id'],
        ondelete='SET NULL'
    )

    # Create weekly_patterns table
    op.create_table(
        'weekly_patterns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('rotation_template_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('rotation_templates.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('time_of_day', sa.String(2), nullable=False),
        sa.Column('activity_type', sa.String(50), nullable=False),
        sa.Column('linked_template_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('rotation_templates.id'), nullable=True),
        sa.Column('is_protected', sa.Boolean(), nullable=False, default=False),
        sa.Column('notes', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('rotation_template_id', 'day_of_week', 'time_of_day',
                          name='uq_weekly_pattern_slot')
    )

    # Create rotation_preferences table
    op.create_table(
        'rotation_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('rotation_template_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('rotation_templates.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('preference_type', sa.String(50), nullable=False),
        sa.Column('weight', sa.String(20), nullable=False, default='medium'),
        sa.Column('config_json', postgresql.JSONB(), nullable=False, default={}),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('description', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )


def downgrade() -> None:
    op.drop_table('rotation_preferences')
    op.drop_table('weekly_patterns')

    op.drop_constraint('fk_rotation_template_paired', 'rotation_templates')
    op.drop_column('rotation_templates', 'is_mirror_primary')
    op.drop_column('rotation_templates', 'split_day')
    op.drop_column('rotation_templates', 'paired_template_id')
    op.drop_column('rotation_templates', 'setting_type')
    op.drop_column('rotation_templates', 'pattern_type')
```

### 1.6 Pydantic Schemas

**File:** `backend/app/schemas/rotation_template.py` (extend)

```python
# Add to existing schemas

class WeeklyPatternBase(BaseModel):
    """Base schema for weekly pattern slots."""
    day_of_week: int = Field(..., ge=0, le=6, description="0=Sunday, 6=Saturday")
    time_of_day: Literal["AM", "PM"]
    activity_type: str = Field(..., max_length=50)
    linked_template_id: UUID | None = None
    is_protected: bool = False
    notes: str | None = Field(None, max_length=200)


class WeeklyPatternCreate(WeeklyPatternBase):
    """Schema for creating a weekly pattern slot."""
    pass


class WeeklyPatternResponse(WeeklyPatternBase):
    """Schema for weekly pattern response."""
    id: UUID
    rotation_template_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WeeklyGridUpdate(BaseModel):
    """Schema for updating the entire 7x2 weekly grid at once."""
    patterns: list[WeeklyPatternCreate] = Field(
        ...,
        max_length=14,
        description="Up to 14 slots (7 days x 2 time periods)"
    )


class RotationPreferenceBase(BaseModel):
    """Base schema for rotation preferences."""
    preference_type: str = Field(..., max_length=50)
    weight: Literal["low", "medium", "high", "required"] = "medium"
    config_json: dict = Field(default_factory=dict)
    is_active: bool = True
    description: str | None = Field(None, max_length=200)


class RotationPreferenceCreate(RotationPreferenceBase):
    """Schema for creating a preference."""
    pass


class RotationPreferenceResponse(RotationPreferenceBase):
    """Schema for preference response."""
    id: UUID
    rotation_template_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RotationTemplateExtendedResponse(RotationTemplateResponse):
    """Extended response including patterns and preferences."""
    pattern_type: str = "regular"
    setting_type: str = "outpatient"
    paired_template_id: UUID | None = None
    split_day: int | None = None
    is_mirror_primary: bool = True

    weekly_patterns: list[WeeklyPatternResponse] = []
    preferences: list[RotationPreferenceResponse] = []

    # Computed fields
    half_day_summary: dict[str, int] | None = None  # {"fm_clinic": 4, "specialty": 3, ...}


class SplitRotationCreate(BaseModel):
    """Schema for creating a split or mirrored rotation pair."""
    primary_template: RotationTemplateCreate
    secondary_template: RotationTemplateCreate
    pattern_type: Literal["split", "mirrored"]
    split_day: int = Field(14, ge=1, le=27, description="Day where split occurs")
    create_mirror: bool = Field(
        False,
        description="If true, auto-generate cohort B with swapped halves"
    )
```

### 1.7 API Routes

**File:** `backend/app/api/routes/rotation_templates.py` (extend)

```python
# Add new endpoints

@router.get("/{template_id}/patterns", response_model=list[WeeklyPatternResponse])
async def get_weekly_patterns(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[WeeklyPatternResponse]:
    """Get all weekly pattern slots for a rotation template."""
    ...


@router.put("/{template_id}/patterns", response_model=list[WeeklyPatternResponse])
async def update_weekly_grid(
    template_id: UUID,
    grid: WeeklyGridUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[WeeklyPatternResponse]:
    """
    Update the entire 7x2 weekly grid for a rotation template.

    This replaces all existing patterns with the provided ones.
    Validates that protected slots (like Wed AM conference) are preserved.
    """
    ...


@router.get("/{template_id}/preferences", response_model=list[RotationPreferenceResponse])
async def get_preferences(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[RotationPreferenceResponse]:
    """Get all scheduling preferences for a rotation template."""
    ...


@router.put("/{template_id}/preferences", response_model=list[RotationPreferenceResponse])
async def update_preferences(
    template_id: UUID,
    preferences: list[RotationPreferenceCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[RotationPreferenceResponse]:
    """Update scheduling preferences for a rotation template."""
    ...


@router.post("/split", response_model=dict)
async def create_split_rotation(
    split_config: SplitRotationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Create a split or mirrored rotation pair.

    For mirrored rotations with create_mirror=True, automatically
    generates Cohort B template with swapped first/second half.

    Returns:
        {
            "primary": RotationTemplateExtendedResponse,
            "secondary": RotationTemplateExtendedResponse,
            "cohort_b_primary": RotationTemplateExtendedResponse | None,
            "cohort_b_secondary": RotationTemplateExtendedResponse | None
        }
    """
    ...


@router.get("/{template_id}/preview")
async def preview_rotation(
    template_id: UUID,
    weeks: int = Query(4, ge=1, le=8),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Generate a preview of how this rotation would look over N weeks.

    Returns a visual grid representation without saving anything.
    """
    ...
```

---

## Phase 2: Weekly Grid Editor Component

**Duration Estimate:** Medium-High complexity
**Dependencies:** Phase 1 (backend models)

### 2.1 Component Structure

```
frontend/src/features/rotation-templates/
├── components/
│   ├── RotationTemplateEditor.tsx      # Main container/orchestrator
│   ├── WeeklyGridEditor.tsx            # 7x2 visual grid (core)
│   ├── GridCell.tsx                    # Individual AM/PM cell
│   ├── ActivityPicker.tsx              # Dropdown/popover for activity selection
│   ├── HalfDaySummary.tsx              # Real-time half-day counts
│   ├── SplitRotationConfig.tsx         # Split/mirrored configuration
│   ├── PreferencePanel.tsx             # Soft constraint toggles
│   ├── RotationTypeSelector.tsx        # Regular/Split/Mirrored tabs
│   ├── SettingTypeToggle.tsx           # Inpatient/Outpatient switch
│   ├── RotationPreview.tsx             # Multi-week preview
│   └── index.ts                        # Barrel exports
├── hooks/
│   ├── useRotationTemplate.ts          # CRUD operations
│   ├── useWeeklyGrid.ts                # Grid state management
│   ├── usePreferences.ts               # Preference management
│   └── useSplitRotation.ts             # Split rotation logic
├── types.ts                            # TypeScript interfaces
├── constants.ts                        # Activity types, colors, defaults
├── utils/
│   ├── gridHelpers.ts                  # Grid manipulation utilities
│   ├── validationHelpers.ts            # Pattern validation
│   └── previewGenerator.ts             # Generate preview data
└── api.ts                              # API client functions
```

### 2.2 Core Types

**File:** `frontend/src/features/rotation-templates/types.ts`

```typescript
// Rotation pattern types
export type RotationPatternType = 'regular' | 'split' | 'mirrored' | 'alternating';
export type RotationSettingType = 'inpatient' | 'outpatient';
export type TimeOfDay = 'AM' | 'PM';
export type DayOfWeek = 0 | 1 | 2 | 3 | 4 | 5 | 6;
export type PreferenceWeight = 'low' | 'medium' | 'high' | 'required';

// Activity types for the grid
export type ActivityType =
  | 'fm_clinic'
  | 'specialty'
  | 'elective'
  | 'conference'
  | 'inpatient'
  | 'call'
  | 'off'
  | 'procedure';

// Single cell in the 7x2 grid
export interface GridCell {
  id?: string;
  dayOfWeek: DayOfWeek;
  timeOfDay: TimeOfDay;
  activityType: ActivityType | null;
  linkedTemplateId?: string;
  isProtected: boolean;
  notes?: string;
}

// Complete weekly grid (14 cells max)
export interface WeeklyGrid {
  cells: GridCell[];
  templateId: string;
}

// Preference configuration
export interface RotationPreference {
  id?: string;
  preferenceType: string;
  weight: PreferenceWeight;
  configJson: Record<string, unknown>;
  isActive: boolean;
  description?: string;
}

// Extended rotation template with GUI fields
export interface RotationTemplateExtended {
  id: string;
  name: string;
  abbreviation?: string;
  activityType: string;
  patternType: RotationPatternType;
  settingType: RotationSettingType;
  pairedTemplateId?: string;
  splitDay?: number;
  isMirrorPrimary: boolean;

  // Nested data
  weeklyPatterns: GridCell[];
  preferences: RotationPreference[];
  halfDayRequirement?: HalfDayRequirement;

  // Display
  fontColor?: string;
  backgroundColor?: string;

  // Constraints
  leaveEligible: boolean;
  maxResidents?: number;
  supervisionRequired: boolean;
  maxSupervisionRatio?: number;
}

// Half-day allocation summary
export interface HalfDaySummary {
  fmClinic: number;
  specialty: number;
  elective: number;
  conference: number;
  off: number;
  total: number;
}

// Split rotation configuration
export interface SplitRotationConfig {
  patternType: 'split' | 'mirrored';
  primaryActivity: ActivityType;
  secondaryActivity: ActivityType;
  splitDay: number;
  createMirror: boolean;
}

// Grid editor state
export interface GridEditorState {
  grid: WeeklyGrid;
  selectedCell: { day: DayOfWeek; time: TimeOfDay } | null;
  isDragging: boolean;
  dragActivity: ActivityType | null;
  hasUnsavedChanges: boolean;
}
```

### 2.3 WeeklyGridEditor Component

**File:** `frontend/src/features/rotation-templates/components/WeeklyGridEditor.tsx`

```tsx
'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { GridCell } from './GridCell';
import { ActivityPicker } from './ActivityPicker';
import { HalfDaySummary } from './HalfDaySummary';
import { useWeeklyGrid } from '../hooks/useWeeklyGrid';
import type {
  GridCell as GridCellType,
  ActivityType,
  DayOfWeek,
  TimeOfDay,
  RotationSettingType
} from '../types';
import { DAYS_OF_WEEK, ACTIVITY_COLORS } from '../constants';

interface WeeklyGridEditorProps {
  templateId: string;
  initialPatterns: GridCellType[];
  settingType: RotationSettingType;
  onSave: (patterns: GridCellType[]) => Promise<void>;
  onChange?: (patterns: GridCellType[]) => void;
  readOnly?: boolean;
}

export function WeeklyGridEditor({
  templateId,
  initialPatterns,
  settingType,
  onSave,
  onChange,
  readOnly = false
}: WeeklyGridEditorProps) {
  const {
    grid,
    selectedCell,
    setSelectedCell,
    updateCell,
    fillRange,
    clearCell,
    getHalfDaySummary,
    hasChanges,
    resetGrid,
    isDragging,
    startDrag,
    endDrag
  } = useWeeklyGrid(initialPatterns);

  const [showActivityPicker, setShowActivityPicker] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Compute summary
  const summary = useMemo(() => getHalfDaySummary(), [grid]);

  // Check if weekends should be shown (inpatient = yes, outpatient = no)
  const showWeekends = settingType === 'inpatient';

  // Days to display
  const visibleDays = showWeekends
    ? DAYS_OF_WEEK
    : DAYS_OF_WEEK.filter(d => d.value !== 0 && d.value !== 6);

  // Handle cell click
  const handleCellClick = useCallback((day: DayOfWeek, time: TimeOfDay) => {
    if (readOnly) return;

    const cell = grid.find(c => c.dayOfWeek === day && c.timeOfDay === time);
    if (cell?.isProtected) return;

    setSelectedCell({ day, time });
    setShowActivityPicker(true);
  }, [grid, readOnly, setSelectedCell]);

  // Handle activity selection
  const handleActivitySelect = useCallback((activity: ActivityType | null) => {
    if (!selectedCell) return;

    updateCell(selectedCell.day, selectedCell.time, activity);
    setShowActivityPicker(false);
    setSelectedCell(null);

    onChange?.(grid);
  }, [selectedCell, updateCell, onChange, grid, setSelectedCell]);

  // Handle drag operations
  const handleDragStart = useCallback((activity: ActivityType) => {
    if (readOnly) return;
    startDrag(activity);
  }, [readOnly, startDrag]);

  const handleDragOver = useCallback((day: DayOfWeek, time: TimeOfDay) => {
    if (!isDragging || readOnly) return;
    // Visual feedback handled in GridCell
  }, [isDragging, readOnly]);

  const handleDrop = useCallback((day: DayOfWeek, time: TimeOfDay) => {
    if (!isDragging || readOnly) return;
    endDrag(day, time);
    onChange?.(grid);
  }, [isDragging, readOnly, endDrag, onChange, grid]);

  // Handle save
  const handleSave = useCallback(async () => {
    setIsSaving(true);
    try {
      await onSave(grid);
    } finally {
      setIsSaving(false);
    }
  }, [grid, onSave]);

  return (
    <div className="space-y-4">
      {/* Grid Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">Weekly Pattern</h3>
        <div className="flex items-center gap-2">
          {hasChanges && !readOnly && (
            <>
              <button
                onClick={resetGrid}
                className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900"
              >
                Reset
              </button>
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="px-4 py-1.5 text-sm bg-blue-600 text-white rounded-md
                         hover:bg-blue-700 disabled:opacity-50"
              >
                {isSaving ? 'Saving...' : 'Save Changes'}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Weekly Grid */}
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse">
          <thead>
            <tr>
              <th className="w-16 p-2 text-xs font-medium text-gray-500 text-left">
                Time
              </th>
              {visibleDays.map(day => (
                <th
                  key={day.value}
                  className="p-2 text-xs font-medium text-gray-500 text-center min-w-[80px]"
                >
                  {day.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* AM Row */}
            <tr>
              <td className="p-2 text-xs font-medium text-gray-500">AM</td>
              {visibleDays.map(day => {
                const cell = grid.find(
                  c => c.dayOfWeek === day.value && c.timeOfDay === 'AM'
                );
                return (
                  <td key={`${day.value}-AM`} className="p-1">
                    <GridCell
                      cell={cell}
                      day={day.value as DayOfWeek}
                      time="AM"
                      onClick={handleCellClick}
                      onDragOver={handleDragOver}
                      onDrop={handleDrop}
                      isSelected={
                        selectedCell?.day === day.value &&
                        selectedCell?.time === 'AM'
                      }
                      isDragTarget={isDragging}
                      readOnly={readOnly}
                    />
                  </td>
                );
              })}
            </tr>
            {/* PM Row */}
            <tr>
              <td className="p-2 text-xs font-medium text-gray-500">PM</td>
              {visibleDays.map(day => {
                const cell = grid.find(
                  c => c.dayOfWeek === day.value && c.timeOfDay === 'PM'
                );
                return (
                  <td key={`${day.value}-PM`} className="p-1">
                    <GridCell
                      cell={cell}
                      day={day.value as DayOfWeek}
                      time="PM"
                      onClick={handleCellClick}
                      onDragOver={handleDragOver}
                      onDrop={handleDrop}
                      isSelected={
                        selectedCell?.day === day.value &&
                        selectedCell?.time === 'PM'
                      }
                      isDragTarget={isDragging}
                      readOnly={readOnly}
                    />
                  </td>
                );
              })}
            </tr>
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-2 text-xs">
        {Object.entries(ACTIVITY_COLORS).map(([activity, colors]) => (
          <div
            key={activity}
            className={`px-2 py-1 rounded ${colors.bg} ${colors.text}`}
          >
            {activity.replace('_', ' ')}
          </div>
        ))}
      </div>

      {/* Half-Day Summary */}
      <HalfDaySummary summary={summary} />

      {/* Activity Picker Modal/Popover */}
      {showActivityPicker && selectedCell && (
        <ActivityPicker
          selectedActivity={
            grid.find(
              c => c.dayOfWeek === selectedCell.day &&
                   c.timeOfDay === selectedCell.time
            )?.activityType ?? null
          }
          onSelect={handleActivitySelect}
          onClose={() => {
            setShowActivityPicker(false);
            setSelectedCell(null);
          }}
          position={selectedCell}
        />
      )}
    </div>
  );
}
```

### 2.4 Grid Cell Component

**File:** `frontend/src/features/rotation-templates/components/GridCell.tsx`

```tsx
'use client';

import React from 'react';
import { LockClosedIcon } from '@heroicons/react/20/solid';
import type { GridCell as GridCellType, DayOfWeek, TimeOfDay, ActivityType } from '../types';
import { ACTIVITY_COLORS, ACTIVITY_ABBREVIATIONS } from '../constants';
import { cn } from '@/lib/utils';

interface GridCellProps {
  cell: GridCellType | undefined;
  day: DayOfWeek;
  time: TimeOfDay;
  onClick: (day: DayOfWeek, time: TimeOfDay) => void;
  onDragOver: (day: DayOfWeek, time: TimeOfDay) => void;
  onDrop: (day: DayOfWeek, time: TimeOfDay) => void;
  isSelected: boolean;
  isDragTarget: boolean;
  readOnly: boolean;
}

export function GridCell({
  cell,
  day,
  time,
  onClick,
  onDragOver,
  onDrop,
  isSelected,
  isDragTarget,
  readOnly
}: GridCellProps) {
  const activity = cell?.activityType;
  const isProtected = cell?.isProtected ?? false;
  const isEmpty = !activity;

  const colors = activity ? ACTIVITY_COLORS[activity] : null;
  const abbreviation = activity ? ACTIVITY_ABBREVIATIONS[activity] : null;

  const handleClick = () => {
    if (!readOnly && !isProtected) {
      onClick(day, time);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!readOnly && !isProtected) {
      onDragOver(day, time);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (!readOnly && !isProtected) {
      onDrop(day, time);
    }
  };

  return (
    <div
      className={cn(
        'relative h-12 min-w-[60px] rounded-md border-2 transition-all',
        'flex items-center justify-center cursor-pointer',
        // Base states
        isEmpty && 'bg-gray-50 border-gray-200 border-dashed',
        !isEmpty && colors && `${colors.bg} ${colors.border} border-solid`,
        // Interactive states
        !readOnly && !isProtected && 'hover:shadow-md hover:scale-105',
        isSelected && 'ring-2 ring-blue-500 ring-offset-1',
        isDragTarget && !isProtected && 'ring-2 ring-green-400 ring-offset-1',
        // Protected/readonly states
        isProtected && 'cursor-not-allowed opacity-75',
        readOnly && 'cursor-default'
      )}
      onClick={handleClick}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      title={cell?.notes ?? activity ?? 'Empty slot'}
    >
      {/* Activity Abbreviation */}
      {abbreviation && (
        <span className={cn('text-sm font-semibold', colors?.text)}>
          {abbreviation}
        </span>
      )}

      {/* Empty state */}
      {isEmpty && !isProtected && (
        <span className="text-gray-400 text-xs">+</span>
      )}

      {/* Protected indicator */}
      {isProtected && (
        <div className="absolute top-0.5 right-0.5">
          <LockClosedIcon className="h-3 w-3 text-gray-400" />
        </div>
      )}

      {/* Notes indicator */}
      {cell?.notes && (
        <div className="absolute bottom-0.5 right-0.5 h-1.5 w-1.5
                       rounded-full bg-yellow-400" />
      )}
    </div>
  );
}
```

### 2.5 Constants

**File:** `frontend/src/features/rotation-templates/constants.ts`

```typescript
import type { ActivityType, DayOfWeek } from './types';

// Days of week with labels
export const DAYS_OF_WEEK = [
  { value: 0, label: 'Sun', fullLabel: 'Sunday' },
  { value: 1, label: 'Mon', fullLabel: 'Monday' },
  { value: 2, label: 'Tue', fullLabel: 'Tuesday' },
  { value: 3, label: 'Wed', fullLabel: 'Wednesday' },
  { value: 4, label: 'Thu', fullLabel: 'Thursday' },
  { value: 5, label: 'Fri', fullLabel: 'Friday' },
  { value: 6, label: 'Sat', fullLabel: 'Saturday' },
] as const;

// Activity colors (Tailwind classes)
export const ACTIVITY_COLORS: Record<ActivityType, {
  bg: string;
  text: string;
  border: string;
}> = {
  fm_clinic: {
    bg: 'bg-blue-100',
    text: 'text-blue-800',
    border: 'border-blue-300'
  },
  specialty: {
    bg: 'bg-purple-100',
    text: 'text-purple-800',
    border: 'border-purple-300'
  },
  elective: {
    bg: 'bg-green-100',
    text: 'text-green-800',
    border: 'border-green-300'
  },
  conference: {
    bg: 'bg-yellow-100',
    text: 'text-yellow-800',
    border: 'border-yellow-300'
  },
  inpatient: {
    bg: 'bg-red-100',
    text: 'text-red-800',
    border: 'border-red-300'
  },
  call: {
    bg: 'bg-orange-100',
    text: 'text-orange-800',
    border: 'border-orange-300'
  },
  procedure: {
    bg: 'bg-teal-100',
    text: 'text-teal-800',
    border: 'border-teal-300'
  },
  off: {
    bg: 'bg-gray-100',
    text: 'text-gray-600',
    border: 'border-gray-300'
  }
};

// Activity abbreviations for grid display
export const ACTIVITY_ABBREVIATIONS: Record<ActivityType, string> = {
  fm_clinic: 'FM',
  specialty: 'Spec',
  elective: 'Elec',
  conference: 'Conf',
  inpatient: 'Inp',
  call: 'Call',
  procedure: 'Proc',
  off: 'Off'
};

// Activity full names
export const ACTIVITY_LABELS: Record<ActivityType, string> = {
  fm_clinic: 'FM Clinic',
  specialty: 'Specialty',
  elective: 'Elective',
  conference: 'Conference',
  inpatient: 'Inpatient',
  call: 'Call',
  procedure: 'Procedure',
  off: 'Off'
};

// Protected slots (cannot be modified)
export const PROTECTED_SLOTS: Array<{ day: DayOfWeek; time: 'AM' | 'PM'; activity: ActivityType }> = [
  { day: 3, time: 'AM', activity: 'conference' }, // Wednesday AM = Conference
];

// Default preferences
export const DEFAULT_PREFERENCES = [
  {
    preferenceType: 'full_day_grouping',
    weight: 'medium' as const,
    description: 'Prefer full days when possible (AM+PM same activity)',
    isActive: true,
    configJson: {}
  },
  {
    preferenceType: 'consecutive_specialty',
    weight: 'high' as const,
    description: 'Group specialty sessions consecutively',
    isActive: true,
    configJson: { min_consecutive: 2 }
  },
  {
    preferenceType: 'avoid_friday_pm',
    weight: 'low' as const,
    description: 'Keep Friday PM open as travel buffer',
    isActive: false,
    configJson: {}
  }
];

// Half-day allocation limits
export const HALF_DAY_LIMITS = {
  total: 10, // Per block (2 weeks)
  fm_clinic: { min: 2, max: 6 },
  specialty: { min: 2, max: 5 },
  elective: { min: 0, max: 4 },
  conference: { min: 1, max: 1 }, // Fixed
};
```

---

## Phase 3: Split Rotation Configuration

**Duration Estimate:** Medium complexity
**Dependencies:** Phase 1, Phase 2 (grid editor)

### 3.1 SplitRotationConfig Component

**File:** `frontend/src/features/rotation-templates/components/SplitRotationConfig.tsx`

```tsx
'use client';

import React, { useState, useCallback } from 'react';
import { WeeklyGridEditor } from './WeeklyGridEditor';
import { ActivityPicker } from './ActivityPicker';
import type {
  SplitRotationConfig as SplitConfig,
  ActivityType,
  GridCell
} from '../types';
import { cn } from '@/lib/utils';

interface SplitRotationConfigProps {
  config: SplitConfig;
  onConfigChange: (config: SplitConfig) => void;
  primaryPatterns: GridCell[];
  secondaryPatterns: GridCell[];
  onPrimaryPatternsChange: (patterns: GridCell[]) => void;
  onSecondaryPatternsChange: (patterns: GridCell[]) => void;
}

export function SplitRotationConfig({
  config,
  onConfigChange,
  primaryPatterns,
  secondaryPatterns,
  onPrimaryPatternsChange,
  onSecondaryPatternsChange
}: SplitRotationConfigProps) {
  const [activeHalf, setActiveHalf] = useState<'first' | 'second'>('first');

  const handlePatternTypeChange = useCallback((type: 'split' | 'mirrored') => {
    onConfigChange({ ...config, patternType: type });
  }, [config, onConfigChange]);

  const handleSplitDayChange = useCallback((day: number) => {
    onConfigChange({ ...config, splitDay: day });
  }, [config, onConfigChange]);

  const handleMirrorToggle = useCallback((enabled: boolean) => {
    onConfigChange({ ...config, createMirror: enabled });
  }, [config, onConfigChange]);

  return (
    <div className="space-y-6">
      {/* Pattern Type Selector */}
      <div className="flex gap-4">
        <button
          onClick={() => handlePatternTypeChange('split')}
          className={cn(
            'flex-1 p-4 rounded-lg border-2 text-left transition-all',
            config.patternType === 'split'
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 hover:border-gray-300'
          )}
        >
          <div className="font-medium">Split Rotation</div>
          <div className="text-sm text-gray-600 mt-1">
            Two activities in sequence (e.g., NF then Elective)
          </div>
        </button>

        <button
          onClick={() => handlePatternTypeChange('mirrored')}
          className={cn(
            'flex-1 p-4 rounded-lg border-2 text-left transition-all',
            config.patternType === 'mirrored'
              ? 'border-purple-500 bg-purple-50'
              : 'border-gray-200 hover:border-gray-300'
          )}
        >
          <div className="font-medium">Mirrored Split</div>
          <div className="text-sm text-gray-600 mt-1">
            Two cohorts swap mid-block (A: NF→Elec, B: Elec→NF)
          </div>
        </button>
      </div>

      {/* Split Day Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Split Point (Day in Block)
        </label>
        <div className="flex items-center gap-4">
          <input
            type="range"
            min={7}
            max={21}
            value={config.splitDay}
            onChange={(e) => handleSplitDayChange(Number(e.target.value))}
            className="flex-1"
          />
          <span className="text-sm font-medium w-20">
            Day {config.splitDay}
          </span>
        </div>
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>Week 1</span>
          <span>Mid-block (Day 14)</span>
          <span>Week 3</span>
        </div>
      </div>

      {/* Visual Preview */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="text-sm font-medium text-gray-700 mb-3">Preview</div>
        <div className="space-y-2">
          {/* Cohort A */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium w-16">Cohort A:</span>
            <div className="flex-1 h-8 flex rounded overflow-hidden">
              <div
                className="bg-blue-200 flex items-center justify-center text-xs font-medium"
                style={{ width: `${(config.splitDay / 28) * 100}%` }}
              >
                {config.primaryActivity?.replace('_', ' ') || 'First Half'}
              </div>
              <div
                className="bg-green-200 flex items-center justify-center text-xs font-medium"
                style={{ width: `${((28 - config.splitDay) / 28) * 100}%` }}
              >
                {config.secondaryActivity?.replace('_', ' ') || 'Second Half'}
              </div>
            </div>
          </div>

          {/* Cohort B (if mirrored) */}
          {config.patternType === 'mirrored' && (
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium w-16">Cohort B:</span>
              <div className="flex-1 h-8 flex rounded overflow-hidden">
                <div
                  className="bg-green-200 flex items-center justify-center text-xs font-medium"
                  style={{ width: `${(config.splitDay / 28) * 100}%` }}
                >
                  {config.secondaryActivity?.replace('_', ' ') || 'Second Half'}
                </div>
                <div
                  className="bg-blue-200 flex items-center justify-center text-xs font-medium"
                  style={{ width: `${((28 - config.splitDay) / 28) * 100}%` }}
                >
                  {config.primaryActivity?.replace('_', ' ') || 'First Half'}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Mirror Toggle (for mirrored type) */}
      {config.patternType === 'mirrored' && (
        <label className="flex items-center gap-3 p-3 bg-purple-50 rounded-lg">
          <input
            type="checkbox"
            checked={config.createMirror}
            onChange={(e) => handleMirrorToggle(e.target.checked)}
            className="h-4 w-4 text-purple-600 rounded"
          />
          <div>
            <div className="text-sm font-medium text-gray-900">
              Auto-generate Cohort B
            </div>
            <div className="text-xs text-gray-600">
              Automatically create the mirrored template pair
            </div>
          </div>
        </label>
      )}

      {/* Half Editors */}
      <div className="border rounded-lg overflow-hidden">
        {/* Tab Headers */}
        <div className="flex border-b">
          <button
            onClick={() => setActiveHalf('first')}
            className={cn(
              'flex-1 px-4 py-2 text-sm font-medium',
              activeHalf === 'first'
                ? 'bg-white border-b-2 border-blue-500 text-blue-600'
                : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
            )}
          >
            First Half (Days 1-{config.splitDay})
          </button>
          <button
            onClick={() => setActiveHalf('second')}
            className={cn(
              'flex-1 px-4 py-2 text-sm font-medium',
              activeHalf === 'second'
                ? 'bg-white border-b-2 border-green-500 text-green-600'
                : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
            )}
          >
            Second Half (Days {config.splitDay + 1}-28)
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-4">
          {activeHalf === 'first' ? (
            <WeeklyGridEditor
              templateId="first-half"
              initialPatterns={primaryPatterns}
              settingType="outpatient"
              onSave={async (patterns) => onPrimaryPatternsChange(patterns)}
              onChange={onPrimaryPatternsChange}
            />
          ) : (
            <WeeklyGridEditor
              templateId="second-half"
              initialPatterns={secondaryPatterns}
              settingType="outpatient"
              onSave={async (patterns) => onSecondaryPatternsChange(patterns)}
              onChange={onSecondaryPatternsChange}
            />
          )}
        </div>
      </div>
    </div>
  );
}
```

---

## Phase 4: Preference System

**Duration Estimate:** Medium complexity
**Dependencies:** Phase 1 (backend models)

### 4.1 PreferencePanel Component

**File:** `frontend/src/features/rotation-templates/components/PreferencePanel.tsx`

```tsx
'use client';

import React, { useCallback } from 'react';
import { Switch } from '@headlessui/react';
import type { RotationPreference, PreferenceWeight } from '../types';
import { cn } from '@/lib/utils';

interface PreferencePanelProps {
  preferences: RotationPreference[];
  onPreferencesChange: (preferences: RotationPreference[]) => void;
  readOnly?: boolean;
}

const WEIGHT_LABELS: Record<PreferenceWeight, { label: string; color: string }> = {
  low: { label: 'Low', color: 'bg-gray-200 text-gray-700' },
  medium: { label: 'Medium', color: 'bg-blue-200 text-blue-700' },
  high: { label: 'High', color: 'bg-orange-200 text-orange-700' },
  required: { label: 'Required', color: 'bg-red-200 text-red-700' }
};

const PREFERENCE_ICONS: Record<string, string> = {
  full_day_grouping: '📅',
  consecutive_specialty: '🔗',
  avoid_isolated: '🚫',
  preferred_days: '⭐',
  avoid_friday_pm: '✈️',
  balance_weekly: '⚖️'
};

export function PreferencePanel({
  preferences,
  onPreferencesChange,
  readOnly = false
}: PreferencePanelProps) {

  const togglePreference = useCallback((index: number) => {
    if (readOnly) return;
    const updated = [...preferences];
    updated[index] = { ...updated[index], isActive: !updated[index].isActive };
    onPreferencesChange(updated);
  }, [preferences, onPreferencesChange, readOnly]);

  const updateWeight = useCallback((index: number, weight: PreferenceWeight) => {
    if (readOnly) return;
    const updated = [...preferences];
    updated[index] = { ...updated[index], weight };
    onPreferencesChange(updated);
  }, [preferences, onPreferencesChange, readOnly]);

  const updateConfig = useCallback((index: number, key: string, value: unknown) => {
    if (readOnly) return;
    const updated = [...preferences];
    updated[index] = {
      ...updated[index],
      configJson: { ...updated[index].configJson, [key]: value }
    };
    onPreferencesChange(updated);
  }, [preferences, onPreferencesChange, readOnly]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">
          Scheduling Preferences
        </h3>
        <span className="text-xs text-gray-500">
          Soft constraints (optimizer will try to satisfy)
        </span>
      </div>

      {/* Preference List */}
      <div className="space-y-3">
        {preferences.map((pref, index) => (
          <div
            key={pref.preferenceType}
            className={cn(
              'p-4 rounded-lg border transition-all',
              pref.isActive
                ? 'bg-white border-gray-200 shadow-sm'
                : 'bg-gray-50 border-gray-100'
            )}
          >
            <div className="flex items-start gap-3">
              {/* Toggle */}
              <Switch
                checked={pref.isActive}
                onChange={() => togglePreference(index)}
                disabled={readOnly}
                className={cn(
                  'relative inline-flex h-5 w-9 items-center rounded-full transition-colors',
                  pref.isActive ? 'bg-blue-600' : 'bg-gray-300',
                  readOnly && 'opacity-50 cursor-not-allowed'
                )}
              >
                <span
                  className={cn(
                    'inline-block h-3 w-3 transform rounded-full bg-white transition-transform',
                    pref.isActive ? 'translate-x-5' : 'translate-x-1'
                  )}
                />
              </Switch>

              {/* Icon & Content */}
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-lg">
                    {PREFERENCE_ICONS[pref.preferenceType] || '⚙️'}
                  </span>
                  <span className={cn(
                    'font-medium',
                    pref.isActive ? 'text-gray-900' : 'text-gray-500'
                  )}>
                    {pref.preferenceType.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </span>
                </div>
                <p className={cn(
                  'text-sm mt-1',
                  pref.isActive ? 'text-gray-600' : 'text-gray-400'
                )}>
                  {pref.description}
                </p>

                {/* Weight Selector (when active) */}
                {pref.isActive && (
                  <div className="flex items-center gap-2 mt-3">
                    <span className="text-xs text-gray-500">Weight:</span>
                    <div className="flex gap-1">
                      {(['low', 'medium', 'high'] as PreferenceWeight[]).map(w => (
                        <button
                          key={w}
                          onClick={() => updateWeight(index, w)}
                          disabled={readOnly}
                          className={cn(
                            'px-2 py-0.5 text-xs rounded transition-all',
                            pref.weight === w
                              ? WEIGHT_LABELS[w].color
                              : 'bg-gray-100 text-gray-500 hover:bg-gray-200',
                            readOnly && 'cursor-not-allowed'
                          )}
                        >
                          {WEIGHT_LABELS[w].label}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Type-specific config */}
                {pref.isActive && pref.preferenceType === 'consecutive_specialty' && (
                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-xs text-gray-500">Min consecutive:</span>
                    <select
                      value={pref.configJson.min_consecutive as number ?? 2}
                      onChange={(e) => updateConfig(index, 'min_consecutive', Number(e.target.value))}
                      disabled={readOnly}
                      className="text-xs border rounded px-2 py-1"
                    >
                      <option value={2}>2 half-days</option>
                      <option value={3}>3 half-days</option>
                      <option value={4}>4 half-days (full day)</option>
                    </select>
                  </div>
                )}

                {pref.isActive && pref.preferenceType === 'preferred_days' && (
                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-xs text-gray-500">Preferred days:</span>
                    <div className="flex gap-1">
                      {['M', 'T', 'W', 'Th', 'F'].map((d, i) => {
                        const days = (pref.configJson.days as number[]) ?? [];
                        const isSelected = days.includes(i + 1);
                        return (
                          <button
                            key={d}
                            onClick={() => {
                              const newDays = isSelected
                                ? days.filter(x => x !== i + 1)
                                : [...days, i + 1];
                              updateConfig(index, 'days', newDays);
                            }}
                            disabled={readOnly}
                            className={cn(
                              'w-6 h-6 text-xs rounded transition-all',
                              isSelected
                                ? 'bg-blue-500 text-white'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            )}
                          >
                            {d}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* ACGME Hard Constraints Notice */}
      <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
        <div className="flex items-start gap-2">
          <span className="text-amber-500">⚠️</span>
          <div>
            <div className="text-sm font-medium text-amber-800">
              ACGME Hard Constraints (Cannot Override)
            </div>
            <ul className="text-xs text-amber-700 mt-1 space-y-0.5">
              <li>• Protected conference time: Wednesday 7-12</li>
              <li>• Max consecutive work: 6 days</li>
              <li>• 1-in-7 day off requirement</li>
              <li>• 80-hour weekly limit (averaged over 4 weeks)</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## Phase 5: Main Editor & Integration

**Duration Estimate:** Medium complexity
**Dependencies:** Phases 1-4

### 5.1 RotationTemplateEditor (Main Container)

**File:** `frontend/src/features/rotation-templates/components/RotationTemplateEditor.tsx`

```tsx
'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Tab } from '@headlessui/react';
import { WeeklyGridEditor } from './WeeklyGridEditor';
import { SplitRotationConfig } from './SplitRotationConfig';
import { PreferencePanel } from './PreferencePanel';
import { RotationTypeSelector } from './RotationTypeSelector';
import { SettingTypeToggle } from './SettingTypeToggle';
import { HalfDayAllocationSlider } from './HalfDayAllocationSlider';
import { RotationPreview } from './RotationPreview';
import { useRotationTemplate } from '../hooks/useRotationTemplate';
import { useWeeklyGrid } from '../hooks/useWeeklyGrid';
import type {
  RotationTemplateExtended,
  RotationPatternType,
  RotationSettingType,
  GridCell,
  RotationPreference,
  SplitRotationConfig as SplitConfig
} from '../types';
import { DEFAULT_PREFERENCES } from '../constants';
import { cn } from '@/lib/utils';

interface RotationTemplateEditorProps {
  templateId?: string; // undefined = create new
  onSave?: (template: RotationTemplateExtended) => void;
  onCancel?: () => void;
}

export function RotationTemplateEditor({
  templateId,
  onSave,
  onCancel
}: RotationTemplateEditorProps) {
  const router = useRouter();
  const isNew = !templateId;

  // Fetch existing template if editing
  const {
    template,
    isLoading,
    updateTemplate,
    createTemplate,
    isUpdating
  } = useRotationTemplate(templateId);

  // Local state
  const [name, setName] = useState('');
  const [abbreviation, setAbbreviation] = useState('');
  const [patternType, setPatternType] = useState<RotationPatternType>('regular');
  const [settingType, setSettingType] = useState<RotationSettingType>('outpatient');
  const [weeklyPatterns, setWeeklyPatterns] = useState<GridCell[]>([]);
  const [preferences, setPreferences] = useState<RotationPreference[]>(DEFAULT_PREFERENCES);
  const [splitConfig, setSplitConfig] = useState<SplitConfig>({
    patternType: 'split',
    primaryActivity: 'fm_clinic',
    secondaryActivity: 'elective',
    splitDay: 14,
    createMirror: false
  });
  const [activeTab, setActiveTab] = useState(0);

  // Populate from loaded template
  useEffect(() => {
    if (template) {
      setName(template.name);
      setAbbreviation(template.abbreviation ?? '');
      setPatternType(template.patternType);
      setSettingType(template.settingType);
      setWeeklyPatterns(template.weeklyPatterns);
      setPreferences(template.preferences.length > 0
        ? template.preferences
        : DEFAULT_PREFERENCES);
    }
  }, [template]);

  // Handle save
  const handleSave = useCallback(async () => {
    const templateData: Partial<RotationTemplateExtended> = {
      name,
      abbreviation,
      patternType,
      settingType,
      weeklyPatterns,
      preferences: preferences.filter(p => p.isActive)
    };

    if (isNew) {
      const created = await createTemplate(templateData);
      onSave?.(created);
    } else {
      const updated = await updateTemplate(templateData);
      onSave?.(updated);
    }
  }, [
    name, abbreviation, patternType, settingType,
    weeklyPatterns, preferences, isNew, createTemplate, updateTemplate, onSave
  ]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-2 border-blue-500
                       border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">
          {isNew ? 'Create Rotation Template' : 'Edit Rotation Template'}
        </h1>
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-600 hover:text-gray-900"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isUpdating || !name}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg
                     hover:bg-blue-700 disabled:opacity-50"
          >
            {isUpdating ? 'Saving...' : 'Save Template'}
          </button>
        </div>
      </div>

      {/* Basic Info */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Template Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., PGY-1 Outpatient Block"
            className="w-full px-3 py-2 border rounded-lg focus:ring-2
                     focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Abbreviation
          </label>
          <input
            type="text"
            value={abbreviation}
            onChange={(e) => setAbbreviation(e.target.value)}
            placeholder="e.g., PGY1-OUT"
            maxLength={10}
            className="w-full px-3 py-2 border rounded-lg focus:ring-2
                     focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Rotation Type & Setting */}
      <div className="grid grid-cols-2 gap-6">
        <RotationTypeSelector
          value={patternType}
          onChange={setPatternType}
        />
        <SettingTypeToggle
          value={settingType}
          onChange={setSettingType}
        />
      </div>

      {/* Main Configuration Tabs */}
      <Tab.Group selectedIndex={activeTab} onChange={setActiveTab}>
        <Tab.List className="flex border-b">
          <Tab className={({ selected }) => cn(
            'px-4 py-2 text-sm font-medium border-b-2 -mb-px',
            selected
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          )}>
            Weekly Pattern
          </Tab>
          {patternType !== 'regular' && (
            <Tab className={({ selected }) => cn(
              'px-4 py-2 text-sm font-medium border-b-2 -mb-px',
              selected
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            )}>
              Split Configuration
            </Tab>
          )}
          <Tab className={({ selected }) => cn(
            'px-4 py-2 text-sm font-medium border-b-2 -mb-px',
            selected
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          )}>
            Half-Day Allocation
          </Tab>
          <Tab className={({ selected }) => cn(
            'px-4 py-2 text-sm font-medium border-b-2 -mb-px',
            selected
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          )}>
            Preferences
          </Tab>
          <Tab className={({ selected }) => cn(
            'px-4 py-2 text-sm font-medium border-b-2 -mb-px',
            selected
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          )}>
            Preview
          </Tab>
        </Tab.List>

        <Tab.Panels className="mt-6">
          {/* Weekly Pattern Tab */}
          <Tab.Panel>
            <WeeklyGridEditor
              templateId={templateId ?? 'new'}
              initialPatterns={weeklyPatterns}
              settingType={settingType}
              onSave={async (patterns) => setWeeklyPatterns(patterns)}
              onChange={setWeeklyPatterns}
            />
          </Tab.Panel>

          {/* Split Configuration Tab */}
          {patternType !== 'regular' && (
            <Tab.Panel>
              <SplitRotationConfig
                config={splitConfig}
                onConfigChange={setSplitConfig}
                primaryPatterns={weeklyPatterns}
                secondaryPatterns={[]}
                onPrimaryPatternsChange={setWeeklyPatterns}
                onSecondaryPatternsChange={() => {}}
              />
            </Tab.Panel>
          )}

          {/* Half-Day Allocation Tab */}
          <Tab.Panel>
            <HalfDayAllocationSlider
              patterns={weeklyPatterns}
              onPatternsChange={setWeeklyPatterns}
            />
          </Tab.Panel>

          {/* Preferences Tab */}
          <Tab.Panel>
            <PreferencePanel
              preferences={preferences}
              onPreferencesChange={setPreferences}
            />
          </Tab.Panel>

          {/* Preview Tab */}
          <Tab.Panel>
            <RotationPreview
              template={{
                name,
                patternType,
                settingType,
                weeklyPatterns,
                preferences
              } as RotationTemplateExtended}
              weeks={4}
            />
          </Tab.Panel>
        </Tab.Panels>
      </Tab.Group>
    </div>
  );
}
```

---

## Phase 6: Testing & Quality Assurance

**Duration Estimate:** Medium complexity
**Dependencies:** All previous phases

### 6.1 Backend Tests

**File:** `backend/tests/test_rotation_template_gui.py`

```python
"""Tests for rotation template GUI features."""
import pytest
from uuid import uuid4

from app.models.rotation_template import RotationTemplate
from app.models.weekly_pattern import WeeklyPattern
from app.models.rotation_preference import RotationPreference
from app.schemas.rotation_template import (
    WeeklyGridUpdate,
    WeeklyPatternCreate,
    RotationPreferenceCreate,
    SplitRotationCreate
)


class TestWeeklyPatterns:
    """Test weekly pattern CRUD operations."""

    async def test_create_weekly_pattern(self, db, rotation_template):
        """Test creating a single weekly pattern slot."""
        pattern = WeeklyPattern(
            rotation_template_id=rotation_template.id,
            day_of_week=1,  # Monday
            time_of_day="AM",
            activity_type="fm_clinic"
        )
        db.add(pattern)
        await db.commit()

        assert pattern.id is not None
        assert pattern.day_of_week == 1
        assert pattern.time_of_day == "AM"

    async def test_update_weekly_grid(self, client, auth_headers, rotation_template):
        """Test updating entire 7x2 grid."""
        patterns = [
            {"day_of_week": 1, "time_of_day": "AM", "activity_type": "fm_clinic"},
            {"day_of_week": 1, "time_of_day": "PM", "activity_type": "specialty"},
            {"day_of_week": 2, "time_of_day": "AM", "activity_type": "fm_clinic"},
            {"day_of_week": 3, "time_of_day": "AM", "activity_type": "conference", "is_protected": True},
        ]

        response = await client.put(
            f"/api/rotation_templates/{rotation_template.id}/patterns",
            json={"patterns": patterns},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4

        # Verify protected slot
        conf_slot = next(p for p in data if p["day_of_week"] == 3)
        assert conf_slot["is_protected"] is True

    async def test_unique_slot_constraint(self, db, rotation_template):
        """Test that duplicate day/time slots raise error."""
        pattern1 = WeeklyPattern(
            rotation_template_id=rotation_template.id,
            day_of_week=1,
            time_of_day="AM",
            activity_type="fm_clinic"
        )
        pattern2 = WeeklyPattern(
            rotation_template_id=rotation_template.id,
            day_of_week=1,
            time_of_day="AM",
            activity_type="specialty"  # Same slot, different activity
        )

        db.add(pattern1)
        await db.commit()

        db.add(pattern2)
        with pytest.raises(Exception):  # IntegrityError
            await db.commit()


class TestRotationPreferences:
    """Test rotation preference management."""

    async def test_create_preference(self, db, rotation_template):
        """Test creating a scheduling preference."""
        pref = RotationPreference(
            rotation_template_id=rotation_template.id,
            preference_type="full_day_grouping",
            weight="medium",
            config_json={},
            description="Prefer full days when possible"
        )
        db.add(pref)
        await db.commit()

        assert pref.id is not None
        assert pref.is_active is True

    async def test_update_preference_weight(self, client, auth_headers, rotation_template):
        """Test updating preference weight."""
        prefs = [
            {
                "preference_type": "consecutive_specialty",
                "weight": "high",
                "config_json": {"min_consecutive": 3},
                "is_active": True
            }
        ]

        response = await client.put(
            f"/api/rotation_templates/{rotation_template.id}/preferences",
            json=prefs,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data[0]["weight"] == "high"
        assert data[0]["config_json"]["min_consecutive"] == 3


class TestSplitRotations:
    """Test split and mirrored rotation creation."""

    async def test_create_split_rotation(self, client, auth_headers):
        """Test creating a split rotation pair."""
        split_config = {
            "primary_template": {
                "name": "Night Float",
                "rotation_type": "inpatient",
                "abbreviation": "NF"
            },
            "secondary_template": {
                "name": "Elective",
                "rotation_type": "elective",
                "abbreviation": "ELEC"
            },
            "pattern_type": "split",
            "split_day": 14,
            "create_mirror": False
        }

        response = await client.post(
            "/api/rotation_templates/split",
            json=split_config,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert "primary" in data
        assert "secondary" in data
        assert data["primary"]["pattern_type"] == "split"
        assert data["primary"]["paired_template_id"] == data["secondary"]["id"]

    async def test_create_mirrored_rotation(self, client, auth_headers):
        """Test creating mirrored rotation with auto cohort B."""
        split_config = {
            "primary_template": {
                "name": "Night Float",
                "rotation_type": "inpatient"
            },
            "secondary_template": {
                "name": "Elective",
                "rotation_type": "elective"
            },
            "pattern_type": "mirrored",
            "split_day": 14,
            "create_mirror": True
        }

        response = await client.post(
            "/api/rotation_templates/split",
            json=split_config,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()

        # Should have 4 templates: A-primary, A-secondary, B-primary, B-secondary
        assert "cohort_b_primary" in data
        assert "cohort_b_secondary" in data
        assert data["cohort_b_primary"]["is_mirror_primary"] is False


class TestRotationPreview:
    """Test rotation preview generation."""

    async def test_generate_preview(self, client, auth_headers, rotation_template):
        """Test generating multi-week preview."""
        response = await client.get(
            f"/api/rotation_templates/{rotation_template.id}/preview?weeks=4",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "grid" in data
        assert len(data["grid"]) == 4  # 4 weeks
        assert len(data["grid"][0]) == 7  # 7 days per week
```

### 6.2 Frontend Tests

**File:** `frontend/src/features/rotation-templates/__tests__/WeeklyGridEditor.test.tsx`

```tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { WeeklyGridEditor } from '../components/WeeklyGridEditor';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } }
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('WeeklyGridEditor', () => {
  const mockOnSave = jest.fn();
  const mockOnChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders 7x2 grid for inpatient setting', () => {
    render(
      <WeeklyGridEditor
        templateId="test"
        initialPatterns={[]}
        settingType="inpatient"
        onSave={mockOnSave}
      />,
      { wrapper }
    );

    // Should show all 7 days including weekends
    expect(screen.getByText('Sun')).toBeInTheDocument();
    expect(screen.getByText('Sat')).toBeInTheDocument();
    expect(screen.getByText('Mon')).toBeInTheDocument();
  });

  it('hides weekends for outpatient setting', () => {
    render(
      <WeeklyGridEditor
        templateId="test"
        initialPatterns={[]}
        settingType="outpatient"
        onSave={mockOnSave}
      />,
      { wrapper }
    );

    // Should not show weekends
    expect(screen.queryByText('Sun')).not.toBeInTheDocument();
    expect(screen.queryByText('Sat')).not.toBeInTheDocument();
    expect(screen.getByText('Mon')).toBeInTheDocument();
  });

  it('opens activity picker on cell click', async () => {
    render(
      <WeeklyGridEditor
        templateId="test"
        initialPatterns={[]}
        settingType="outpatient"
        onSave={mockOnSave}
      />,
      { wrapper }
    );

    // Click an empty cell
    const cells = screen.getAllByText('+');
    fireEvent.click(cells[0]);

    // Activity picker should appear
    await waitFor(() => {
      expect(screen.getByText('FM Clinic')).toBeInTheDocument();
    });
  });

  it('updates cell on activity selection', async () => {
    render(
      <WeeklyGridEditor
        templateId="test"
        initialPatterns={[]}
        settingType="outpatient"
        onSave={mockOnSave}
        onChange={mockOnChange}
      />,
      { wrapper }
    );

    // Click cell and select activity
    const cells = screen.getAllByText('+');
    fireEvent.click(cells[0]);

    await waitFor(() => {
      const fmOption = screen.getByText('FM Clinic');
      fireEvent.click(fmOption);
    });

    // Should show abbreviation
    await waitFor(() => {
      expect(screen.getByText('FM')).toBeInTheDocument();
    });

    expect(mockOnChange).toHaveBeenCalled();
  });

  it('shows protected indicator for conference slot', () => {
    const patterns = [
      {
        dayOfWeek: 3, // Wednesday
        timeOfDay: 'AM' as const,
        activityType: 'conference' as const,
        isProtected: true
      }
    ];

    render(
      <WeeklyGridEditor
        templateId="test"
        initialPatterns={patterns}
        settingType="outpatient"
        onSave={mockOnSave}
      />,
      { wrapper }
    );

    // Should show lock icon (protected)
    expect(screen.getByTitle('Protected conference time')).toBeInTheDocument();
  });

  it('displays half-day summary', () => {
    const patterns = [
      { dayOfWeek: 1, timeOfDay: 'AM' as const, activityType: 'fm_clinic' as const, isProtected: false },
      { dayOfWeek: 1, timeOfDay: 'PM' as const, activityType: 'fm_clinic' as const, isProtected: false },
      { dayOfWeek: 2, timeOfDay: 'AM' as const, activityType: 'specialty' as const, isProtected: false },
    ];

    render(
      <WeeklyGridEditor
        templateId="test"
        initialPatterns={patterns}
        settingType="outpatient"
        onSave={mockOnSave}
      />,
      { wrapper }
    );

    // Summary should show counts
    expect(screen.getByText(/FM.*2/)).toBeInTheDocument();
    expect(screen.getByText(/Specialty.*1/)).toBeInTheDocument();
  });
});
```

---

## Implementation Roadmap

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        IMPLEMENTATION ROADMAP                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHASE 1: Backend Models                                                    │
│  ═══════════════════════                                                    │
│  □ Create RotationPatternType enum                                          │
│  □ Extend RotationTemplate model                                            │
│  □ Create WeeklyPattern model                                               │
│  □ Create RotationPreference model                                          │
│  □ Write Alembic migration                                                  │
│  □ Add Pydantic schemas                                                     │
│  □ Add API routes                                                           │
│  □ Write backend tests                                                      │
│                                                                             │
│  PHASE 2: Weekly Grid Editor                                                │
│  ═══════════════════════════                                                │
│  □ Create types.ts with interfaces                                          │
│  □ Create constants.ts with colors/labels                                   │
│  □ Build GridCell component                                                 │
│  □ Build ActivityPicker component                                           │
│  □ Build WeeklyGridEditor component                                         │
│  □ Build HalfDaySummary component                                           │
│  □ Add useWeeklyGrid hook                                                   │
│  □ Write frontend tests                                                     │
│                                                                             │
│  PHASE 3: Split Rotation Config                                             │
│  ═════════════════════════════                                              │
│  □ Build RotationTypeSelector component                                     │
│  □ Build SplitRotationConfig component                                      │
│  □ Add split preview visualization                                          │
│  □ Add useSplitRotation hook                                                │
│  □ Integrate with backend split endpoint                                    │
│                                                                             │
│  PHASE 4: Preference System                                                 │
│  ═════════════════════════                                                  │
│  □ Build PreferencePanel component                                          │
│  □ Add weight selector UI                                                   │
│  □ Add type-specific config UIs                                             │
│  □ Add usePreferences hook                                                  │
│  □ Integrate with solver (future)                                           │
│                                                                             │
│  PHASE 5: Main Editor Integration                                           │
│  ═══════════════════════════════                                            │
│  □ Build RotationTemplateEditor container                                   │
│  □ Build SettingTypeToggle component                                        │
│  □ Build HalfDayAllocationSlider component                                  │
│  □ Build RotationPreview component                                          │
│  □ Add page route /templates/rotation/[id]                                  │
│  □ Add to navigation                                                        │
│                                                                             │
│  PHASE 6: Testing & Polish                                                  │
│  ═════════════════════════                                                  │
│  □ Full E2E test suite                                                      │
│  □ Accessibility audit                                                      │
│  □ Mobile responsiveness                                                    │
│  □ Documentation                                                            │
│  □ User acceptance testing                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## File Summary

### Backend Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `backend/app/models/enums.py` | Create | RotationPatternType, RotationSettingType, PreferenceWeight |
| `backend/app/models/rotation_template.py` | Modify | Add pattern_type, setting_type, paired_template_id fields |
| `backend/app/models/weekly_pattern.py` | Create | WeeklyPattern model for 7x2 grid |
| `backend/app/models/rotation_preference.py` | Create | RotationPreference model |
| `backend/app/schemas/rotation_template.py` | Modify | Add schemas for patterns, preferences, split config |
| `backend/app/api/routes/rotation_templates.py` | Modify | Add pattern, preference, split, preview endpoints |
| `backend/alembic/versions/xxx_rotation_gui.py` | Create | Migration for new tables and columns |
| `backend/tests/test_rotation_template_gui.py` | Create | Test suite for new features |

### Frontend Files to Create

| File | Description |
|------|-------------|
| `frontend/src/features/rotation-templates/types.ts` | TypeScript interfaces |
| `frontend/src/features/rotation-templates/constants.ts` | Colors, labels, defaults |
| `frontend/src/features/rotation-templates/api.ts` | API client functions |
| `frontend/src/features/rotation-templates/hooks/useRotationTemplate.ts` | Template CRUD hook |
| `frontend/src/features/rotation-templates/hooks/useWeeklyGrid.ts` | Grid state management |
| `frontend/src/features/rotation-templates/hooks/usePreferences.ts` | Preference management |
| `frontend/src/features/rotation-templates/components/WeeklyGridEditor.tsx` | 7x2 grid editor |
| `frontend/src/features/rotation-templates/components/GridCell.tsx` | Individual cell |
| `frontend/src/features/rotation-templates/components/ActivityPicker.tsx` | Activity selector |
| `frontend/src/features/rotation-templates/components/HalfDaySummary.tsx` | Allocation summary |
| `frontend/src/features/rotation-templates/components/SplitRotationConfig.tsx` | Split config UI |
| `frontend/src/features/rotation-templates/components/PreferencePanel.tsx` | Preferences UI |
| `frontend/src/features/rotation-templates/components/RotationTypeSelector.tsx` | Type selector |
| `frontend/src/features/rotation-templates/components/SettingTypeToggle.tsx` | Inpatient/outpatient |
| `frontend/src/features/rotation-templates/components/RotationPreview.tsx` | Multi-week preview |
| `frontend/src/features/rotation-templates/components/RotationTemplateEditor.tsx` | Main container |
| `frontend/src/features/rotation-templates/__tests__/*.test.tsx` | Test files |

---

## Next Steps

Ready to begin implementation? I recommend starting with:

1. **Phase 1** - Backend models (foundation for everything else)
2. **Phase 2** - Weekly grid editor (highest-value UX component)

Want me to start implementing Phase 1 (backend models and migration)?
