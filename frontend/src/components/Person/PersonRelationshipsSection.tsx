// frontend/src/components/Person/PersonRelationshipsSection.tsx

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { relationshipsApi, Person, RelationshipDisplay, RelationshipCategory } from '../../services/api';
import LoadingSpinner from '../UI/LoadingSpinner';
import AddRelationshipModal from '../Relationship/AddRelationshipModal';

interface PersonRelationshipsSectionProps {
  person: Person;
}

const PersonRelationshipsSection: React.FC<PersonRelationshipsSectionProps> = ({ person }) => {
  const [isAddRelationshipOpen, setIsAddRelationshipOpen] = useState(false);
  const queryClient = useQueryClient();

  // Get relationships with display formatting
  const {
    data: relationships,
    isLoading: isLoadingRelationships,
  } = useQuery({
    queryKey: ['personRelationshipsDisplay', person.id],
    queryFn: () => relationshipsApi.getByPersonDisplay(person.id),
  });

  // Delete relationship mutation
  const deleteMutation = useMutation({
    mutationFn: relationshipsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['personRelationshipsDisplay', person.id] });
      queryClient.invalidateQueries({ queryKey: ['familyTreeGraph', person.family_tree_id] });
    },
    onError: (error) => {
      console.error('Failed to delete relationship:', error);
      alert('Failed to delete relationship. Please try again.');
    },
  });

  const handleDeleteRelationship = (relationship: RelationshipDisplay) => {
    if (window.confirm(`Are you sure you want to delete the relationship with ${relationship.other_person_name}?`)) {
      deleteMutation.mutate(relationship.id);
    }
  };

  const handleAddRelationshipSuccess = () => {
    setIsAddRelationshipOpen(false);
    // Refresh relationship data
    queryClient.invalidateQueries({ queryKey: ['personRelationshipsDisplay', person.id] });
    queryClient.invalidateQueries({ queryKey: ['familyTreeGraph', person.family_tree_id] });
  };

  // Helper to get relationship color for consistency
  const getRelationshipColor = (category: RelationshipCategory): string => {
    const colors: Record<RelationshipCategory, string> = {
      family_line: '#3b82f6',     // Blue
      partner: '#ef4444',         // Red
      sibling: '#f59e0b',         // Amber
      extended_family: '#10b981', // Emerald
    };
    return colors[category] || '#6b7280';
  };

  // Helper to get relationship icon
  const getRelationshipIcon = (category: RelationshipCategory) => {
    switch (category) {
      case 'family_line':
        return (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
          </svg>
        );
      case 'partner':
        return (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
          </svg>
        );
      case 'sibling':
        return (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        );
      case 'extended_family':
        return (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        );
      default:
        return (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
        );
    }
  };

  // Group relationships by category for better organization
  const groupedRelationships = relationships?.reduce((groups, rel) => {
    const category = rel.relationship_category;
    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push(rel);
    return groups;
  }, {} as Record<RelationshipCategory, RelationshipDisplay[]>) || {};

  // Category display names
  const categoryNames: Record<RelationshipCategory, string> = {
    family_line: 'Family Line',
    partner: 'Partners',
    sibling: 'Siblings',
    extended_family: 'Extended Family',
  };

  if (isLoadingRelationships) {
    return <LoadingSpinner />;
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-medium text-gray-900">Family Relationships</h2>
        <button
          onClick={() => setIsAddRelationshipOpen(true)}
          className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <svg className="-ml-0.5 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Add Relationship
        </button>
      </div>

      {!relationships || relationships.length === 0 ? (
        <div className="text-center py-8">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No relationships</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by adding a family relationship.
          </p>
          <div className="mt-6">
            <button
              onClick={() => setIsAddRelationshipOpen(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <svg className="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Add First Relationship
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedRelationships).map(([category, categoryRelationships]) => (
            <div key={category} className="space-y-3">
              <h3 className="text-sm font-medium text-gray-900 flex items-center">
                <span 
                  className="inline-flex items-center justify-center w-5 h-5 rounded-full mr-2"
                  style={{ backgroundColor: getRelationshipColor(category as RelationshipCategory) }}
                >
                  <span className="text-white text-xs">
                    {getRelationshipIcon(category as RelationshipCategory)}
                  </span>
                </span>
                {categoryNames[category as RelationshipCategory]} ({(categoryRelationships as RelationshipDisplay[]).length})
              </h3>
              
              <div className="grid gap-3">
                {(categoryRelationships as RelationshipDisplay[]).map((rel: RelationshipDisplay) => (
                  <div
                    key={rel.id}
                    className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                  >
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <Link
                          to={`/person/${rel.other_person_id}`}
                          className="text-sm font-medium text-primary-600 hover:text-primary-700"
                        >
                          {rel.other_person_name}
                        </Link>
                        <span className="text-sm text-gray-500">•</span>
                        <span className="text-sm text-gray-700">
                          {rel.description}
                          {rel.relationship_subtype && (
                            <span className="text-gray-500"> ({rel.relationship_subtype})</span>
                          )}
                        </span>
                        {!rel.is_active && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                            Inactive
                          </span>
                        )}
                      </div>
                      
                      {(rel.start_date || rel.end_date || rel.notes) && (
                        <div className="mt-1 text-xs text-gray-500 space-y-1">
                          {rel.start_date && (
                            <div>Started: {new Date(rel.start_date).toLocaleDateString()}</div>
                          )}
                          {rel.end_date && (
                            <div>Ended: {new Date(rel.end_date).toLocaleDateString()}</div>
                          )}
                          {rel.notes && (
                            <div>Notes: {rel.notes}</div>
                          )}
                        </div>
                      )}
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleDeleteRelationship(rel)}
                        className="text-red-600 hover:text-red-700 p-1 rounded"
                        title="Delete relationship"
                      >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Relationship Modal */}
      <AddRelationshipModal
        isOpen={isAddRelationshipOpen}
        onClose={() => setIsAddRelationshipOpen(false)}
        onSuccess={handleAddRelationshipSuccess}
        familyTreeId={person.family_tree_id}
        preselectedPersonId={person.id}
      />
    </div>
  );
};

export default PersonRelationshipsSection;