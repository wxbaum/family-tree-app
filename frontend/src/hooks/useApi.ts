// frontend/src/hooks/useApi.ts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api, { 
  FamilyTree, 
  Person, 
  Relationship, 
  PersonFile,
  CreateRelationshipData,
  UpdateRelationshipData
} from '../services/api';

// Query keys for cache management
export const queryKeys = {
  // Family Trees
  familyTrees: ['familyTrees'] as const,
  familyTree: (id: string) => ['familyTrees', id] as const,
  familyTreeGraph: (id: string) => ['familyTrees', id, 'graph'] as const,
  familyTreeStatistics: (id: string) => ['familyTrees', id, 'statistics'] as const,
  familyTreeCount: ['familyTrees', 'count'] as const,

  // People
  people: (familyTreeId: string) => ['people', familyTreeId] as const,
  person: (id: string) => ['people', 'detail', id] as const,
  peopleCount: (familyTreeId: string) => ['people', familyTreeId, 'count'] as const,
  peopleSearch: (familyTreeId: string, term: string) => ['people', familyTreeId, 'search', term] as const,
  
  // Person relationships
  personRelationships: (personId: string) => ['people', personId, 'relationships'] as const,
  personAncestors: (personId: string) => ['people', personId, 'ancestors'] as const,
  personDescendants: (personId: string) => ['people', personId, 'descendants'] as const,
  personSiblings: (personId: string) => ['people', personId, 'siblings'] as const,
  personAge: (personId: string) => ['people', personId, 'age'] as const,

  // Relationships
  relationships: (familyTreeId: string) => ['relationships', familyTreeId] as const,
  relationship: (id: string) => ['relationships', 'detail', id] as const,
  relationshipStatistics: (familyTreeId: string) => ['relationships', familyTreeId, 'statistics'] as const,
  relationshipPath: (person1Id: string, person2Id: string) => ['relationships', 'path', person1Id, person2Id] as const,
  relationshipInferences: (familyTreeId: string) => ['relationships', familyTreeId, 'infer'] as const,

  // Files
  personFiles: (personId: string) => ['files', 'person', personId] as const,
  familyTreeFiles: (familyTreeId: string) => ['files', 'familyTree', familyTreeId] as const,
  fileStatistics: (familyTreeId: string) => ['files', familyTreeId, 'statistics'] as const,
  fileSearch: (familyTreeId: string, term: string) => ['files', familyTreeId, 'search', term] as const,
  supportedFileTypes: ['files', 'types'] as const,
};

// Family Tree Hooks
export const useFamilyTrees = (params?: { limit?: number; offset?: number; search?: string }) => {
  return useQuery({
    queryKey: [...queryKeys.familyTrees, params],
    queryFn: () => api.familyTrees.getAll(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useFamilyTree = (id: string) => {
  return useQuery({
    queryKey: queryKeys.familyTree(id),
    queryFn: () => api.familyTrees.getById(id),
    enabled: !!id,
  });
};

export const useFamilyTreeGraph = (id: string) => {
  return useQuery({
    queryKey: queryKeys.familyTreeGraph(id),
    queryFn: () => api.familyTrees.getGraph(id),
    enabled: !!id,
    staleTime: 2 * 60 * 1000, // 2 minutes for graph data
  });
};

export const useFamilyTreeStatistics = (id: string) => {
  return useQuery({
    queryKey: queryKeys.familyTreeStatistics(id),
    queryFn: () => api.familyTrees.getStatistics(id),
    enabled: !!id,
  });
};

export const useCreateFamilyTree = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.familyTrees.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.familyTrees });
      queryClient.invalidateQueries({ queryKey: queryKeys.familyTreeCount });
    },
  });
};

export const useUpdateFamilyTree = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { name?: string; description?: string } }) =>
      api.familyTrees.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.familyTree(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.familyTrees });
    },
  });
};

export const useDeleteFamilyTree = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.familyTrees.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.familyTrees });
      queryClient.invalidateQueries({ queryKey: queryKeys.familyTreeCount });
    },
  });
};

// People Hooks
export const usePeople = (familyTreeId: string, params?: { limit?: number; offset?: number }) => {
  return useQuery({
    queryKey: [...queryKeys.people(familyTreeId), params],
    queryFn: () => api.people.getByFamilyTree(familyTreeId, params),
    enabled: !!familyTreeId,
  });
};

export const usePerson = (id: string) => {
  return useQuery({
    queryKey: queryKeys.person(id),
    queryFn: () => api.people.getById(id),
    enabled: !!id,
  });
};

export const usePeopleSearch = (familyTreeId: string, searchTerm: string, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.peopleSearch(familyTreeId, searchTerm),
    queryFn: () => api.people.search(familyTreeId, searchTerm),
    enabled: enabled && !!familyTreeId && searchTerm.length >= 2,
    staleTime: 30 * 1000, // 30 seconds for search results
  });
};

export const usePersonRelationships = (personId: string) => {
  return useQuery({
    queryKey: queryKeys.personRelationships(personId),
    queryFn: () => api.people.getRelationships(personId),
    enabled: !!personId,
  });
};

export const usePersonAncestors = (personId: string, generations?: number) => {
  return useQuery({
    queryKey: [...queryKeys.personAncestors(personId), generations],
    queryFn: () => api.people.getAncestors(personId, generations),
    enabled: !!personId,
  });
};

export const usePersonDescendants = (personId: string, generations?: number) => {
  return useQuery({
    queryKey: [...queryKeys.personDescendants(personId), generations],
    queryFn: () => api.people.getDescendants(personId, generations),
    enabled: !!personId,
  });
};

export const usePersonSiblings = (personId: string) => {
  return useQuery({
    queryKey: queryKeys.personSiblings(personId),
    queryFn: () => api.people.getSiblings(personId),
    enabled: !!personId,
  });
};

export const usePersonAge = (personId: string, asOfDate?: string) => {
  return useQuery({
    queryKey: [...queryKeys.personAge(personId), asOfDate],
    queryFn: () => api.people.getAge(personId, asOfDate),
    enabled: !!personId,
  });
};

export const useCreatePerson = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.people.create,
    onSuccess: (newPerson) => {
      // Invalidate people list for the family tree
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.people(newPerson.family_tree_id) 
      });
      // Invalidate graph data
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.familyTreeGraph(newPerson.family_tree_id) 
      });
      // Invalidate statistics
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.familyTreeStatistics(newPerson.family_tree_id) 
      });
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.peopleCount(newPerson.family_tree_id) 
      });
    },
  });
};

export const useUpdatePerson = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Person> }) =>
      api.people.update(id, data),
    onSuccess: (updatedPerson) => {
      // Update the specific person in cache
      queryClient.setQueryData(queryKeys.person(updatedPerson.id), updatedPerson);
      // Invalidate people list for the family tree
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.people(updatedPerson.family_tree_id) 
      });
      // Invalidate graph data
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.familyTreeGraph(updatedPerson.family_tree_id) 
      });
    },
  });
};

export const useDeletePerson = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.people.delete,
    onSuccess: (_, deletedPersonId) => {
      // Remove from all relevant caches
      queryClient.removeQueries({ queryKey: queryKeys.person(deletedPersonId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.familyTrees });
      queryClient.invalidateQueries({ queryKey: ['people'] });
      queryClient.invalidateQueries({ queryKey: ['relationships'] });
      queryClient.invalidateQueries({ queryKey: ['files'] });
    },
  });
};

// Relationship Hooks
export const useRelationships = (familyTreeId: string) => {
  return useQuery({
    queryKey: queryKeys.relationships(familyTreeId),
    queryFn: () => api.relationships.getByFamilyTree(familyTreeId),
    enabled: !!familyTreeId,
  });
};

export const useRelationship = (id: string) => {
  return useQuery({
    queryKey: queryKeys.relationship(id),
    queryFn: () => api.relationships.getById(id),
    enabled: !!id,
  });
};

export const usePersonRelationshipsList = (personId: string, category?: string) => {
  return useQuery({
    queryKey: ['relationships', 'person', personId, category],
    queryFn: () => api.relationships.getByPerson(personId, category),
    enabled: !!personId,
  });
};

export const useRelationshipStatistics = (familyTreeId: string) => {
  return useQuery({
    queryKey: queryKeys.relationshipStatistics(familyTreeId),
    queryFn: () => api.relationships.getStatistics(familyTreeId),
    enabled: !!familyTreeId,
  });
};

export const useRelationshipPath = (person1Id: string, person2Id: string, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.relationshipPath(person1Id, person2Id),
    queryFn: () => api.relationships.getRelationshipPath(person1Id, person2Id),
    enabled: enabled && !!person1Id && !!person2Id && person1Id !== person2Id,
  });
};

export const useInferredRelationships = (familyTreeId: string) => {
  return useQuery({
    queryKey: queryKeys.relationshipInferences(familyTreeId),
    queryFn: () => api.relationships.inferRelationships(familyTreeId),
    enabled: !!familyTreeId,
    staleTime: 10 * 60 * 1000, // 10 minutes - expensive operation
  });
};

export const useValidateRelationship = () => {
  return useMutation({
    mutationFn: api.relationships.validateRelationship,
  });
};

export const useCreateRelationship = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.relationships.create,
    onSuccess: (newRelationship) => {
      // Get the family tree ID from one of the people
      queryClient.invalidateQueries({ queryKey: ['relationships'] });
      queryClient.invalidateQueries({ queryKey: ['people'] });
      // Invalidate graph data for visual updates
      queryClient.invalidateQueries({ queryKey: ['familyTrees'] });
    },
  });
};

export const useUpdateRelationship = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateRelationshipData }) =>
      api.relationships.update(id, data),
    onSuccess: (updatedRelationship) => {
      queryClient.setQueryData(queryKeys.relationship(updatedRelationship.id), updatedRelationship);
      queryClient.invalidateQueries({ queryKey: ['relationships'] });
      queryClient.invalidateQueries({ queryKey: ['familyTrees'] });
    },
  });
};

export const useDeleteRelationship = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.relationships.delete,
    onSuccess: (_, deletedRelationshipId) => {
      queryClient.removeQueries({ queryKey: queryKeys.relationship(deletedRelationshipId) });
      queryClient.invalidateQueries({ queryKey: ['relationships'] });
      queryClient.invalidateQueries({ queryKey: ['familyTrees'] });
    },
  });
};

export const useCreateMultipleRelationships = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ relationships, continueOnError }: { 
      relationships: CreateRelationshipData[]; 
      continueOnError?: boolean 
    }) => api.relationships.createMultiple(relationships, continueOnError),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['relationships'] });
      queryClient.invalidateQueries({ queryKey: ['familyTrees'] });
    },
  });
};

// File Hooks
export const usePersonFiles = (personId: string, fileType?: string) => {
  return useQuery({
    queryKey: [...queryKeys.personFiles(personId), fileType],
    queryFn: () => api.files.getByPerson(personId, fileType),
    enabled: !!personId,
  });
};

export const useFamilyTreeFiles = (familyTreeId: string, params?: {
  file_type?: string;
  limit?: number;
  offset?: number;
}) => {
  return useQuery({
    queryKey: [...queryKeys.familyTreeFiles(familyTreeId), params],
    queryFn: () => api.files.getByFamilyTree(familyTreeId, params),
    enabled: !!familyTreeId,
  });
};

export const useFileStatistics = (familyTreeId: string) => {
  return useQuery({
    queryKey: queryKeys.fileStatistics(familyTreeId),
    queryFn: () => api.files.getFamilyTreeStatistics(familyTreeId),
    enabled: !!familyTreeId,
  });
};

export const useFileSearch = (familyTreeId: string, searchTerm: string, fileType?: string, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.fileSearch(familyTreeId, searchTerm),
    queryFn: () => api.files.search(familyTreeId, searchTerm, fileType),
    enabled: enabled && !!familyTreeId && searchTerm.length >= 2,
    staleTime: 30 * 1000, // 30 seconds
  });
};

export const useSupportedFileTypes = () => {
  return useQuery({
    queryKey: queryKeys.supportedFileTypes,
    queryFn: api.files.getSupportedTypes,
    staleTime: 60 * 60 * 1000, // 1 hour - rarely changes
  });
};

export const useUploadFile = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ personId, file, description }: { 
      personId: string; 
      file: File; 
      description?: string 
    }) => api.files.upload(personId, file, description),
    onSuccess: (newFile) => {
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.personFiles(newFile.person_id) 
      });
      queryClient.invalidateQueries({ queryKey: ['files'] });
    },
  });
};

export const useBulkUploadFiles = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ personId, files, descriptions }: { 
      personId: string; 
      files: File[]; 
      descriptions?: string[] 
    }) => api.files.bulkUpload(personId, files, descriptions),
    onSuccess: (newFiles) => {
      if (newFiles.length > 0) {
        queryClient.invalidateQueries({ 
          queryKey: queryKeys.personFiles(newFiles[0].person_id) 
        });
        queryClient.invalidateQueries({ queryKey: ['files'] });
      }
    },
  });
};

export const useDeleteFile = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.files.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] });
    },
  });
};

export const useUpdateFileMetadata = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ fileId, description }: { fileId: string; description?: string }) =>
      api.files.updateMetadata(fileId, description),
    onSuccess: (updatedFile) => {
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.personFiles(updatedFile.person_id) 
      });
    },
  });
};

export const useDeleteAllPersonFiles = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ personId, fileType }: { personId: string; fileType?: string }) =>
      api.files.deleteAllPersonFiles(personId, fileType),
    onSuccess: (_, { personId }) => {
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.personFiles(personId) 
      });
      queryClient.invalidateQueries({ queryKey: ['files'] });
    },
  });
};

// Utility hooks for file operations
export const useDownloadFile = () => {
  return useMutation({
    mutationFn: async ({ fileId, filename }: { fileId: string; filename: string }) => {
      const blob = await api.files.download(fileId);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    },
  });
};

export const usePreviewFile = () => {
  return useMutation({
    mutationFn: async ({ fileId }: { fileId: string }) => {
      const blob = await api.files.view(fileId);
      const url = window.URL.createObjectURL(blob);
      window.open(url, '_blank');
      return url;
    },
  });
};

// Combined hooks for complex operations
export const useFamilyTreeWithData = (familyTreeId: string) => {
  const familyTree = useFamilyTree(familyTreeId);
  const people = usePeople(familyTreeId);
  const relationships = useRelationships(familyTreeId);
  const graph = useFamilyTreeGraph(familyTreeId);
  
  return {
    familyTree,
    people,
    relationships,
    graph,
    isLoading: familyTree.isLoading || people.isLoading || relationships.isLoading || graph.isLoading,
    error: familyTree.error || people.error || relationships.error || graph.error,
  };
};

export const usePersonWithRelations = (personId: string) => {
  const person = usePerson(personId);
  const relationships = usePersonRelationships(personId);
  const ancestors = usePersonAncestors(personId, 3); // 3 generations
  const descendants = usePersonDescendants(personId, 3); // 3 generations
  const siblings = usePersonSiblings(personId);
  const files = usePersonFiles(personId);
  const age = usePersonAge(personId);
  
  return {
    person,
    relationships,
    ancestors,
    descendants,
    siblings,
    files,
    age,
    isLoading: person.isLoading || relationships.isLoading,
    error: person.error || relationships.error,
  };
};

// Custom hook for optimistic updates
export const useOptimisticPersonUpdate = () => {
  const queryClient = useQueryClient();
  const updatePersonMutation = useUpdatePerson();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Person> }) => {
      // Optimistically update the cache
      const previousPerson = queryClient.getQueryData(queryKeys.person(id));
      if (previousPerson) {
        queryClient.setQueryData(queryKeys.person(id), { ...previousPerson, ...data });
      }
      
      return api.people.update(id, data);
    },
    onError: (error, { id }) => {
      // Revert optimistic update on error
      queryClient.invalidateQueries({ queryKey: queryKeys.person(id) });
    },
    onSuccess: (updatedPerson) => {
      // Ensure the cache is updated with the server response
      queryClient.setQueryData(queryKeys.person(updatedPerson.id), updatedPerson);
    },
  });
};

// Export all hooks
export default {
  // Family Trees
  useFamilyTrees,
  useFamilyTree,
  useFamilyTreeGraph,
  useFamilyTreeStatistics,
  useCreateFamilyTree,
  useUpdateFamilyTree,
  useDeleteFamilyTree,
  
  // People
  usePeople,
  usePerson,
  usePeopleSearch,
  usePersonRelationships,
  usePersonAncestors,
  usePersonDescendants,
  usePersonSiblings,
  usePersonAge,
  useCreatePerson,
  useUpdatePerson,
  useDeletePerson,
  
  // Relationships
  useRelationships,
  useRelationship,
  usePersonRelationshipsList,
  useRelationshipStatistics,
  useRelationshipPath,
  useInferredRelationships,
  useValidateRelationship,
  useCreateRelationship,
  useUpdateRelationship,
  useDeleteRelationship,
  useCreateMultipleRelationships,
  
  // Files
  usePersonFiles,
  useFamilyTreeFiles,
  useFileStatistics,
  useFileSearch,
  useSupportedFileTypes,
  useUploadFile,
  useBulkUploadFiles,
  useDeleteFile,
  useUpdateFileMetadata,
  useDeleteAllPersonFiles,
  useDownloadFile,
  usePreviewFile,
  
  // Combined
  useFamilyTreeWithData,
  usePersonWithRelations,
  useOptimisticPersonUpdate,
};