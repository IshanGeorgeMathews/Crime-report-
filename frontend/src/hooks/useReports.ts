import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { ApiResponse } from '../types/api';
import type { Report, ReportItem } from '../types/profile';

// Re-map import from profile structure to verify type naming
type ReportDetailData = Report & { items: ReportItem[] };

export const useReports = (reportId?: string) => {
  // Query report history list
  const listQuery = useQuery<ApiResponse<Report[]>, Error>({
    queryKey: ['reports'],
    queryFn: async () => {
      const response = await api.get<ApiResponse<Report[]>>('/reports');
      return response.data;
    },
  });

  // Query single report details with text sections
  const detailQuery = useQuery<ApiResponse<ReportDetailData>, Error>({
    queryKey: ['report', reportId],
    queryFn: async () => {
      const response = await api.get<ApiResponse<ReportDetailData>>(`/reports/${reportId}`);
      return response.data;
    },
    enabled: !!reportId,
  });

  // Downloader trigger function (streams bytes directly from FastAPI backend)
  const downloadDocx = async (id: string, type: 'daily' | 'less-priority' | 'pp' | 'uo') => {
    let url = '';
    let defaultFilename = '';

    if (type === 'daily') {
      url = `/reports/${id}/download`;
      defaultFilename = `IS_Daily_Report_${id}.docx`;
    } else if (type === 'less-priority') {
      url = `/reports/${id}/less-priority/download`;
      defaultFilename = `Less_Priority_Report_${id}.docx`;
    } else if (type === 'pp') {
      url = `/profiles/${id}/docx`;
      defaultFilename = `PP_Profile_${id}.docx`;
    } else if (type === 'uo') {
      url = `/profiles/${id}/generate-uo`;
      defaultFilename = `UO_Note_${id}.docx`;
    }

    try {
      const response = await api.get(url, {
        responseType: 'blob', // Critical for streaming files
      });
      
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', defaultFilename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
      return true;
    } catch (e) {
      console.error('Failed to download document:', e);
      throw e;
    }
  };

  return {
    reports: listQuery.data?.data || [],
    isFetchingReports: listQuery.isFetching,
    reportsError: listQuery.error,

    reportDetail: detailQuery.data?.data,
    isFetchingDetail: detailQuery.isFetching,
    detailError: detailQuery.error,
    
    downloadDocx,
  };
};
export type { Report, ReportDetailData };
