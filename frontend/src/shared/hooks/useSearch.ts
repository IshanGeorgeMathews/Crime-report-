import { useMutation } from '@tanstack/react-query';
import { api } from '../api/api';
import type { ApiResponse } from '../types/api';

export interface SearchResult {
  entityType: 'profile' | 'report_item' | 'case' | 'organization' | 'crime';
  title: string;
  score?: number; // Present only in semantic search
  snippet: string;
  id: string;
}

export interface ChatCitation {
  entityType: 'profile' | 'report_item' | 'case' | 'organization' | 'crime';
  title: string;
  snippet: string;
  id: string;
  score?: number;
}

export interface ChatResponse {
  answer: string;
  citations: ChatCitation[];
  graphSummary?: string;
  usedFallback: boolean;
  model?: string | null;
}

export const useSearch = () => {
  // Semantic search mutation (Qdrant vector similarity check)
  const semanticMutation = useMutation<
    ApiResponse<SearchResult[]>,
    Error,
    { query: string; collections?: string[]; limit?: number; filters?: Record<string, any> }
  >({
    mutationFn: async (params) => {
      const response = await api.post<ApiResponse<SearchResult[]>>(
        '/search/semantic',
        params
      );
      return response.data;
    },
  });

  // Structured SQL database search mutation
  const structuredMutation = useMutation<
    ApiResponse<SearchResult[]>,
    Error,
    { query: string; filters?: Record<string, any> }
  >({
    mutationFn: async (params) => {
      const response = await api.post<ApiResponse<SearchResult[]>>(
        '/search/structured',
        params
      );
      return response.data;
    },
  });

  const chatMutation = useMutation<
    ApiResponse<ChatResponse>,
    Error,
    { query: string; limit?: number; graphDepth?: number }
  >({
    mutationFn: async (params) => {
      const response = await api.post<ApiResponse<ChatResponse>>(
        '/search/chat',
        params
      );
      return response.data;
    },
  });

  return {
    searchSemantic: semanticMutation.mutateAsync,
    isSearchingSemantic: semanticMutation.isPending,
    semanticError: semanticMutation.error,
    semanticResults: semanticMutation.data?.data || [],

    searchStructured: structuredMutation.mutateAsync,
    isSearchingStructured: structuredMutation.isPending,
    structuredError: structuredMutation.error,
    structuredResults: structuredMutation.data?.data || [],

    chatSearch: chatMutation.mutateAsync,
    isSearchingChat: chatMutation.isPending,
    chatError: chatMutation.error,
    chatResponse: chatMutation.data?.data || null,
  };
};
