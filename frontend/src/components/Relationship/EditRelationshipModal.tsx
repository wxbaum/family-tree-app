import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { relationshipsApi, peopleApi, Person, Relationship } from '../../services/api';
import LoadingSpinner from '../UI/LoadingSpinner';

interface EditRelationshipModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  relationship: Relationship;
  currentPersonId: string;
}

interface FormData {
  from_person_id: string;
  to_person_id: string;
  relationship_type: string;
  start_date: string;
  end_date: string;
  notes: string;
  is_active: boolean;
}

// Updated relationship types for Phase 2B
const relationshipTypes = [
  { 
    value: 'partner', 
    label: 'Partner/Spouse', 
    description: 'Partner/spouse of', 
    allowDates: true,
    bidirectional: true,
    helpText: 'Marriage, civil partnership, or romantic partnership'
  },
  { 
    value: 'parent', 
    label: 'Parent', 
    description: 'Is parent of', 
    allowDates: false,
    bidirectional: false,
    helpText: 'Biological or legal parent relationship'
  },
  { 
    value: 'child', 
    label: 'Child', 
    description: 'Is child of', 
    allowDates: false,
    bidirectional: false,
    helpText: 'Biological or legal child relationship'
  },
  { 
    value: 'sibling', 
    label: 'Sibling', 
    description: 'Is sibling of', 
    allowDates: false,
    bidirectional: true,
    helpText: 'Brother or sister (biological or legal)'
  },
  { 
    value: 'adopted_parent', 
    label: 'Adoptive Parent', 
    description: 'Adopted parent of', 
    allowDates: true,
    bidirectional: false,
    helpText: 'Legal adoptive parent relationship'
  },
  { 
    value: 'adopted_child', 
    label: 'Adopted Child', 
    description: 'Adopted child of', 
    allowDates: true,
    bidirectional: false,
    helpText: 'Legal adoptive child relationship'
  },
];

const EditRelationshipModal: React.FC<EditRelationshipModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  relationship,
  currentPersonId,
}) => {
  const [error, setError] = useState<string>('');
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isDirty },
  } = useForm<FormData>();

  // Get the other person in the relationship
  const otherPersonId = relationship.from_person_id === currentPersonId 
    ? relationship.to_person_id 
    : relationship.from_person_id;

  const {
    data: otherPerson,
    isLoading: isLoadingOtherPerson,
  } = useQuery({
    queryKey: ['person', otherPersonId],
    queryFn: () => peopleApi.getById(otherPersonId),
    enabled: isOpen && !!otherPersonId,
  });

  const {
    data: currentPerson,
    isLoading: isLoadingCurrentPerson,
  } = useQuery({
    queryKey: ['person', currentPersonId],
    queryFn: () => peopleApi.getById(currentPersonId),
    enabled: isOpen && !!currentPersonId,
  });

  // Reset form when relationship changes or modal opens
  useEffect(() => {
    if (isOpen && relationship) {
      reset({
        from_person_id: relationship.from_person_id,
        to_person_id: relationship.to_person_id,
        relationship_type: relationship.relationship_type,
        start_date: relationship.start_date ? relationship.start_date.split('T')[0] : '',
        end_date: relationship.end_date ? relationship.end_date.split('T')[0] : '',
        notes: relationship.notes || '',
        is_active: relationship.is_active,
      });
    }
  }, [isOpen, relationship, reset]);

  const updateMutation = useMutation({
    mutationFn: (data: any) => relationshipsApi.update(relationship.id, data),
    onSuccess: () => {
      // Invalidate all relevant queries
      queryClient.invalidateQueries({ queryKey: ['person', currentPersonId] });
      queryClient.invalidateQueries({ queryKey: ['person', otherPersonId] });
      queryClient.invalidateQueries({ queryKey: ['personRelationships', currentPersonId] });
      queryClient.invalidateQueries({ queryKey: ['personRelationships', otherPersonId] });
      
      // Also invalidate family tree queries if they're in the same tree
      if (currentPerson?.family_tree_id) {
        queryClient.invalidateQueries({ queryKey: ['familyTreeGraph', currentPerson.family_tree_id] });
        queryClient.invalidateQueries({ queryKey: ['familyTreePeople', currentPerson.family_tree_id] });
        queryClient.invalidateQueries({ queryKey: ['familyTreeRelationships', currentPerson.family_tree_id] });
      }
      
      onSuccess();
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to update relationship');
    },
  });

  const onSubmit = async (data: FormData) => {
    setError('');
    
    const updateData = {
      relationship_type: data.relationship_type,
      start_date: data.start_date ? new Date(data.start_date).toISOString() : undefined,
      end_date: data.end_date ? new Date(data.end_date).toISOString() : undefined,
      notes: data.notes || undefined,
      is_active: data.is_active,
    };

    updateMutation.mutate(updateData);
  };

  const handleClose = () => {
    setError('');
    onClose();
  };

  const watchedRelationshipType = watch('relationship_type');

  // Helper to check if current relationship type allows dates
  const currentRelationshipAllowsDates = () => {
    const relType = relationshipTypes.find(rt => rt.value === watchedRelationshipType);
    return relType?.allowDates || false;
  };

  // Helper to get date field labels
  const getDateLabels = () => {
    switch (watchedRelationshipType) {
      case 'partner':
        return {
          start: 'Marriage/Partnership Date',
          end: 'Divorce/Separation Date',
          startHelp: 'When the marriage or partnership began',
          endHelp: 'When the marriage or partnership ended (if applicable)'
        };
      case 'adopted_parent':
      case 'adopted_child':
        return {
          start: 'Adoption Date',
          end: 'End Date',
          startHelp: 'When the adoption was finalized',
          endHelp: 'End of legal adoption (rare)'
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

  // Helper to describe the relationship
  const getRelationshipDescription = () => {
    if (!currentPerson || !otherPerson || !watchedRelationshipType) return '';
    
    const relType = relationshipTypes.find(rt => rt.value === watchedRelationshipType);
    if (!relType) return '';
    
    if (relType.bidirectional) {
      return `${currentPerson.full_name} and ${otherPerson.full_name} are ${relType.label.toLowerCase()}s`;
    } else {
      // For directional relationships, maintain the original direction
      const isOriginalDirection = relationship.from_person_id === currentPersonId;
      if (isOriginalDirection) {
        return `${currentPerson.full_name} ${relType.description} ${otherPerson.full_name}`;
      } else {
        // Reverse the description for the opposite direction
        const reverseDescription = watchedRelationshipType === 'parent' ? 'is child of' :
                                 watchedRelationshipType === 'child' ? 'is parent of' :
                                 watchedRelationshipType === 'adopted_parent' ? 'is adopted child of' :
                                 watchedRelationshipType === 'adopted_child' ? 'is adopted parent of' :
                                 relType.description;
        return `${currentPerson.full_name} ${reverseDescription} ${otherPerson.full_name}`;
      }
    }
  };

  if (!isOpen) return null;

  const isLoading = isLoadingCurrentPerson || isLoadingOtherPerson;
  const dateLabels = getDateLabels();
  const selectedRelType = relationshipTypes.find(rt => rt.value === watchedRelationshipType);

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-lg shadow-lg rounded-md bg-white">
        <div className="mt-3">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">
              Edit Relationship
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
                {typeof error === 'string' ? error : 'Failed to update relationship'}
              </div>
            )}

            {isLoading ? (
              <LoadingSpinner />
            ) : (
              <>
                {/* People involved - Read only display */}
                <div className="bg-gray-50 p-4 rounded-md">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">People in this relationship:</h4>
                  <div className="flex items-center justify-between text-sm text-gray-900">
                    <span className="font-medium">{currentPerson?.full_name}</span>
                    <span className="text-gray-500">and</span>
                    <span className="font-medium">{otherPerson?.full_name}</span>
                  </div>
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
                    {relationshipTypes.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                  {errors.relationship_type && (
                    <p className="mt-1 text-sm text-red-600">
                      {typeof errors.relationship_type.message === 'string' 
                        ? errors.relationship_type.message 
                        : 'Please select a relationship type'}
                    </p>
                  )}
                  {selectedRelType && (
                    <p className="mt-1 text-xs text-gray-500">{selectedRelType.helpText}</p>
                  )}
                </div>

                {/* Relationship Preview */}
                {currentPerson && otherPerson && watchedRelationshipType && (
                  <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                    <p className="text-sm text-blue-800">
                      <strong>Relationship:</strong> {getRelationshipDescription()}
                    </p>
                  </div>
                )}

                {/* Optional Dates - Only show for relationships that allow dates */}
                {currentRelationshipAllowsDates() && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="start_date" className="block text-sm font-medium text-gray-700">
                        {dateLabels.start}
                      </label>
                      <input
                        {...register('start_date')}
                        type="date"
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        {dateLabels.startHelp}
                      </p>
                    </div>

                    <div>
                      <label htmlFor="end_date" className="block text-sm font-medium text-gray-700">
                        {dateLabels.end}
                      </label>
                      <input
                        {...register('end_date')}
                        type="date"
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        {dateLabels.endHelp}
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

                {/* Active Status */}
                <div className="flex items-center">
                  <input
                    {...register('is_active')}
                    type="checkbox"
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  />
                  <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">
                    This relationship is currently active
                  </label>
                </div>
              </>
            )}

            {/* Actions */}
            <div className="flex space-x-3 pt-4">
              <button
                type="button"
                onClick={handleClose}
                className="flex-1 btn-secondary"
                disabled={updateMutation.isPending}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 btn-primary flex items-center justify-center"
                disabled={updateMutation.isPending || isLoading || !isDirty}
              >
                {updateMutation.isPending ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  'Save Changes'
                )}
              </button>
            </div>

            {!isDirty && !isLoading && (
              <p className="text-center text-sm text-gray-500">
                Make changes to enable the save button
              </p>
            )}
          </form>
        </div>
      </div>
    </div>
  );
};

export default EditRelationshipModal;