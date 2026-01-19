import { Personnel } from "./types";

/**
 * Fallback personnel data for use when the API is unavailable.
 * In production, data should come from useSynapseData() hook which
 * fetches from the /resilience/health API endpoint.
 *
 * @deprecated Use useSynapseData() hook for real data
 */
export const FALLBACK_PERSONNEL: Personnel[] = [
  {
    name: "MAJ Montgomery",
    debt: 14.2,
    reserve: 82,
    acuity: "High",
    risk: "Low",
  },
  {
    name: "LTC Sterling",
    debt: 28.5,
    reserve: 45,
    acuity: "Critical",
    risk: "High",
  },
  { name: "MAJ Vance", debt: 8.0, reserve: 91, acuity: "Low", risk: "Low" },
  {
    name: "MAJ Rhodes",
    debt: 32.1,
    reserve: 22,
    acuity: "High",
    risk: "Critical",
  },
  { name: "CPT Miller", debt: 18.4, reserve: 68, acuity: "Med", risk: "Med" },
  { name: "MAJ Chen", debt: 4.5, reserve: 95, acuity: "Low", risk: "Low" },
  { name: "LT Svelv", debt: 21.2, reserve: 55, acuity: "Med", risk: "Med" },
  {
    name: "WO1 Thrace",
    debt: 41.0,
    reserve: 12,
    acuity: "Critical",
    risk: "Critical",
  },
];
