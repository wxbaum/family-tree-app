import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { familyTreesApi, peopleApi } from '../services/api';
import LoadingSpinner from '../components/UI/LoadingSpinner';
import FamilyTreeVisualization from '../components/FamilyTree/FamilyTreeVisualization';
import AddPersonModal from '../components/Person/AddPersonModal';
import AddRelationshipModal from '../components/Relationship/AddRelationshipModal';

const FamilyTreePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [isAddPersonModalOpen, setIsAddPersonModalOpen] = useState(false);
  const [isAddRelationshipModalOpen, setIsAddRelationshipModalOpen] = useState(false);
  const queryClient = useQueryClient();

  const {
    data: familyTree,
    isLoading: isLoadingTree,
    error: treeError,
  } = useQuery({
    queryKey: ['familyTree', id],
    queryFn: () => familyTreesApi.getById(id!),
    enabled: !!id,
  });

  const {
    data: graphData,
    isLoading: isLoadingGraph,
    error: graphError,
  } = useQuery({
    queryKey: ['familyTreeGraph', id],
    queryFn: () => familyTreesApi.getGraph(id!),
    enabled: !!id,
  });

  const {
    data: people,
    isLoading: isLoadingPeople,
  } = useQuery({
    queryKey: ['familyTreePeople', id],
    queryFn: () => peopleApi.getByFamilyTree(id!),
    enabled: !!id,
  });

  const handleAddPersonSuccess = () => {
    setIsAddPersonModalOpen(false);
    // Refresh the graph data to show new person
    queryClient.invalidateQueries({ queryKey: ['familyTreeGraph', id] });
    // Also refresh any people queries
    queryClient.invalidateQueries({ queryKey: ['familyTreePeople', id] });
    // Force a refetch of the graph data immediately
    queryClient.refetchQueries({ queryKey: ['familyTreeGraph', id] });
  };

  const handleAddRelationshipSuccess = () => {
    setIsAddRelationshipModalOpen(false);
    // Refresh the graph data to show new relationship
    queryClient.invalidateQueries({ queryKey: ['familyTreeGraph', id] });
    queryClient.refetchQueries({ queryKey: ['familyTreeGraph', id] });
  };

  // Handle the case where id is not available
  if (!id) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Family Tree Not Found</h2>
          <Link to="/dashboard" className="btn-primary">
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  if (isLoadingTree || isLoadingGraph) {
    return <LoadingSpinner className="min-h-screen" />;
  }

  if (treeError || graphError) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Error Loading Family Tree</h2>
          <p className="text-gray-600 mb-4">Please try refreshing the page.</p>
          <Link to="/dashboard" className="btn-primary">
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link
              to="/dashboard"
              className="text-gray-500 hover:text-gray-700 transition-colors"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {familyTree?.name}
              </h1>
              {familyTree?.description && (
                <p className="text-gray-600 text-sm">{familyTree.description}</p>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="text-sm text-gray-500">
              {people?.length || 0} {people?.length === 1 ? 'person' : 'people'}
            </div>
            <button
              onClick={() => setIsAddPersonModalOpen(true)}
              className="btn-primary flex items-center"
            >
              <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add Person
            </button>
            {people && people.length >= 2 && (
              <button
                onClick={() => setIsAddRelationshipModalOpen(true)}
                className="btn-secondary flex items-center"
              >
                <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
                Add Relationship
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Family Tree Visualization */}
      <div className="flex-1 bg-gray-50">
        {graphData && graphData.nodes.length > 0 ? (
          <FamilyTreeVisualization
            familyTreeId={id}
          />
        ) : (
          /* Empty state */
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No family members yet</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by adding the first person to your family tree.
              </p>
              <div className="mt-6">
                <button
                  onClick={() => setIsAddPersonModalOpen(true)}
                  className="btn-primary mr-3"
                >
                  Add First Person
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Add Person Modal */}
      <AddPersonModal
        isOpen={isAddPersonModalOpen}
        onClose={() => setIsAddPersonModalOpen(false)}
        onSuccess={handleAddPersonSuccess}
        familyTreeId={id}
      />

      {/* Add Relationship Modal */}
      <AddRelationshipModal
        isOpen={isAddRelationshipModalOpen}
        onClose={() => setIsAddRelationshipModalOpen(false)}
        onSuccess={handleAddRelationshipSuccess}
        familyTreeId={id}
      />
    </div>
  );
};

export default FamilyTreePage;