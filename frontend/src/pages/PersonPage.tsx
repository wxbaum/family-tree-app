import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { peopleApi, filesApi } from '../services/api';
import LoadingSpinner from '../components/UI/LoadingSpinner';

const PersonPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  if (!id) {
    return <div>Person not found</div>;
  }

  const {
    data: person,
    isLoading: isLoadingPerson,
    error: personError,
  } = useQuery({
    queryKey: ['person', id],
    queryFn: () => peopleApi.getById(id),
  });

  const {
    data: files,
    isLoading: isLoadingFiles,
  } = useQuery({
    queryKey: ['personFiles', id],
    queryFn: () => filesApi.getByPerson(id),
  });

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

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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

        <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
          <div className="flex items-start space-x-6">
            {/* Profile Photo */}
            <div className="flex-shrink-0">
              <div className="w-24 h-24 bg-gray-300 rounded-full flex items-center justify-center">
                {person.profile_photo_url ? (
                  <img
                    src={person.profile_photo_url}
                    alt={person.full_name}
                    className="w-full h-full rounded-full object-cover"
                  />
                ) : (
                  <svg className="w-12 h-12 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                )}
              </div>
            </div>

            {/* Basic Info */}
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {person.full_name}
              </h1>
              {person.maiden_name && (
                <p className="text-lg text-gray-600 mb-4">
                  Maiden name: {person.maiden_name}
                </p>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">Birth Date</p>
                  <p className="text-gray-900">{formatDate(person.birth_date)}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Death Date</p>
                  <p className="text-gray-900">{formatDate(person.death_date)}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Birth Place</p>
                  <p className="text-gray-900">{person.birth_place || 'Unknown'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Death Place</p>
                  <p className="text-gray-900">{person.death_place || 'Unknown'}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Biography */}
          {person.bio && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Biography</h3>
              <p className="text-gray-700 whitespace-pre-wrap">{person.bio}</p>
            </div>
          )}
        </div>
      </div>

      {/* Files Section */}
      <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900">Documents & Photos</h2>
          <button className="btn-primary">
            Upload File
          </button>
        </div>

        {isLoadingFiles ? (
          <LoadingSpinner />
        ) : files && files.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {files.map((file) => (
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
                      <p className="text-xs text-gray-600 mt-1">
                        {file.description}
                      </p>
                    )}
                  </div>
                </div>
                <div className="mt-3 flex space-x-2">
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
              Upload photos, documents, or other files related to this person.
            </p>
            <div className="mt-6">
              <button className="btn-primary">
                Upload First File
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PersonPage;