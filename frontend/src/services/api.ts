// frontend/src/services/api.ts - Updated types section

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
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

// UPDATED TYPES FOR NEW RELATIONSHIP SYSTEM
export interface User {
  id: string;
  email: string;
  is_active: boolean;
  subscription_tier: string;
  created_at: string;
}

export interface FamilyTree {
  id: string;
  owner_id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at?: string;
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
  updated_at?: string;
  full_name: string;
}

// NEW RELATIONSHIP SYSTEM TYPES
export type RelationshipCategory = 'family_line' | 'partner' | 'sibling' | 'extended_family';

export type RelationshipSubtype = 
  // Family line subtypes
  | 'biological' | 'adoptive' | 'step' | 'foster'
  // Partner subtypes  
  | 'married' | 'engaged' | 'dating' | 'divorced' | 'separated' | 'widowed'
  // Sibling subtypes
  | 'half'
  // Extended family subtypes
  | 'aunt' | 'uncle' | 'cousin' | 'grandparent' | 'grandchild' | 'in_law';

export interface Relationship {
  id: string;
  from_person_id: string;
  to_person_id: string;
  relationship_category: RelationshipCategory;
  generation_difference?: number; // Only for family_line: -1 (parent), +1 (child)
  relationship_subtype?: RelationshipSubtype;
  start_date?: string;
  end_date?: string;
  is_active: boolean;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface RelationshipDisplay {
  id: string;
  other_person_id: string;
  other_person_name: string;
  relationship_category: RelationshipCategory;
  generation_difference?: number;
  relationship_subtype?: RelationshipSubtype;
  description: string; // Human-readable description from perspective
  is_active: boolean;
  start_date?: string;
  end_date?: string;
  notes?: string;
}

export interface RelationshipCategories {
  categories: {
    [key in RelationshipCategory]: {
      description: string;
      requires_generation_difference: boolean;
      valid_subtypes: string[];
      bidirectional?: boolean;
      generation_values?: {
        [key: string]: string;
      };
    };
  };
}

// Family line specific interface for cleaner typing
export interface FamilyLineRelationships {
  parents: Person[];
  children: Person[];
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
  uploaded_at: string;
}

export interface GraphNode {
  id: string;
  type: string;
  data: Person;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string; // Maps to relationship_category
  data: Relationship;
}

export interface FamilyTreeGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// Relationship creation/update interfaces
export interface CreateRelationshipData {
  from_person_id: string;
  to_person_id: string;
  relationship_category: RelationshipCategory;
  generation_difference?: number;
  relationship_subtype?: RelationshipSubtype;
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

// Relationship statistics and analytics
export interface RelationshipStatistics {
  total_relationships: number;
  by_category: Record<RelationshipCategory, number>;
  by_subtype: Record<RelationshipSubtype, number>;
  active_relationships: number;
  inactive_relationships: number;
}

// Relationship inference
export interface InferredRelationship {
  type: string;
  person1_id: string;
  person2_id: string;
  confidence: 'high' | 'medium' | 'low';
  reason: string;
}

// Relationship path finding
export interface RelationshipPath {
  path: Relationship[];
  relationship_found: boolean;
}

// Validation response
export interface RelationshipValidation {
  valid: boolean;
  message: string;
}

// UPDATED API CLIENTS WITH NEW RELATIONSHIP SYSTEM

// Auth API (unchanged)
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

// Family Trees API (unchanged)
export const familyTreesApi = {
  getAll: async (): Promise<FamilyTree[]> => {
    const response = await apiClient.get('/api/v1/family-trees/');
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

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/family-trees/${id}`);
  },

  getGraph: async (id: string): Promise<FamilyTreeGraph> => {
    const response = await apiClient.get(`/api/v1/family-trees/${id}/graph`);
    return response.data;
  },
};

// People API (unchanged)
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

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/people/${id}`);
  },

  getByFamilyTree: async (familyTreeId: string): Promise<Person[]> => {
    const response = await apiClient.get(`/api/v1/people/family-tree/${familyTreeId}`);
    return response.data;
  },
};

// UPDATED RELATIONSHIPS API FOR NEW SYSTEM
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

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/relationships/${id}`);
  },

  // Person-specific queries
  getByPerson: async (personId: string): Promise<Relationship[]> => {
    const response = await apiClient.get(`/api/v1/relationships/person/${personId}`);
    return response.data;
  },

  getByPersonDisplay: async (personId: string): Promise<RelationshipDisplay[]> => {
    const response = await apiClient.get(`/api/v1/relationships/person/${personId}/display`);
    return response.data;
  },

  getFamilyLine: async (personId: string): Promise<FamilyLineRelationships> => {
    const response = await apiClient.get(`/api/v1/relationships/person/${personId}/family-line`);
    return response.data;
  },

  getPartners: async (personId: string): Promise<Person[]> => {
    const response = await apiClient.get(`/api/v1/relationships/person/${personId}/partners`);
    return response.data;
  },

  getSiblings: async (personId: string): Promise<Person[]> => {
    const response = await apiClient.get(`/api/v1/relationships/person/${personId}/siblings`);
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

  // Advanced features
  getRelationshipPath: async (person1Id: string, person2Id: string): Promise<RelationshipPath> => {
    const response = await apiClient.get(`/api/v1/relationships/path/${person1Id}/${person2Id}`);
    return response.data;
  },

  inferRelationships: async (familyTreeId: string): Promise<InferredRelationship[]> => {
    const response = await apiClient.get(`/api/v1/relationships/family-tree/${familyTreeId}/infer`);
    return response.data;
  },

  // Utility functions
  getCategories: async (): Promise<RelationshipCategories> => {
    const response = await apiClient.get('/api/v1/relationships/categories');
    return response.data;
  },

  validateRelationship: async (data: CreateRelationshipData): Promise<RelationshipValidation> => {
    const response = await apiClient.post('/api/v1/relationships/validate', data);
    return response.data;
  },
};

// Files API (unchanged)
export const filesApi = {
  upload: async (personId: string, file: File, description?: string): Promise<PersonFile> => {
    const formData = new FormData();
    formData.append('file', file);
    if (description) {
      formData.append('description', description);
    }

    const response = await apiClient.post(`/api/v1/files/person/${personId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getByPerson: async (personId: string): Promise<PersonFile[]> => {
    const response = await apiClient.get(`/api/v1/files/person/${personId}`);
    return response.data;
  },

  delete: async (fileId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/files/${fileId}`);
  },
};