// frontend/src/components/Relationship/AddRelationshipModal.tsx

import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQuery } from '@tanstack/react-query';
import { 
  relationshipsApi, 
  peopleApi, 
  Person, 
  RelationshipCategory, 
  RelationshipSubtype,
  CreateRelationshipData,
  RelationshipCategories 
} from '../../services/api';
import LoadingSpinner from '../UI/LoadingSpinner';

interface AddRelationshipModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  familyTreeId: string;
  preselectedPersonId?: string;
}

interface FormData {
  from_person_id: string;
  to_person_id: string;
  relationship_category: RelationshipCategory;
  generation_difference?: number;
  relationship_subtype?: RelationshipSubtype;
  start_date: string;
  end_date: string;
  notes: string;
}

const AddRelationshipModal: React.FC<AddRelationshipModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  familyTreeId,
  preselectedPersonId,
}) => {
  const [error, setError] = useState<string>('');
  
  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormData>();

  // Watch form values for dynamic behavior
  const watchedFromPerson = watch('from_person_id');
  const watchedToPerson = watch('to_person_id');
  const watchedCategory = watch('relationship_category');

  // Get all people in the family tree
  const {
    data: people,
    isLoading: isLoadingPeople,
  } = useQuery({
    queryKey: ['people', familyTreeId],
    queryFn: () => peopleApi.getByFamilyTree(familyTreeId),
    enabled: isOpen,
  });

  // Get relationship categories and their configurations
  const {
    data: relationshipCategories,
    isLoading: isLoadingCategories,
  } = useQuery({
    queryKey: ['relationshipCategories'],
    queryFn: () => relationshipsApi.getCategories(),
    enabled: isOpen,
  });

  // Create relationship mutation
  const createMutation = useMutation({
    mutationFn: relationshipsApi.create,
    onSuccess: () => {
      onSuccess();
      handleClose();
    },
    onError: (error: any) => {
      setError(error.response?.data?.detail || 'Failed to create relationship');
    },
  });

  // Set preselected person if provided
  useEffect(() => {
    if (preselectedPersonId && isOpen) {
      setValue('from_person_id', preselectedPersonId);
    }
  }, [preselectedPersonId, isOpen, setValue]);

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      reset();
      setError('');
      if (preselectedPersonId) {
        setValue('from_person_id', preselectedPersonId);
      }
    }
  }, [isOpen, reset, preselectedPersonId, setValue]);

  const onSubmit = (data: FormData) => {
    const relationshipData: CreateRelationshipData = {
      from_person_id: data.from_person_id,
      to_person_id: data.to_person_id,
      relationship_category: data.relationship_category,
      generation_difference: data.generation_difference || undefined,
      relationship_subtype: data.relationship_subtype || undefined,
      start_date: data.start_date ? new Date(data.start_date).toISOString() : undefined,
      end_date: data.end_date ? new Date(data.end_date).toISOString() : undefined,
      notes: data.notes || undefined,
    };

    createMutation.mutate(relationshipData);
  };

  const handleClose = () => {
    setError('');
    onClose();
  };

  // Helper functions
  const getPersonName = (personId: string) => {
    const person = people?.find(p => p.id === personId);
    return person?.full_name || 'Unknown';
  };

  const getCurrentCategoryConfig = () => {
    if (!relationshipCategories || !watchedCategory) return null;
    return relationshipCategories.categories[watchedCategory];
  };

  const getRelationshipDescription = () => {
    if (!watchedFromPerson || !watchedCategory || !watchedToPerson) return '';
    
    const fromName = getPersonName(watchedFromPerson);
    const toName = getPersonName(watchedToPerson);
    const categoryConfig = getCurrentCategoryConfig();
    
    if (!categoryConfig) return '';
    
    if (categoryConfig.bidirectional) {
      return `${fromName} and ${toName} are ${watchedCategory.replace('_', ' ')}s`;
    } else if (watchedCategory === 'family_line') {
      const genDiff = watch('generation_difference');
      if (genDiff === -1) {
        return `${fromName} is parent of ${toName}`;
      } else if (genDiff === 1) {
        return `${fromName} is child of ${toName}`;
      }
      return `${fromName} and ${toName} have a family relationship`;
    } else {
      return `${fromName} has ${watchedCategory.replace('_', ' ')} relationship with ${toName}`;
    }
  };

  const getDateLabels = () => {
    switch (watchedCategory) {
      case 'partner':
        return {
          start: 'Relationship Start Date',
          end: 'Relationship End Date',
          startHelp: 'When the relationship began (marriage, engagement, etc.)',
          endHelp: 'When the relationship ended (divorce, separation, etc.)'
        };
      case 'family_line':
        const subtype = watch('relationship_subtype');
        if (subtype === 'adoptive') {
          return {
            start: 'Adoption Date',
            end: 'End Date',
            startHelp: 'When the adoption was finalized',
            endHelp: 'End of legal relationship (rare)'
          };
        }
        return {
          start: 'Relationship Start Date',
          end: 'Relationship End Date',
          startHelp: 'When this relationship was established',
          endHelp: 'When this relationship ended'
        };
      default:
        return {
          start: 'Start Date',
          end: 'End Date',
          startHelp: 'When this relationship began',
          endHelp: 'When this relationship ended'
        };
    }
  };

  if (!isOpen) return null;

  const categoryConfig = getCurrentCategoryConfig();
  const dateLabels = getDateLabels();
  const isLoading = isLoadingPeople || isLoadingCategories;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
        <div className="mt-3">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">
              Add Family Relationship
            </h3>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
                {error}
              </div>
            )}

            {isLoading ? (
              <LoadingSpinner />
            ) : (
              <>
                {/* Person Selection */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="from_person_id" className="block text-sm font-medium text-gray-700">
                      First Person *
                    </label>
                    <select
                      {...register('from_person_id', { required: 'Please select the first person' })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    >
                      <option value="">Select person...</option>
                      {people?.map((person: Person) => (
                        <option key={person.id} value={person.id}>
                          {person.full_name}
                        </option>
                      ))}
                    </select>
                    {errors.from_person_id && (
                      <p className="mt-1 text-sm text-red-600">
                        {errors.from_person_id.message}
                      </p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="to_person_id" className="block text-sm font-medium text-gray-700">
                      Second Person *
                    </label>
                    <select
                      {...register('to_person_id', { required: 'Please select the second person' })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    >
                      <option value="">Select person...</option>
                      {people?.filter(p => p.id !== watchedFromPerson).map((person: Person) => (
                        <option key={person.id} value={person.id}>
                          {person.full_name}
                        </option>
                      ))}
                    </select>
                    {errors.to_person_id && (
                      <p className="mt-1 text-sm text-red-600">
                        {errors.to_person_id.message}
                      </p>
                    )}
                  </div>
                </div>

                {/* Relationship Category */}
                <div>
                  <label htmlFor="relationship_category" className="block text-sm font-medium text-gray-700">
                    Relationship Category *
                  </label>
                  <select
                    {...register('relationship_category', { required: 'Please select a relationship category' })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  >
                    <option value="">Select category...</option>
                    {relationshipCategories && Object.entries(relationshipCategories.categories).map(([key, config]) => (
                      <option key={key} value={key}>
                        {config.description}
                      </option>
                    ))}
                  </select>
                  {errors.relationship_category && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.relationship_category.message}
                    </p>
                  )}
                  {categoryConfig && (
                    <p className="mt-1 text-sm text-gray-500">
                      {categoryConfig.description}
                    </p>
                  )}
                </div>

                {/* Generation Difference - Only for family_line */}
                {watchedCategory === 'family_line' && (
                  <div>
                    <label htmlFor="generation_difference" className="block text-sm font-medium text-gray-700">
                      Generation Relationship *
                    </label>
                    <select
                      {...register('generation_difference', { 
                        required: watchedCategory === 'family_line' ? 'Please select generation relationship' : false,
                        valueAsNumber: true 
                      })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    >
                      <option value="">Select relationship...</option>
                      <option value={-1}>First person is parent of second person</option>
                      <option value={1}>First person is child of second person</option>
                    </select>
                    {errors.generation_difference && (
                      <p className="mt-1 text-sm text-red-600">
                        {errors.generation_difference.message}
                      </p>
                    )}
                    <p className="mt-1 text-sm text-gray-500">
                      This determines the parent-child direction of the relationship.
                    </p>
                  </div>
                )}

                {/* Relationship Subtype */}
                {categoryConfig && categoryConfig.valid_subtypes.length > 0 && (
                  <div>
                    <label htmlFor="relationship_subtype" className="block text-sm font-medium text-gray-700">
                      Relationship Type
                    </label>
                    <select
                      {...register('relationship_subtype')}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    >
                      <option value="">Select type (optional)...</option>
                      {categoryConfig.valid_subtypes.map((subtype: string) => (
                        <option key={subtype} value={subtype}>
                          {subtype.charAt(0).toUpperCase() + subtype.slice(1).replace('_', ' ')}
                        </option>
                      ))}
                    </select>
                    <p className="mt-1 text-sm text-gray-500">
                      Optional: Specify the specific type of {watchedCategory.replace('_', ' ')} relationship.
                    </p>
                  </div>
                )}

                {/* Relationship Description Preview */}
                {watchedFromPerson && watchedToPerson && watchedCategory && (
                  <div className="bg-blue-50 border border-blue-200 p-3 rounded-md">
                    <h4 className="text-sm font-medium text-blue-900 mb-1">Relationship Preview:</h4>
                    <p className="text-sm text-blue-800">
                      {getRelationshipDescription()}
                    </p>
                  </div>
                )}

                {/* Date Fields */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="start_date" className="block text-sm font-medium text-gray-700">
                      {dateLabels.start}
                    </label>
                    <input
                      type="date"
                      {...register('start_date')}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    />
                    <p className="mt-1 text-sm text-gray-500">
                      {dateLabels.startHelp}
                    </p>
                  </div>

                  <div>
                    <label htmlFor="end_date" className="block text-sm font-medium text-gray-700">
                      {dateLabels.end}
                    </label>
                    <input
                      type="date"
                      {...register('end_date')}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    />
                    <p className="mt-1 text-sm text-gray-500">
                      {dateLabels.endHelp}
                    </p>
                  </div>
                </div>

                {/* Notes */}
                <div>
                  <label htmlFor="notes" className="block text-sm font-medium text-gray-700">
                    Notes
                  </label>
                  <textarea
                    {...register('notes')}
                    rows={3}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    placeholder="Additional notes about this relationship (optional)"
                  />
                </div>
              </>
            )}

            {/* Form Actions */}
            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={handleClose}
                className="inline-flex justify-center py-2 px-4 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                disabled={isSubmitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={isSubmitting || isLoading}
              >
                {isSubmitting ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Creating...
                  </>
                ) : (
                  'Create Relationship'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AddRelationshipModal;