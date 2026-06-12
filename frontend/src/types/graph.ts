export interface GraphNode {
  id: string;
  label: string; // Name, title, or date
  type: 'individual' | 'crime' | 'record' | 'organization' | 'case';
  properties: {
    pp_id?: string;
    police_station?: string;
    activity_type?: string;
    text?: string;
    district?: string;
    date?: string;
    anomaly?: string;
    [key: string]: any;
  };
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: 'ASSOCIATED_WITH' | 'MENTIONED_IN' | 'CO_OCCURRED_WITH' | 'MEMBER_OF' | 'ACCUSED_IN' | 'REPORTED_IN';
  weight: number;
  rawWeight?: number;
  firstSeen?: string;
  lastSeen?: string;
  occurrenceCount?: number;
  decayHalfLifeDays?: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GnnRecommendation {
  name: string;
  similarity: number;
  hasEdge: boolean;
  relationshipHint?: string;
}
