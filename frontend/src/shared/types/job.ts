export interface Job {
  id: string;
  jobType: 'consolidation' | 'profile_sync' | 'gnn_training' | 'embedding_update';
  status:
    | 'queued'
    | 'running'
    | 'completed'
    | 'failed'
    | 'cancelled'
    | 'stopped'
    | 'received'
    | 'translating'
    | 'summarizing'
    | 'profile_sync'
    | 'neo4j_sync'
    | 'qdrant_indexing'
    | 'docx_ready';
  progress: number; // 0-100
  currentStep?: string; // e.g., "Step 4/9: Classifying items"
  inputParams?: Record<string, any>;
  result?: Record<string, any>;
  errorMessage?: string;
  createdBy: string;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
}
