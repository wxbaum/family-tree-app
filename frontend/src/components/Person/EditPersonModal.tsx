import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { peopleApi, Person } from '../../services/api';
import LoadingSpinner from '../UI/LoadingSpinner';

interface EditPersonModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  person: Person;
}

interface FormData {
  first_name: string;
  last_name: string;
  maiden_name: string;
  birth_date: string;
  death_date: string;
  birth_place: string;
  death_place: string;
  bio: string;
}

const EditPersonModal: React.FC<EditPersonModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  person,
}) => {
  const [error, setError] = useState<string>('');
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<FormData>();

  // Reset form when person changes or modal opens
  useEffect(() => {
    if (isOpen && person) {
      reset({
        first_name: person.first_name || '',
        last_name: person.last_name || '',
        maiden_name: person.maiden_name || '',
        birth_date: person.birth_date ? person.birth_date.split('T')[0] : '',
        death_date: person.death_date ? person.death_date.split('T')[0] : '',
        birth_place: person.birth_place || '',
        death_place: person.death_place || '',
        bio: person.bio || '',
      });
    }
  }, [isOpen, person, reset]);

  const updateMutation = useMutation({
    mutationFn: (data: any) => peopleApi.update(person.id, data),
    onSuccess: (updatedPerson) => {
      // Update all relevant queries
      queryClient.invalidateQueries({ queryKey: ['person', person.id] });
      queryClient.invalidateQueries({ queryKey: ['familyTreePeople', person.family_tree_id] });
      queryClient.invalidateQueries({ queryKey: ['familyTreeGraph', person.family_tree_id] });
      
      // Refresh the queries to get latest data
      queryClient.refetchQueries({ queryKey: ['person', person.id] });
      queryClient.refetchQueries({ queryKey: ['familyTreeGraph', person.family_tree_id] });
      
      onSuccess();
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to update person');
    },
  });

  const onSubmit = async (data: FormData) => {
    setError('');
    
    // Convert dates to ISO format or undefined
    const updateData = {
      first_name: data.first_name,
      last_name: data.last_name || undefined,
      maiden_name: data.maiden_name || undefined,
      birth_date: data.birth_date ? new Date(data.birth_date).toISOString() : undefined,
      death_date: data.death_date ? new Date(data.death_date).toISOString() : undefined,
      birth_place: data.birth_place || undefined,
      death_place: data.death_place || undefined,
      bio: data.bio || undefined,
    };

    updateMutation.mutate(updateData);
  };

  const handleClose = () => {
    setError('');
    onClose();
  };

  const formatDateForInput = (dateString?: string) => {
    if (!dateString) return '';
    return dateString.split('T')[0];
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
        <div className="mt-3">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-gray-900">
              Edit {person.full_name}
            </h3>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
                {typeof error === 'string' ? error : 'Failed to update person'}
              </div>
            )}

            {/* Basic Information */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="text-lg font-medium text-gray-900 mb-4">Basic Information</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="first_name" className="block text-sm font-medium text-gray-700">
                    First Name *
                  </label>
                  <input
                    {...register('first_name', {
                      required: 'First name is required',
                      maxLength: {
                        value: 100,
                        message: 'First name must be less than 100 characters',
                      },
                    })}
                    type="text"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    placeholder="John"
                  />
                  {errors.first_name && (
                    <p className="mt-1 text-sm text-red-600">{errors.first_name.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="last_name" className="block text-sm font-medium text-gray-700">
                    Last Name
                  </label>
                  <input
                    {...register('last_name')}
                    type="text"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    placeholder="Smith"
                  />
                </div>

                <div>
                  <label htmlFor="maiden_name" className="block text-sm font-medium text-gray-700">
                    Maiden Name
                  </label>
                  <input
                    {...register('maiden_name')}
                    type="text"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    placeholder="Johnson"
                  />
                  <p className="mt-1 text-xs text-gray-500">Birth name before marriage</p>
                </div>
              </div>
            </div>

            {/* Life Events */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="text-lg font-medium text-gray-900 mb-4">Life Events</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="birth_date" className="block text-sm font-medium text-gray-700">
                    Birth Date
                  </label>
                  <input
                    {...register('birth_date')}
                    type="date"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label htmlFor="death_date" className="block text-sm font-medium text-gray-700">
                    Death Date
                  </label>
                  <input
                    {...register('death_date')}
                    type="date"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  />
                  <p className="mt-1 text-xs text-gray-500">Leave blank if still living</p>
                </div>

                <div>
                  <label htmlFor="birth_place" className="block text-sm font-medium text-gray-700">
                    Birth Place
                  </label>
                  <input
                    {...register('birth_place')}
                    type="text"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    placeholder="New York, NY, USA"
                  />
                </div>

                <div>
                  <label htmlFor="death_place" className="block text-sm font-medium text-gray-700">
                    Death Place
                  </label>
                  <input
                    {...register('death_place')}
                    type="text"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    placeholder="Los Angeles, CA, USA"
                  />
                </div>
              </div>
            </div>

            {/* Biography */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="text-lg font-medium text-gray-900 mb-4">Biography</h4>
              
              <div>
                <label htmlFor="bio" className="block text-sm font-medium text-gray-700">
                  Life Story
                </label>
                <textarea
                  {...register('bio')}
                  rows={4}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  placeholder="Share their life story, achievements, personality, and memorable moments..."
                />
                <p className="mt-1 text-xs text-gray-500">Tell their story for future generations</p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex space-x-3 pt-6 border-t border-gray-200">
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
                disabled={updateMutation.isPending || !isDirty}
              >
                {updateMutation.isPending ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  'Save Changes'
                )}
              </button>
            </div>

            {!isDirty && (
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

export default EditPersonModal;