export interface Snippet {
  id: string;
  title: string;
  content: string;
}

export interface ResourceLink {
  title: string;
  url: string;
}

export interface CompliancePage {
  slug: string;
  title: string;
  sector: string;
  targetAudiences: string[];
  heroImageUrl: string;
  regulatoryRequirements: string[];
  complianceInstructions: string[];
  snippetIds: string[];
  relatedDocuments: ResourceLink[];
}

import cmsData from './cms-data.json';

// Export the mapped structure globally
export const mockPages: CompliancePage[] = cmsData as CompliancePage[];

// Helper functions for the Wizard
export function getSectors(): string[] {
  const sectors = new Set(mockPages.map(p => p.sector));
  return Array.from(sectors).filter(Boolean).sort();
}

export function getGoalsBySector(sector: string): string[] {
  return mockPages
    .filter(p => p.sector === sector)
    .map(p => p.title)
    .sort();
}

export function getPageData(title: string): CompliancePage | null {
  return mockPages.find(p => p.title === title) || null;
}
