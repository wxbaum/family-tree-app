import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { familyTreesApi, FamilyTree } from '../services/api';
import LoadingSpinner from '../components/UI/LoadingSpinner';
import CreateFamilyTreeModal from '../components/FamilyTree/CreateFamilyTreeModal';

const DashboardPage: React.FC = () => {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const queryClient = useQueryClient();

  const {
    data: familyTrees,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['familyTrees'],
    queryFn: familyTreesApi.getAll,
  });

  const deleteMutation = useMutation({
    mutationFn: familyTreesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['familyTrees'] });
    },
  });

  const handleDelete = async (id: string, name: string) => {
    if (window.confirm(`Are you sure you want to delete "${name}"? This action cannot be undone.`)) {
      try {
        await deleteMutation.mutateAsync(id);
      } catch (error) {
        console.error('Failed to delete family tree:', error);
      }
    }
  };

  const handleCreateSuccess = () => {
    setIsCreateModalOpen(false);
    queryClient.invalidateQueries({ queryKey: ['familyTrees'] });
  };

  if (isLoading) {
    return <LoadingSpinner className="min-h-screen" />;
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Error Loading Family Trees</h2>
          <p className="text-gray-600">Please try refreshing the page.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between mb-8">
        <div className="flex-1 min-w-0">
          <h1 className="text-3xl font-bold text-gray-900">Your Family Trees</h1>
          <p className="mt-2 text-gray-600">
            Create and manage your family history
          </p>
        </div>
        <div className="mt-4 md:mt-0">
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="btn-primary flex items-center"
          >
            <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create Family Tree
          </button>
        </div>
      </div>

      {/* Family Trees Grid */}
      {familyTrees && familyTrees.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {familyTrees.map((tree: FamilyTree) => (
            <div
              key={tree.id}
              className="bg-white rounded-lg shadow-md border border-gray-200 hover:shadow-lg transition-shadow duration-200"
            >
              <div className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {tree.name}
                    </h3>
                    {tree.description && (
                      <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                        {tree.description}
                      </p>
                    )}
                    <p className="text-xs text-gray-500">
                      Created {new Date(tree.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  
                  {/* Actions dropdown */}
                  <div className="relative ml-4">
                    <button
                      onClick={() => handleDelete(tree.id, tree.name)}
                      className="text-gray-400 hover:text-red-600 transition-colors"
                      title="Delete family tree"
                    >
                      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>

                <div className="mt-6 flex space-x-3">
                  <Link
                    to={`/family-tree/${tree.id}`}
                    className="flex-1 btn-primary text-center"
                  >
                    View Tree
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Empty state */
        <div className="text-center py-12">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No family trees</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by creating your first family tree.
          </p>
          <div className="mt-6">
            <button
              onClick={() => setIsCreateModalOpen(true)}
              className="btn-primary"
            >
              Create Family Tree
            </button>
          </div>
        </div>
      )}

      {/* Create Family Tree Modal */}
      <CreateFamilyTreeModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={handleCreateSuccess}
      />
    </div>
  );
};

export default DashboardPage;