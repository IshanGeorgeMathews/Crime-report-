import axios from 'axios';
import { useAuthStore } from '../stores/authStore';

// Retrieve backend URL from environment or fallback to relative URL
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Attach Auth Token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle Token Expiry
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Auto logout on 401 unauthorized
      useAuthStore.getState().logout();
    }
    return Promise.reject(error);
  }
);

// MOCK ADAPTER FOR LOCAL UI-ONLY VALIDATION
const VITE_USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

if (VITE_USE_MOCK) {
  console.warn('[KPIP API] Operating in MOCK mode. Network requests are mocked locally.');
  
  // Set up request interception for mocks
  api.interceptors.request.use(async (config) => {
    const url = config.url || '';
    const method = (config.method || 'get').toLowerCase();
    
    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 500));
    
    // Helper to return mock response
    const mockResponse = (data: any, status = 200) => {
      return {
        data: { success: status >= 200 && status < 300, data },
        status,
        statusText: 'OK',
        headers: {},
        config,
      } as any;
    };

    // --- Mock Auth Routes ---
    if (url.includes('/auth/login') && method === 'post') {
      const { username } = JSON.parse(config.data || '{}');
      const user = {
        id: 'usr-1',
        username,
        fullName: username === 'admin' ? 'System Administrator' : 'SI Pradeep Kumar',
        role: username === 'admin' ? 'admin' : username === 'supervisor' ? 'supervisor' : 'analyst',
        district: 'PKD',
      };
      return Promise.reject({
        config,
        mockResponse: mockResponse({ user, token: 'mock-jwt-token-xyz' }),
      });
    }

    if (url.includes('/auth/me') && method === 'get') {
      const user = useAuthStore.getState().user || {
        id: 'usr-1',
        username: 'pradeep_si',
        fullName: 'SI Pradeep Kumar',
        role: 'analyst',
        district: 'PKD',
      };
      return Promise.reject({ config, mockResponse: mockResponse(user) });
    }

    // --- Mock Consolidation Routes ---
    if (url.includes('/consolidate/upload') && method === 'post') {
      return Promise.reject({
        config,
        mockResponse: mockResponse({ jobId: 'job_' + Math.random().toString(36).substring(2, 9) }),
      });
    }

    // --- Mock Jobs Routes ---
    if (url.includes('/jobs/') && method === 'get') {
      const jobId = url.split('/').pop();
      // Mock progress
      const job = {
        id: jobId,
        jobType: 'consolidation',
        status: 'running',
        progress: 62,
        currentStep: 'Step 4/9: Classifying + summarizing items via LLM',
        createdBy: 'SI Pradeep Kumar',
        createdAt: new Date().toISOString(),
      };
      return Promise.reject({ config, mockResponse: mockResponse(job) });
    }

    if (url === '/jobs' && method === 'get') {
      const activeJobs = [
        {
          id: 'job-101',
          jobType: 'consolidation',
          status: 'running',
          progress: 62,
          currentStep: 'Step 4/9: Classifying + summarizing items via LLM',
          createdBy: 'SI Pradeep Kumar',
          createdAt: new Date().toISOString(),
        },
        {
          id: 'job-102',
          jobType: 'gnn_training',
          status: 'queued',
          progress: 0,
          currentStep: 'Waiting for worker...',
          createdBy: 'System Scheduler',
          createdAt: new Date().toISOString(),
        }
      ];
      return Promise.reject({ config, mockResponse: mockResponse(activeJobs) });
    }

    // --- Mock Report Routes ---
    if (url === '/reports' && method === 'get') {
      const reports = [
        {
          id: 'rep-1',
          reportDate: '04.06.2026',
          refNumber: 'KPIP/2026/06/04',
          eventCount: 11,
          forecastCount: 8,
          socialMediaCount: 5,
          notNeededCount: 3,
          createdBy: 'SI Pradeep Kumar',
          createdAt: new Date(Date.now() - 86400000).toISOString(),
        },
        {
          id: 'rep-2',
          reportDate: '03.06.2026',
          refNumber: 'KPIP/2026/06/03',
          eventCount: 14,
          forecastCount: 10,
          socialMediaCount: 7,
          notNeededCount: 1,
          createdBy: 'SI Pradeep Kumar',
          createdAt: new Date(Date.now() - 172800000).toISOString(),
        }
      ];
      return Promise.reject({ config, mockResponse: mockResponse(reports) });
    }

    if (url.includes('/reports/') && method === 'get') {
      const reportId = url.split('/').pop();
      const reportMetadata = {
        id: reportId,
        reportDate: '04.06.2026',
        refNumber: 'KPIP/2026/06/04',
        eventCount: 3,
        forecastCount: 1,
        socialMediaCount: 1,
        notNeededCount: 0,
        createdBy: 'SI Pradeep Kumar',
        createdAt: new Date().toISOString(),
      };
      
      const items = [
        {
          id: 'item-1',
          reportId,
          category: 'event',
          summaryText: 'Active Maoist cadre associated with RPI (RL) Blue Star. Linked to land encroachment agitation at Arippa since 2013. Multiple FIRs under UAPA and RAP Act. (PKD)',
          rawText: 'Meleparambil Chittoor Kutty was seen at Arippa protesting with group...',
          sourceFilename: 'PKD_Daily_Report.docx',
          districtTag: 'PKD',
          translationEngine: 'indictrans',
        },
        {
          id: 'item-2',
          reportId,
          category: 'event',
          summaryText: 'Extremist sympathizer Vishnu Koya was arrested by Kozhikode Town Police for writing pamphlets supporting banned outfits. Under sections 13 UAPA. (KKD)',
          rawText: 'Kozhikode Town Police arrested Vishnu Koya...',
          sourceFilename: 'KKD_pamphlets.docx',
          districtTag: 'KKD',
          translationEngine: 'indictrans',
        },
        {
          id: 'item-3',
          reportId,
          category: 'forecast',
          summaryText: 'Political agitation planned by RPI (RL) members in front of Palakkad Collectorate on 12.06.2026. Security measures ordered. (PKD)',
          rawText: 'RSU group planning protest...',
          sourceFilename: 'F1_PKD.docx',
          districtTag: 'PKD',
          translationEngine: 'none',
        }
      ];
      return Promise.reject({ config, mockResponse: mockResponse({ ...reportMetadata, items }) });
    }

    // --- Mock Profile Routes ---
    if (url === '/profiles' && method === 'get') {
      const profiles = [
        {
          id: 'prof-1',
          ppId: '040/PKD',
          name: 'Chittoor Kutty',
          parentage: 'S/o Rajan',
          address: 'Meleparambil, Nilambur, Palakkad',
          policeStation: 'Chittur PS',
          activityType: 'Extremism',
          reviewStatus: 'approved',
          updatedAt: new Date().toISOString(),
        },
        {
          id: 'prof-2',
          ppId: '041/KKD',
          name: 'Vishnu Koya',
          parentage: 'S/o Moideen Koya',
          address: 'Koyas House, Beypore, Kozhikode',
          policeStation: 'Beypore PS',
          activityType: 'Extremism',
          reviewStatus: 'approved',
          updatedAt: new Date().toISOString(),
        },
        {
          id: 'prof-3',
          ppId: 'PENDING',
          name: 'Hashim Cherian Abraham',
          parentage: 'S/o Abraham',
          address: 'Palackal House, Arippa, Kollam',
          policeStation: 'Thenmala PS',
          activityType: 'Left Wing Extremism',
          reviewStatus: 'pending',
          updatedAt: new Date().toISOString(),
        }
      ];
      return Promise.reject({ config, mockResponse: mockResponse({ items: profiles, total: 3, page: 1, limit: 10, pages: 1 }) });
    }

    if (url.includes('/profiles/') && method === 'get') {
      const profileId = url.split('/').pop();
      const profile = {
        id: profileId,
        ppId: profileId === 'prof-1' ? '040/PKD' : profileId === 'prof-2' ? '041/KKD' : 'PENDING',
        name: profileId === 'prof-1' ? 'Chittoor Kutty' : profileId === 'prof-2' ? 'Vishnu Koya' : 'Hashim Cherian Abraham',
        parentage: profileId === 'prof-1' ? 'S/o Rajan' : profileId === 'prof-2' ? 'S/o Moideen Koya' : 'S/o Abraham',
        address: profileId === 'prof-1' ? 'Meleparambil, Nilambur, Palakkad' : profileId === 'prof-2' ? 'Koyas House, Beypore, Kozhikode' : 'Palackal House, Arippa, Kollam',
        policeStation: profileId === 'prof-1' ? 'Chittur PS' : profileId === 'prof-2' ? 'Beypore PS' : 'Thenmala PS',
        activityType: 'Extremism',
        reasonForInclusion: 'Involvement in anti-national / extremist movements.',
        organizationName: 'RPI (RL) Blue Star',
        organizationRemarks: 'State level coordinator and planner.',
        briefHistory: 'Active Maoist sympathizer. Mentioned in report since 2013 Arippa land encroachment. Convicted under Arms Act and RAP Act.',
        reviewStatus: profileId === 'prof-3' ? 'pending' : 'approved',
        createdAt: new Date(Date.now() - 31536000000).toISOString(),
        updatedAt: new Date().toISOString(),
      };
      
      const cases = [
        {
          id: 'case-1',
          profileId,
          firNumber: '1599/14',
          underSections: '143, 147, 148, 427, 506(ii), 120(b) IPC, 16, 18, 20 UAPA',
          policeStation: 'Town South PS',
          caseBrief: 'Staged illegal road block and burned public bus.',
          caseStatus: 'Under Investigation',
          coAccused: 'Hashim Cherian Abraham, Mini Mathew',
        }
      ];

      const relations = [
        { id: 'rel-1', profileId, name: 'Rajan', relationType: 'Father', address: 'Palakkad' },
        { id: 'rel-2', profileId, name: 'Smt. Lakshmi', relationType: 'Spouse', address: 'Palakkad' }
      ];

      const activities = [
        {
          id: 'act-1',
          profileId,
          activityName: 'Mentioned in IS Report 04.06.2026',
          activityDesc: 'Protest activity at Arippa continuing, led by Chittoor Kutty.',
          activityDate: '04.06.2026',
          createdAt: new Date().toISOString(),
        }
      ];

      return Promise.reject({ config, mockResponse: mockResponse({ ...profile, cases, relations, activities }) });
    }

    // --- Mock Review (VEG) Routes ---
    if (url === '/review' && method === 'get') {
      const reviewItems = [
        {
          id: 'cand-1',
          name: 'Renjith Varma',
          source: 'Report dated 04.06.2026: Renjith Varma was seen leading a march near Nilambur PS.',
          extractionMethod: 'HF bert-base-NER',
          anomalyFlags: 'High-Frequency Edge Guard — linked to 4 events',
          status: 'pending',
        },
        {
          id: 'cand-2',
          name: 'Subin Kizhakkedath',
          source: 'Report dated 04.06.2026: Subin Kizhakkedath organized a secret meeting at a local homestay.',
          extractionMethod: 'LLM classification',
          anomalyFlags: 'None',
          status: 'pending',
        }
      ];
      return Promise.reject({ config, mockResponse: mockResponse(reviewItems) });
    }

    if (url.includes('/review/') && method === 'post') {
      const parts = url.split('/');
      const action = parts.pop(); // approve / reject
      const id = parts.pop();
      return Promise.reject({ config, mockResponse: mockResponse({ id, status: action === 'approve' ? 'approved' : 'rejected' }) });
    }

    // --- Mock Graph Routes ---
    if (url === '/graph/stats' && method === 'get') {
      return Promise.reject({
        config,
        mockResponse: mockResponse({
          total_nodes: 142,
          total_edges: 387,
          individual_nodes: 34,
          crime_nodes: 72,
          record_nodes: 24,
          edge_types: {
            ASSOCIATED_WITH: 110,
            MENTIONED_IN: 140,
            CO_OCCURRED_WITH: 85,
            MEMBER_OF: 32,
            ACCUSED_IN: 20,
          },
        }),
      });
    }

    if (url.includes('/graph/query') && method === 'get') {
      const nodes = [
        { id: 'ind_chittoor_kutty', label: 'Chittoor Kutty', type: 'individual', properties: { pp_id: '040/PKD', activity_type: 'Extremism' } },
        { id: 'ind_hashim_cherian', label: 'Hashim Cherian', type: 'individual', properties: { pp_id: 'PENDING', activity_type: 'Left Wing Extremism' } },
        { id: 'org_rpi_blue_star', label: 'RPI (RL) Blue Star', type: 'organization', properties: { description: 'Political extremist organization' } },
        { id: 'crime_04_06_1', label: 'Protest at Arippa', type: 'crime', properties: { district: 'PKD', date: '04.06.2026', text: 'Land encroachment agitation protest at Arippa...' } },
      ];
      
      const edges = [
        { id: 'e1', source: 'ind_chittoor_kutty', target: 'crime_04_06_1', type: 'ASSOCIATED_WITH', weight: 1.0 },
        { id: 'e2', source: 'ind_hashim_cherian', target: 'crime_04_06_1', type: 'ASSOCIATED_WITH', weight: 1.0 },
        { id: 'e3', source: 'ind_chittoor_kutty', target: 'org_rpi_blue_star', type: 'MEMBER_OF', weight: 1.0 },
        { id: 'e4', source: 'ind_hashim_cherian', target: 'org_rpi_blue_star', type: 'MEMBER_OF', weight: 1.0 },
        { id: 'e5', source: 'ind_chittoor_kutty', target: 'ind_hashim_cherian', type: 'CO_OCCURRED_WITH', weight: 3.0 },
      ];
      return Promise.reject({ config, mockResponse: mockResponse({ nodes, edges }) });
    }

    if (url.includes('/graph/associates/') && method === 'get') {
      const recs = [
        { name: 'Vishnu Koya', similarity: 0.847, hasEdge: false },
        { name: 'Biju Santhosh', similarity: 0.712, hasEdge: true },
        { name: 'Mini Mathew', similarity: 0.698, hasEdge: false },
      ];
      return Promise.reject({ config, mockResponse: mockResponse(recs) });
    }

    // --- Mock Search Routes ---
    if (url.includes('/search/semantic') && method === 'post') {
      const results = [
        {
          entityType: 'profile',
          title: 'Chittoor Kutty (PP/040/PKD)',
          score: 0.892,
          snippet: 'Active Maoist cadre associated with RPI (RL) Blue Star. Linked to land encroachment agitation at <strong>Arippa</strong>...',
          id: 'prof-1',
        },
        {
          entityType: 'report_item',
          title: 'IS Daily Report 04.06.2026',
          score: 0.814,
          snippet: 'Staged illegal road block and burned public bus near <strong>Arippa</strong> town. Charging sections of UAPA...',
          id: 'rep-1',
        }
      ];
      return Promise.reject({ config, mockResponse: mockResponse(results) });
    }

    // Default error for unmocked routes
    return Promise.reject({
      config,
      mockResponse: mockResponse({ error: 'Mock endpoint not implemented' }, 404),
    });
  }, (error) => {
    // Intercept mock error redirects
    if (error.mockResponse) {
      return Promise.resolve(error.mockResponse);
    }
    return Promise.reject(error);
  });
}
