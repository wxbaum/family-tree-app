import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { relationshipsApi, peopleApi, Person, Relationship } from '../../services/api';
import LoadingSpinner from '../UI/LoadingSpinner';
import EditRelationshipModal from '../Relationship/EditRelationshipModal';
import AddRelationshipModal from '../Relationship/AddRelationshipModal';

interface PersonRelationshipsSectionProps {
  person: Person;
}

interface RelationshipWithPerson {
  relationship: Relationship;
  otherPerson: Person;
  isFromPerson: boolean; // true if person is the "from" person in the relationship
}

const PersonRelationshipsSection: React.FC<PersonRelationshipsSectionProps> = ({ person }) => {
  const [editingRelationship, setEditingRelationship] = useState<Relationship | null>(null);
  const [isAddRelationshipOpen, setIsAddRelationshipOpen] = useState(false);
  const queryClient = useQueryClient();

  // Get all relationships for this person using the proper API endpoint
  const {
    data: relationships,
    isLoading: isLoadingRelationships,
  } = useQuery({
    queryKey: ['personRelationships', person.id],
    queryFn: () => relationshipsApi.getByPerson(person.id),
  });

  // Get details for all people involved in relationships
  const {
    data: relationshipsWithPeople,
    isLoading: isLoadingPeople,
  } = useQuery({
    queryKey: ['personRelationshipsWithPeople', person.id],
    queryFn: async (): Promise<RelationshipWithPerson[]> => {
      if (!relationships || relationships.length === 0) return [];
      
      const results: RelationshipWithPerson[] = [];
      
      for (const relationship of relationships) {
        const otherPersonId = relationship.from_person_id === person.id 
          ? relationship.to_person_id 
          : relationship.from_person_id;
        
        const otherPerson = await peopleApi.getById(otherPersonId);
        
        results.push({
          relationship,
          otherPerson,
          isFromPerson: relationship.from_person_id === person.id,
        });
      }
      
      return results;
    },
    enabled: !!relationships && relationships.length > 0,
  });

  const deleteMutation = useMutation({
    mutationFn: relationshipsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['personRelationships', person.id] });
      queryClient.invalidateQueries({ queryKey: ['personRelationshipsWithPeople', person.id] });
      queryClient.invalidateQueries({ queryKey: ['familyTreeGraph', person.family_tree_id] });
    },
    onError: (error) => {
      console.error('Failed to delete relationship:', error);
      alert('Failed to delete relationship. Please try again.');
    },
  });

  const handleDeleteRelationship = (relationship: Relationship, otherPersonName: string) => {
    if (window.confirm(`Are you sure you want to delete the relationship with ${otherPersonName}?`)) {
      deleteMutation.mutate(relationship.id);
    }
  };

  const handleEditSuccess = () => {
    setEditingRelationship(null);
    // Refresh relationship data
    queryClient.invalidateQueries({ queryKey: ['personRelationships', person.id] });
    queryClient.invalidateQueries({ queryKey: ['personRelationshipsWithPeople', person.id] });
    queryClient.invalidateQueries({ queryKey: ['familyTreeGraph', person.family_tree_id] });
  };

  const handleAddRelationshipSuccess = () => {
    setIsAddRelationshipOpen(false);
    // Refresh relationship data
    queryClient.invalidateQueries({ queryKey: ['personRelationships', person.id] });
    queryClient.invalidateQueries({ queryKey: ['personRelationshipsWithPeople', person.id] });
    queryClient.invalidateQueries({ queryKey: ['familyTreeGraph', person.family_tree_id] });
  };

  // Helper to get relationship display info
  const getRelationshipDisplay = (rel: RelationshipWithPerson) => {
    const { relationship, otherPerson, isFromPerson } = rel;
    
    // Get the relationship color for consistency with family tree
    const getRelationshipColor = (type: string): string => {
      const colors: Record<string, string> = {
        partner: '#ef4444',
        parent: '#3b82f6',
        child: '#3b82f6',
        sibling: '#f59e0b',
        adopted_parent: '#10b981',
        adopted_child: '#10b981',
      };
      return colors[type] || '#6b7280';
    };

    // Get the relationship description from the current person's perspective
    const getDescription = () => {
      const type = relationship.relationship_type;
      
      switch (type) {
        case 'partner':
          return 'Partner/Spouse';
        case 'parent':
          return isFromPerson ? 'Child' : 'Parent';
        case 'child':
          return isFromPerson ? 'Parent' : 'Child';
        case 'sibling':
          return 'Sibling';
        case 'adopted_parent':
          return isFromPerson ? 'Adopted Child' : 'Adoptive Parent';
        case 'adopted_child':
          return isFromPerson ? 'Adoptive Parent' : 'Adopted Child';
        default:
          return type;
      }
    };

    // Get emoji for relationship type
    const getEmoji = () => {
      const type = relationship.relationship_type;
      switch (type) {
        case 'partner': return '❤️';
        case 'parent': case 'child': return '👨‍👩‍👧‍👦';
        case 'sibling': return '👫';
        case 'adopted_parent': case 'adopted_child': return '👨‍👩‍👧‍👦✨';
        default: return '👥';
      }
    };

    return {
      description: getDescription(),
      color: getRelationshipColor(relationship.relationship_type),
      emoji: getEmoji(),
    };
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return null;
    return new Date(dateString).toLocaleDateString();
  };

  const isLoading = isLoadingRelationships || isLoadingPeople;

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <h2 className="text-xl font-bold text-gray-900">Relationships</h2>
          {relationshipsWithPeople && relationshipsWithPeople.length > 0 && (
            <span className="bg-gray-100 text-gray-800 text-sm font-medium px-2.5 py-0.5 rounded-full">
              {relationshipsWithPeople.length}
            </span>
          )}
        </div>
        <button
          onClick={() => setIsAddRelationshipOpen(true)}
          className="btn-primary"
        >
          <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Relationship
        </button>
      </div>

      {isLoading ? (
        <LoadingSpinner />
      ) : relationshipsWithPeople && relationshipsWithPeople.length > 0 ? (
        <div className="space-y-4">
          {relationshipsWithPeople.map((rel) => {
            const display = getRelationshipDisplay(rel);
            const { relationship, otherPerson } = rel;
            
            return (
              <div
                key={relationship.id}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4 flex-1">
                    {/* Relationship indicator */}
                    <div className="flex items-center space-x-2">
                      <div
                        className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium"
                        style={{ backgroundColor: display.color }}
                      >
                        {display.emoji}
                      </div>
                    </div>

                    {/* Relationship details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="text-sm font-medium" style={{ color: display.color }}>
                          {display.description}
                        </span>
                        {!relationship.is_active && (
                          <span className="bg-red-100 text-red-800 text-xs font-medium px-2 py-0.5 rounded-full">
                            Inactive
                          </span>
                        )}
                      </div>
                      
                      <Link
                        to={`/person/${otherPerson.id}`}
                        className="text-lg font-semibold text-gray-900 hover:text-primary-600 transition-colors"
                      >
                        {otherPerson.full_name}
                      </Link>
                      
                      {/* Dates */}
                      {(relationship.start_date || relationship.end_date) && (
                        <div className="text-sm text-gray-600 mt-1">
                          {relationship.start_date && (
                            <span>Started: {formatDate(relationship.start_date)}</span>
                          )}
                          {relationship.start_date && relationship.end_date && (
                            <span className="mx-2">•</span>
                          )}
                          {relationship.end_date && (
                            <span>Ended: {formatDate(relationship.end_date)}</span>
                          )}
                        </div>
                      )}

                      {/* Notes */}
                      {relationship.notes && (
                        <p className="text-sm text-gray-600 mt-1 italic">
                          "{relationship.notes}"
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Action buttons - Re-enabled */}
                  <div className="flex space-x-2 ml-4">
                    <button
                      onClick={() => setEditingRelationship(relationship)}
                      className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded transition-colors"
                      disabled={deleteMutation.isPending}
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteRelationship(relationship, otherPerson.full_name)}
                      className="text-xs text-red-600 hover:text-red-800 transition-colors px-2 py-1"
                      disabled={deleteMutation.isPending}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-8">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No relationships</h3>
          <p className="mt-1 text-sm text-gray-500">
            Connect {person.first_name} to family members by adding relationships.
          </p>
          <div className="mt-6">
            <button
              onClick={() => setIsAddRelationshipOpen(true)}
              className="btn-primary"
            >
              Add First Relationship
            </button>
          </div>
        </div>
      )}

      {/* Edit Relationship Modal */}
      {editingRelationship && (
        <EditRelationshipModal
          isOpen={!!editingRelationship}
          onClose={() => setEditingRelationship(null)}
          onSuccess={handleEditSuccess}
          relationship={editingRelationship}
          currentPersonId={person.id}
        />
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