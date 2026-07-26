/**
 * The single vocabulary for user-profile fields.
 *
 * Why this file exists
 * ────────────────────
 * OnboardingModal and the /profile page each carried their own hardcoded option
 * lists, and they disagreed. Onboarding wrote "Salaried Employee", "Mutual funds /
 * SIPs" and an Indian city from a dropdown; /profile wrote "salary", "conservative"
 * and a free-text city hinted "e.g. San Francisco". Both wrote to the SAME database
 * columns, so whichever screen the user touched last determined what the analyze
 * prompt received — and the two produced mutually unintelligible values.
 *
 * Everything that offers profile choices imports from here. Adding an option in one
 * place now changes every surface.
 *
 * The India-first vocabulary won: this product's thesis is Indian professionals, the
 * SOPs are written around Indian markets, and "Mutual funds / SIPs" is the phrasing
 * the target user actually recognises.
 */

export const INCOME_OPTIONS = [
  "Salaried Employee",
  "Business Owner",
  "Investor / Trader",
  "Student",
] as const;

export const SECTOR_OPTIONS = [
  "IT / Software",
  "Banking & Finance",
  "Real Estate",
  "Manufacturing",
  "Healthcare",
  "Education",
  "None / Not sure",
] as const;

export const INVESTMENT_OPTIONS = [
  "Mostly FDs & savings",
  "Mutual funds / SIPs",
  "Direct stocks",
  "Crypto",
  "No investments",
] as const;

export const CITY_OPTIONS = [
  "Mumbai",
  "Delhi",
  "Bengaluru",
  "Hyderabad",
  "Chennai",
  "Pune",
  "Ahmedabad",
  "Kolkata",
  "Other",
] as const;

/**
 * `sector_exposure` is a single TEXT column in SQLite but a multi-select in the UI.
 * These two helpers are the only place that conversion is allowed to happen, so the
 * separator can never drift between screens.
 */
export function sectorsToString(sectors: string[]): string {
  return sectors.join(", ");
}

export function sectorsToArray(raw: string | null | undefined): string[] {
  if (!raw) return [];
  return raw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}
