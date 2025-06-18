// frontend/src/services/api.ts

import axios from 'axios';

// Configure axios instance
const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Type definitions
export interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
  subscription_tier: string;
  created_at: string;
  updated_at: string;
}

export interface FamilyTree {
  id: string;
  owner_id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface Person {
  id: string;
  family_tree_id: string;
  first_name: string;
  last_name?: string;
  maiden_name?: string;
  birth_date?: string;
  death_date?: string;
  birth_place?: string;
  death_place?: string;
  bio?: string;
  profile_photo_url?: string;
  created_at: string;
  updated_at: string;
}

export interface Relationship {
  id: string;
  from_person_id: string;
  to_person_id: string;
  relationship_category: RelationshipCategory;
  relationship_subtype?: RelationshipSubtype;
  generation_difference?: number;
  is_active: boolean;
  start_date?: string;
  end_date?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface PersonFile {
  id: string;
  person_id: string;
  filename: string;
  original_filename: string;
  file_path: string;
  file_type: string;
  mime_type: string;
  file_size: number;
  description?: string;
  created_at: string;
  updated_at: string;
}

// Enums
export type RelationshipCategory = 'family_line' | 'partner' | 'sibling' | 'extended_family';
export type RelationshipSubtype = 
  | 'biological_parent' | 'adoptive_parent' | 'step_parent' | 'foster_parent'
  | 'spouse' | 'domestic_partner' | 'engaged'
  | 'full_sibling' | 'half_sibling' | 'step_sibling' | 'adoptive_sibling'
  | 'grandparent' | 'aunt_uncle' | 'cousin' | 'niece_nephew';

// Graph visualization types
export interface GraphNode {
  id: string;
  type: string;
  data: any;
  position: { x: number; y: number };
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  data: any;
}

export interface FamilyTreeGraph {
  family_tree_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// Request/response types
export interface CreateRelationshipData {
  from_person_id: string;
  to_person_id: string;
  relationship_category: RelationshipCategory;
  relationship_subtype?: RelationshipSubtype;
  generation_difference?: number;
  start_date?: string;
  end_date?: string;
  notes?: string;
}

export interface UpdateRelationshipData {
  relationship_category?: RelationshipCategory;
  generation_difference?: number;
  relationship_subtype?: RelationshipSubtype;
  start_date?: string;
  end_date?: string;
  is_active?: boolean;
  notes?: string;
}

export interface RelationshipStatistics {
  total_relationships: number;
  by_category: Record<string, number>;
  by_subtype: Record<string, number>;
  active_relationships: number;
  inactive_relationships: number;
}

export interface InferredRelationship {
  type: string;
  person1_id: string;
  person2_id: string;
  confidence: 'high' | 'medium' | 'low';
  reason: string;
}

export interface RelationshipPath {
  path: Relationship[];
  relationship_found: boolean;
}

export interface RelationshipValidation {
  valid: boolean;
  message: string;
}

export interface MessageResponse {
  message: string;
}

// API clients
export const authApi = {
  register: async (email: string, password: string): Promise<User> => {
    const response = await apiClient.post('/auth/register', { email, password });
    return response.data;
  },

  login: async (email: string, password: string): Promise<{ access_token: string; token_type: string }> => {
    const response = await apiClient.post('/auth/login', new URLSearchParams({
      username: email,
      password: password,
    }), {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get('/users/me');
    return response.data;
  },
};

// Enhanced Family Trees API
export const familyTreesApi = {
  getAll: async (params?: {
    limit?: number;
    offset?: number;
    search?: string;
  }): Promise<FamilyTree[]> => {
    const response = await apiClient.get('/api/v1/family-trees/', { params });
    return response.data;
  },

  getCount: async (): Promise<{ count: number }> => {
    const response = await apiClient.get('/api/v1/family-trees/count');
    return response.data;
  },

  create: async (data: { name: string; description?: string }): Promise<FamilyTree> => {
    const response = await apiClient.post('/api/v1/family-trees/', data);
    return response.data;
  },

  getById: async (id: string): Promise<FamilyTree> => {
    const response = await apiClient.get(`/api/v1/family-trees/${id}`);
    return response.data;
  },

  update: async (id: string, data: { name?: string; description?: string }): Promise<FamilyTree> => {
    const response = await apiClient.put(`/api/v1/family-trees/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<MessageResponse> => {
    const response = await apiClient.delete(`/api/v1/family-trees/${id}`);
    return response.data;
  },

  getGraph: async (id: string): Promise<FamilyTreeGraph> => {
    const response = await apiClient.get(`/api/v1/family-trees/${id}/graph`);
    return response.data;
  },

  getStatistics: async (id: string): Promise<any> => {
    const response = await apiClient.get(`/api/v1/family-trees/${id}/statistics`);
    return response.data;
  },
};

// Enhanced People API
export const peopleApi = {
  create: async (data: {
    family_tree_id: string;
    first_name: string;
    last_name?: string;
    maiden_name?: string;
    birth_date?: string;
    death_date?: string;
    birth_place?: string;
    death_place?: string;
    bio?: string;
  }): Promise<Person> => {
    const response = await apiClient.post('/api/v1/people/', data);
    return response.data;
  },

  getById: async (id: string): Promise<Person> => {
    const response = await apiClient.get(`/api/v1/people/${id}`);
    return response.data;
  },

  update: async (id: string, data: Partial<Person>): Promise<Person> => {
    const response = await apiClient.put(`/api/v1/people/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<MessageResponse> => {
    const response = await apiClient.delete(`/api/v1/people/${id}`);
    return response.data;
  },

  getByFamilyTree: async (familyTreeId: string, params?: {
    limit?: number;
    offset?: number;
  }): Promise<Person[]> => {
    const response = await apiClient.get(`/api/v1/people/family-tree/${familyTreeId}`, { params });
    return response.data;
  },

  getCount: async (familyTreeId: string): Promise<{ count: number }> => {
    const response = await apiClient.get(`/api/v1/people/family-tree/${familyTreeId}/count`);
    return response.data;
  },

  search: async (familyTreeId: string, searchTerm: string, params?: {
    limit?: number;
  }): Promise<Person[]> => {
    const response = await apiClient.get(`/api/v1/people/family-tree/${familyTreeId}/search`, {
      params: { search_term: searchTerm, ...params }
    });
    return response.data;
  },

  getRelationships: async (personId: string): Promise<Record<string, any[]>> => {
    const response = await apiClient.get(`/api/v1/people/${personId}/relationships`);
    return response.data;
  },

  getAncestors: async (personId: string, generations?: number): Promise<Person[]> => {
    const response = await apiClient.get(`/api/v1/people/${personId}/ancestors`, {
      params: generations ? { generations } : {}
    });
    return response.data;
  },

  getDescendants: async (personId: string, generations?: number): Promise<Person[]> => {
    const response = await apiClient.get(`/api/v1/people/${personId}/descendants`, {
      params: generations ? { generations } : {}
    });
    return response.data;
  },

  getSiblings: async (personId: string): Promise<Person[]> => {
    const response = await apiClient.get(`/api/v1/people/${personId}/siblings`);
    return response.data;
  },

  getAge: async (personId: string, asOfDate?: string): Promise<{
    person_id: string;
    age: number | null;
    as_of_date: string;
    has_birth_date: boolean;
  }> => {
    const response = await apiClient.get(`/api/v1/people/${personId}/age`, {
      params: asOfDate ? { as_of_date: asOfDate } : {}
    });
    return response.data;
  },
};

// Complete Relationships API
export const relationshipsApi = {
  // Basic CRUD operations
  create: async (data: CreateRelationshipData): Promise<Relationship> => {
    const response = await apiClient.post('/api/v1/relationships/', data);
    return response.data;
  },

  getById: async (id: string): Promise<Relationship> => {
    const response = await apiClient.get(`/api/v1/relationships/${id}`);
    return response.data;
  },

  update: async (id: string, data: UpdateRelationshipData): Promise<Relationship> => {
    const response = await apiClient.put(`/api/v1/relationships/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<MessageResponse> => {
    const response = await apiClient.delete(`/api/v1/relationships/${id}`);
    return response.data;
  },

  // Person-specific queries
  getByPerson: async (personId: string, category?: string): Promise<Relationship[]> => {
    const response = await apiClient.get(`/api/v1/relationships/person/${personId}`, {
      params: category ? { category } : {}
    });
    return response.data;
  },

  // Family tree queries
  getByFamilyTree: async (familyTreeId: string): Promise<Relationship[]> => {
    const response = await apiClient.get(`/api/v1/relationships/family-tree/${familyTreeId}`);
    return response.data;
  },

  getStatistics: async (familyTreeId: string): Promise<RelationshipStatistics> => {
    const response = await apiClient.get(`/api/v1/relationships/family-tree/${familyTreeId}/statistics`);
    return response.data;
  },

  // Advanced relationship analysis
  getRelationshipPath: async (person1Id: string, person2Id: string, maxDepth?: number): Promise<RelationshipPath> => {
    const response = await apiClient.get(`/api/v1/relationships/path/${person1Id}/${person2Id}`, {
      params: maxDepth ? { max_depth: maxDepth } : {}
    });
    return response.data;
  },

  inferRelationships: async (familyTreeId: string): Promise<InferredRelationship[]> => {
    const response = await apiClient.get(`/api/v1/relationships/family-tree/${familyTreeId}/infer`);
    return response.data;
  },

  validateRelationship: async (data: CreateRelationshipData): Promise<RelationshipValidation> => {
    const response = await apiClient.post('/api/v1/relationships/validate', data);
    return response.data;
  },

  // Bulk operations
  createMultiple: async (relationships: CreateRelationshipData[], continueOnError?: boolean): Promise<Relationship[]> => {
    const response = await apiClient.post('/api/v1/relationships/bulk', relationships, {
      params: continueOnError ? { continue_on_error: continueOnError } : {}
    });
    return response.data;
  },

  deleteByCategory: async (familyTreeId: string, category: string): Promise<MessageResponse> => {
    const response = await apiClient.delete(`/api/v1/relationships/family-tree/${familyTreeId}/category/${category}`);
    return response.data;
  },
};

// Complete Files API
export const filesApi = {
  // File upload and management
  upload: async (personId: string, file: File, description?: string): Promise<PersonFile> => {
    const formData = new FormData();
    formData.append('file', file);
    if (description) {
      formData.append('description', description);
    }

    const response = await apiClient.post(`/api/v1/files/upload/${personId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getByPerson: async (personId: string, fileType?: string): Promise<PersonFile[]> => {
    const response = await apiClient.get(`/api/v1/files/person/${personId}`, {
      params: fileType ? { file_type: fileType } : {}
    });
    return response.data;
  },

  download: async (fileId: string): Promise<Blob> => {
    const response = await apiClient.get(`/api/v1/files/download/${fileId}`, {
      responseType: 'blob'
    });
    return response.data;
  },

  view: async (fileId: string): Promise<Blob> => {
    const response = await apiClient.get(`/api/v1/files/view/${fileId}`, {
      responseType: 'blob'
    });
    return response.data;
  },

  delete: async (fileId: string): Promise<MessageResponse> => {
    const response = await apiClient.delete(`/api/v1/files/${fileId}`);
    return response.data;
  },

  updateMetadata: async (fileId: string, description?: string): Promise<PersonFile> => {
    const formData = new FormData();
    if (description !== undefined) {
      formData.append('description', description);
    }

    const response = await apiClient.put(`/api/v1/files/${fileId}/metadata`, formData);
    return response.data;
  },

  getMetadata: async (fileId: string): Promise<PersonFile> => {
    const response = await apiClient.get(`/api/v1/files/${fileId}`);
    return response.data;
  },

  // Family tree file operations
  getByFamilyTree: async (familyTreeId: string, params?: {
    file_type?: string;
    limit?: number;
    offset?: number;
  }): Promise<PersonFile[]> => {
    const response = await apiClient.get(`/api/v1/files/family-tree/${familyTreeId}`, { params });
    return response.data;
  },

  getFamilyTreeStatistics: async (familyTreeId: string): Promise<{
    total_files: number;
    total_size_bytes: number;
    total_size_mb: number;
    by_file_type: Record<string, number>;
    by_mime_type: Record<string, number>;
    average_file_size_bytes: number;
  }> => {
    const response = await apiClient.get(`/api/v1/files/family-tree/${familyTreeId}/statistics`);
    return response.data;
  },

  search: async (familyTreeId: string, searchTerm: string, fileType?: string): Promise<PersonFile[]> => {
    const response = await apiClient.get(`/api/v1/files/family-tree/${familyTreeId}/search`, {
      params: { search_term: searchTerm, ...(fileType ? { file_type: fileType } : {}) }
    });
    return response.data;
  },

  // Bulk operations
  bulkUpload: async (personId: string, files: File[], descriptions?: string[]): Promise<PersonFile[]> => {
    const formData = new FormData();
    
    files.forEach((file) => {
      formData.append('files', file);
    });
    
    if (descriptions) {
      descriptions.forEach((description) => {
        formData.append('descriptions', description);
      });
    }

    const response = await apiClient.post(`/api/v1/files/bulk-upload/${personId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  deleteAllPersonFiles: async (personId: string, fileType?: string): Promise<MessageResponse> => {
    const response = await apiClient.delete(`/api/v1/files/person/${personId}/all`, {
      params: fileType ? { file_type: fileType } : {}
    });
    return response.data;
  },

  // System information
  getSupportedTypes: async (): Promise<{
    max_file_size_bytes: number;
    max_file_size_mb: number;
    allowed_mime_types: string[];
    file_type_categories: Record<string, string[]>;
  }> => {
    const response = await apiClient.get('/api/v1/files/types');
    return response.data;
  },
};

// Utility functions
export const downloadFile = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

export const previewFile = (blob: Blob, mimeType: string) => {
  const url = window.URL.createObjectURL(blob);
  const newWindow = window.open(url, '_blank');
  if (!newWindow) {
    // Fallback if popup blocked
    const link = document.createElement('a');
    link.href = url;
    link.target = '_blank';
    link.click();
  }
};

// Export default API object
export default {
  auth: authApi,
  familyTrees: familyTreesApi,
  people: peopleApi,
  relationships: relationshipsApi,
  files: filesApi,
};