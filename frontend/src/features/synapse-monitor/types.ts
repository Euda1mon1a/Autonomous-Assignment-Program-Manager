export type AcuityLevel = "High" | "Med" | "Low" | "Critical";
export type RiskLevel = "Low" | "Med" | "High" | "Critical";

export interface Personnel {
  name: string;
  debt: number; // Sleep debt in hours
  reserve: number; // Cognitive reserve percentage (0-100)
  acuity: AcuityLevel;
  risk: RiskLevel;
  unit?: string; // Optional unit assignment
}

export interface SynapseMonitorProps {
  personnel?: Personnel[];
  onPersonSelect?: (person: Personnel) => void;
  className?: string;
}
