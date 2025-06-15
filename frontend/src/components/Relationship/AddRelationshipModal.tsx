import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQuery } from '@tanstack/react-query';
import { relationshipsApi, peopleApi, Person } from '../../services/api';
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
  relationship_type: string;
  start_date: string;
  end_date: string;
  notes: string;
}

const relationshipTypes = [
  { value: 'partner', label: 'Partner', description: 'Partner/spouse of', allowDates: true },
  { value: 'parent', label: 'Parent', description: 'Is parent of', allowDates: false },
  { value: 'child', label: 'Child', description: 'Is child of', allowDates: false },
  { value: 'sibling', label: 'Sibling', description: 'Is sibling of', allowDates: false },
  { value: 'adopted_parent', label: 'Adoptive Parent', description: 'Adopted parent of', allowDates: true },
  { value: 'adopted_child', label: 'Adopted Child', description: 'Adopted child of', allowDates: true },
];

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
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: {
      from_person_id: preselectedPersonId || '',
    },
  });

  // Get all people in the family tree for selection
  const {
    data: people,
    isLoading: isLoadingPeople,
  } = useQuery({
    queryKey: ['familyTreePeople', familyTreeId],
    queryFn: () => peopleApi.getByFamilyTree(familyTreeId),
    enabled: isOpen,
  });

  const createMutation = useMutation({
    mutationFn: relationshipsApi.create,
    onSuccess: () => {
      reset();
      onSuccess();
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to create relationship');
    },
  });

  const onSubmit = async (data: FormData) => {
    setError('');
    
    // Validate that from and to are different people
    if (data.from_person_id === data.to_person_id) {
      setError('Cannot create a relationship between the same person');
      return;
    }

    const relationshipData = {
      from_person_id: data.from_person_id,
      to_person_id: data.to_person_id,
      relationship_type: data.relationship_type,
      start_date: data.start_date || undefined,
      end_date: data.end_date || undefined,
      notes: data.notes || undefined,
    };

    createMutation.mutate(relationshipData);
  };

  const handleClose = () => {
    reset();
    setError('');
    onClose();
  };

  const watchedFromPerson = watch('from_person_id');
  const watchedRelationshipType = watch('relationship_type');

  // Helper to get the display name for a person
  const getPersonName = (personId: string) => {
    const person = people?.find(p => p.id === personId);
    return person?.full_name || 'Unknown';
  };

  // Helper to describe the relationship
  const getRelationshipDescription = () => {
    if (!watchedFromPerson || !watchedRelationshipType) return '';
    
    const fromName = getPersonName(watchedFromPerson);
    const relType = relationshipTypes.find(rt => rt.value === watchedRelationshipType);
    
    return `${fromName} ${relType?.description || ''} [selected person]`;
  };

  // Helper to check if current relationship type allows dates
  const currentRelationshipAllowsDates = () => {
    const relType = relationshipTypes.find(rt => rt.value === watchedRelationshipType);
    return relType?.allowDates || false;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-lg shadow-lg rounded-md bg-white">
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

            {isLoadingPeople ? (
              <LoadingSpinner />
            ) : (
              <>
                {/* From Person */}
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
                    <p className="mt-1 text-sm text-red-600">{errors.from_person_id.message}</p>
                  )}
                </div>

                {/* Relationship Type */}
                <div>
                  <label htmlFor="relationship_type" className="block text-sm font-medium text-gray-700">
                    Relationship Type *
                  </label>
                  <select
                    {...register('relationship_type', { required: 'Please select a relationship type' })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  >
                    <option value="">Select relationship...</option>
                    {relationshipTypes.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                  {errors.relationship_type && (
                    <p className="mt-1 text-sm text-red-600">{errors.relationship_type.message}</p>
                  )}
                </div>

                {/* To Person */}
                <div>
                  <label htmlFor="to_person_id" className="block text-sm font-medium text-gray-700">
                    Second Person *
                  </label>
                  <select
                    {...register('to_person_id', { required: 'Please select the second person' })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  >
                    <option value="">Select person...</option>
                    {people?.filter((person: Person) => person.id !== watchedFromPerson).map((person: Person) => (
                      <option key={person.id} value={person.id}>
                        {person.full_name}
                      </option>
                    ))}
                  </select>
                  {errors.to_person_id && (
                    <p className="mt-1 text-sm text-red-600">{errors.to_person_id.message}</p>
                  )}
                </div>

                {/* Relationship Preview */}
                {watchedFromPerson && watchedRelationshipType && (
                  <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                    <p className="text-sm text-blue-800">
                      <strong>Relationship:</strong> {getRelationshipDescription()}
                    </p>
                    {!currentRelationshipAllowsDates() && (
                      <p className="text-xs text-blue-600 mt-1">
                        <em>Note: {relationshipTypes.find(rt => rt.value === watchedRelationshipType)?.label} relationships are permanent and don't require dates.</em>
                      </p>
                    )}
                  </div>
                )}

                {/* Optional Dates - Only show for relationships that allow dates */}
                {currentRelationshipAllowsDates() && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="start_date" className="block text-sm font-medium text-gray-700">
                        Start Date
                      </label>
                      <input
                        {...register('start_date')}
                        type="date"
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                        placeholder="Marriage, adoption, etc."
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        {watchedRelationshipType === 'partner' && 'Marriage or partnership start date'}
                        {(watchedRelationshipType === 'adopted_parent' || watchedRelationshipType === 'adopted_child') && 'Adoption date'}
                      </p>
                    </div>

                    <div>
                      <label htmlFor="end_date" className="block text-sm font-medium text-gray-700">
                        End Date
                      </label>
                      <input
                        {...register('end_date')}
                        type="date"
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                        placeholder="Divorce, separation, etc."
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        {watchedRelationshipType === 'partner' && 'Divorce or separation date (if applicable)'}
                        {(watchedRelationshipType === 'adopted_parent' || watchedRelationshipType === 'adopted_child') && 'End of legal adoption (rare)'}
                      </p>
                    </div>
                  </div>
                )}

                {/* Notes */}
                <div>
                  <label htmlFor="notes" className="block text-sm font-medium text-gray-700">
                    Notes
                  </label>
                  <textarea
                    {...register('notes')}
                    rows={2}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    placeholder="Additional details about this relationship..."
                  />
                </div>
              </>
            )}

            {/* Actions */}
            <div className="flex space-x-3 pt-4">
              <button
                type="button"
                onClick={handleClose}
                className="flex-1 btn-secondary"
                disabled={createMutation.isPending}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 btn-primary flex items-center justify-center"
                disabled={createMutation.isPending || isLoadingPeople}
              >
                {createMutation.isPending ? (
                  <LoadingSpinner size="sm" />
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