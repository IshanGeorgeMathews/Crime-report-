export interface PersonProfile {
  id: string;
  ppId: string; // e.g. "040/PKD"
  name: string;
  parentage?: string;
  address?: string;
  policeStation?: string;
  dob?: string;
  placeOfBirth?: string;
  qualification?: string;
  religion?: string;
  identificationMarks?: string;
  mobile?: string;
  activityType?: string; // e.g. "Extremism", "NDPS"
  reasonForInclusion?: string;
  organizationName?: string;
  organizationRemarks?: string;
  briefHistory?: string;
  reviewStatus: 'approved' | 'pending' | 'rejected';
  neo4jNodeId?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ProfileRelation {
  id: string;
  profileId: string;
  name: string;
  relationType: string; // e.g. "Father", "Spouse"
  address?: string;
  mobile?: string;
}

export interface ProfileCase {
  id: string;
  profileId: string;
  firNumber: string; // e.g. "1599/14"
  underSections?: string;
  policeStation?: string;
  caseBrief?: string;
  caseStatus: string; // e.g. "Under Investigation"
  coAccused?: string;
}

export interface ProfileActivity {
  id: string;
  profileId: string;
  activityName: string;
  activityDesc: string;
  activityDate: string;
  reportId?: string;
  createdAt: string;
}

export interface Report {
  id: string;
  reportDate: string;
  refNumber: string;
  eventCount: number;
  forecastCount: number;
  socialMediaCount: number;
  notNeededCount: number;
  createdBy: string;
  createdAt: string;
}

export interface ReportItem {
  id: string;
  reportId: string;
  category: string;
  summaryText: string;
  rawText: string;
  sourceFilename: string;
  districtTag: string;
  translationEngine?: string;
}
