import React, { useState, useEffect } from 'react';
import { useParams, Link, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { peopleApi, filesApi, PersonFile } from '../services/api';
import LoadingSpinner from '../components/UI/LoadingSpinner';
import EditPersonModal from '../components/Person/EditPersonModal';
import PersonRelationshipsSection from '../components/Person/PersonRelationshipsSection';

const PersonPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  // All hooks must be called before any conditional logic
  const {
    data: person,
    isLoading: isLoadingPerson,
    error: personError,
  } = useQuery({
    queryKey: ['person', id],
    queryFn: () => peopleApi.getById(id!),
    enabled: !!id, // Only run if id exists
  });

  const {
    data: files,
    isLoading: isLoadingFiles,
  } = useQuery({
    queryKey: ['personFiles', id],
    queryFn: () => filesApi.getByPerson(id!),
    enabled: !!id, // Only run if id exists
  });

  // Check if we should open edit modal on page load
  useEffect(() => {
    if (searchParams.get('edit') === 'true') {
      setIsEditModalOpen(true);
      // Remove the edit parameter from URL without causing a navigation
      setSearchParams(prev => {
        const newParams = new URLSearchParams(prev);
        newParams.delete('edit');
        return newParams;
      });
    }
  }, [searchParams, setSearchParams]);

  // Early returns after all hooks
  if (!id) {
    return <div>Person not found</div>;
  }

  const handleEditSuccess = () => {
    setIsEditModalOpen(false);
    // The query will be invalidated and refetched by the EditPersonModal
  };

  if (isLoadingPerson) {
    return <LoadingSpinner className="min-h-screen" />;
  }

  if (personError || !person) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Person Not Found</h2>
          <p className="text-gray-600 mb-4">The person you're looking for doesn't exist or you don't have access.</p>
          <Link to="/dashboard" className="btn-primary">
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleDateString();
  };

  const getLifespan = () => {
    const birthYear = person.birth_date ? new Date(person.birth_date).getFullYear() : null;
    const deathYear = person.death_date ? new Date(person.death_date).getFullYear() : null;
    
    if (birthYear && deathYear) {
      return `${birthYear} - ${deathYear} (${deathYear - birthYear} years)`;
    } else if (birthYear) {
      const currentYear = new Date().getFullYear();
      return `${birthYear} - Present (${currentYear - birthYear} years old)`;
    } else if (deathYear) {
      return `Unknown - ${deathYear}`;
    }
    return 'Unknown lifespan';
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <Link
          to={`/family-tree/${person.family_tree_id}`}
          className="inline-flex items-center text-gray-500 hover:text-gray-700 transition-colors mb-4"
        >
          <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Family Tree
        </Link>

        {/* Main Profile Card */}
        <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-start space-x-6 flex-1">
              {/* Profile Photo */}
              <div className="flex-shrink-0">
                <div className="w-32 h-32 bg-gray-300 rounded-full flex items-center justify-center">
                  {person.profile_photo_url ? (
                    <img
                      src={person.profile_photo_url}
                      alt={person.full_name}
                      className="w-full h-full rounded-full object-cover"
                    />
                  ) : (
                    <svg className="w-16 h-16 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  )}
                </div>
              </div>

              {/* Basic Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-3 mb-2">
                  <h1 className="text-3xl font-bold text-gray-900">
                    {person.full_name}
                  </h1>
                  <button
                    onClick={() => setIsEditModalOpen(true)}
                    className="inline-flex items-center px-3 py-1 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
                  >
                    <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                    Edit Details
                  </button>
                </div>

                {person.maiden_name && (
                  <p className="text-lg text-gray-600 mb-3">
                    Maiden name: {person.maiden_name}
                  </p>
                )}

                <div className="text-lg text-gray-700 mb-4">
                  <p className="font-medium">{getLifespan()}</p>
                </div>

                {/* Quick Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-gray-50 p-3 rounded-md">
                    <p className="text-sm font-medium text-gray-500">Birth</p>
                    <p className="text-gray-900">{formatDate(person.birth_date)}</p>
                    {person.birth_place && (
                      <p className="text-sm text-gray-600">{person.birth_place}</p>
                    )}
                  </div>
                  
                  {person.death_date && (
                    <div className="bg-gray-50 p-3 rounded-md">
                      <p className="text-sm font-medium text-gray-500">Death</p>
                      <p className="text-gray-900">{formatDate(person.death_date)}</p>
                      {person.death_place && (
                        <p className="text-sm text-gray-600">{person.death_place}</p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Biography Section */}
          {person.bio && (
            <div className="pt-6 border-t border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Biography</h3>
              <div className="prose max-w-none">
                <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                  {person.bio}
                </p>
              </div>
            </div>
          )}

          {!person.bio && (
            <div className="pt-6 border-t border-gray-200">
              <div className="text-center py-6">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">No biography yet</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Add their life story, achievements, and memorable moments.
                </p>
                <div className="mt-6">
                  <button
                    onClick={() => setIsEditModalOpen(true)}
                    className="btn-primary"
                  >
                    Add Biography
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Relationships Section - NEW for Phase 2B */}
      <PersonRelationshipsSection person={person} />

      {/* Files Section */}
      <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900">Documents & Photos</h2>
          <button className="btn-primary">
            <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            Upload File
          </button>
        </div>

        {isLoadingFiles ? (
          <LoadingSpinner />
        ) : files && files.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {files.map((file: PersonFile) => (
              <div key={file.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0">
                    {file.file_type === 'image' ? (
                      <svg className="h-8 w-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    ) : file.file_type === 'pdf' ? (
                      <svg className="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    ) : (
                      <svg className="h-8 w-8 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {file.original_filename}
                    </p>
                    <p className="text-sm text-gray-500">
                      {(file.file_size / 1024 / 1024).toFixed(1)} MB
                    </p>
                    {file.description && (
                      <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                        {file.description}
                      </p>
                    )}
                  </div>
                </div>
                <div className="mt-3 flex space-x-2">
                  <button className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-2 py-1 rounded transition-colors">
                    View
                  </button>
                  <button className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-2 py-1 rounded transition-colors">
                    Download
                  </button>
                  <button className="text-xs text-red-600 hover:text-red-800 transition-colors">
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No documents</h3>
            <p className="mt-1 text-sm text-gray-500">
              Upload photos, documents, or other files related to {person.first_name}.
            </p>
            <div className="mt-6">
              <button className="btn-primary">
                Upload First File
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Edit Person Modal */}
      <EditPersonModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        onSuccess={handleEditSuccess}
        person={person}
      />
    </div>
  );
};

export default PersonPage;