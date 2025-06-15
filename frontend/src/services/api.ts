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

// Types
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

export interface Relationship {
  id: string;
  from_person_id: string;
  to_person_id: string;
  relationship_type: 'partner' | 'parent' | 'child' | 'sibling' | 'adopted_child' | 'adopted_parent';
  start_date?: string;
  end_date?: string;
  is_active: boolean;
  notes?: string;
  created_at: string;
  updated_at?: string;
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
  type: string;
  data: Relationship;
}

export interface FamilyTreeGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// Auth API
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

// Family Trees API
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

// People API
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

// Relationships API
export const relationshipsApi = {
  create: async (data: {
    from_person_id: string;
    to_person_id: string;
    relationship_type: string;
    start_date?: string;
    end_date?: string;
    notes?: string;
  }): Promise<Relationship> => {
    const response = await apiClient.post('/api/v1/relationships/', data);
    return response.data;
  },

  getById: async (id: string): Promise<Relationship> => {
    const response = await apiClient.get(`/api/v1/relationships/${id}`);
    return response.data;
  },

  update: async (id: string, data: Partial<Relationship>): Promise<Relationship> => {
    const response = await apiClient.put(`/api/v1/relationships/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/relationships/${id}`);
  },

  getByPerson: async (personId: string): Promise<Relationship[]> => {
    const response = await apiClient.get(`/api/v1/relationships/person/${personId}`);
    return response.data;
  },

  getByFamilyTree: async (familyTreeId: string): Promise<Relationship[]> => {
    const response = await apiClient.get(`/api/v1/relationships/family-tree/${familyTreeId}`);
    return response.data;
  },
};

// Files API
export const filesApi = {
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

  getByPerson: async (personId: string): Promise<PersonFile[]> => {
    const response = await apiClient.get(`/api/v1/files/person/${personId}`);
    return response.data;
  },

  download: async (fileId: string): Promise<Blob> => {
    const response = await apiClient.get(`/api/v1/files/download/${fileId}`, {
      responseType: 'blob',
    });
    return response.data;
  },

  delete: async (fileId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/files/${fileId}`);
  },
};