export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface AuditLog {
  id: string;
  userId: string;
  username: string;
  action: string;
  entityType?: string;
  entityId?: string;
  details: Record<string, any>;
  ipAddress: string;
  createdAt: string;
}

export interface SystemHealth {
  status: 'UP' | 'DOWN' | 'DEGRADED';
  postgres: boolean;
  neo4j: boolean;
  redis: boolean;
  qdrant: boolean;
  ollama: {
    status: 'UP' | 'DOWN';
    model: string;
  };
  translation: {
    engine: string;
    initialized: boolean;
  };
  ner: {
    initialized: boolean;
  };
  diskSpace: {
    total: number;
    free: number;
    usedPercent: number;
  };
}
