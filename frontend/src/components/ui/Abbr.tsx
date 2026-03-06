'use client';

import React from 'react';
import { Tooltip } from './Tooltip';

/**
 * Medical/military abbreviation glossary.
 * Used by the <Abbr> component to show definitions on hover.
 */
const GLOSSARY: Record<string, string> = {
  // Rotations & Schedule
  FMIT: 'Family Medicine Inpatient Team — the inpatient teaching service rotation',
  NF: 'Night Float — overnight on-call coverage rotation',
  PCAT: 'Primary Care Ambulatory Training — outpatient clinic sessions',
  DO: 'Day Off — scheduled non-duty day',
  HDA: 'Half-Day Assignment — a single AM or PM schedule slot',
  SM: 'Sports Medicine rotation',
  OB: 'Obstetrics rotation',
  FM: 'Family Medicine',
  IM: 'Internal Medicine',
  EM: 'Emergency Medicine',
  CV: 'Cardiovascular / Cardiology',
  LEC: 'Lecture — protected didactic time',

  // Training & Compliance
  PGY: 'Post-Graduate Year — year of residency training (PGY-1 = intern)',
  AY: 'Academic Year — training year running July 1 to June 30',
  ACGME: 'Accreditation Council for Graduate Medical Education — residency accrediting body',
  GME: 'Graduate Medical Education',

  // Military
  TDY: 'Temporary Duty — military temporary assignment away from home station',
  TAMC: 'Tripler Army Medical Center',
  MTF: 'Military Treatment Facility',

  // Technical
  'CP-SAT': 'Constraint Programming with Boolean Satisfiability — the scheduling solver engine',
  MAD: 'Mean Absolute Deviation — statistical fairness metric for call distribution',
  MFA: 'Multi-Factor Authentication — two-step login verification',
  RBAC: 'Role-Based Access Control — permission system based on user roles',
};

export interface AbbrProps {
  /** The glossary term to look up. If omitted, uses children text. */
  term?: string;
  /** Display text. Defaults to the term itself. */
  children?: React.ReactNode;
}

/**
 * Abbreviation component with hover tooltip definition.
 *
 * @example
 * <Abbr>FMIT</Abbr>                    // looks up "FMIT" in glossary
 * <Abbr term="PGY">PGY-3</Abbr>        // looks up "PGY", displays "PGY-3"
 * <Abbr term="ACGME">accreditation</Abbr>
 */
export function Abbr({ term, children }: AbbrProps) {
  const key = term || (typeof children === 'string' ? children : '');
  const definition = GLOSSARY[key];

  if (!definition) {
    return <>{children || term}</>;
  }

  return (
    <Tooltip content={definition} position="top">
      <abbr
        className="no-underline border-b border-dotted border-gray-400 cursor-help"
        title={definition}
      >
        {children || term}
      </abbr>
    </Tooltip>
  );
}

/** Export the glossary for use in other contexts (e.g., a glossary page) */
export { GLOSSARY };
