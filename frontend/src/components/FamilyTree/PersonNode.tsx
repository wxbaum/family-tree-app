import React from 'react';
import { Handle, Position } from 'reactflow';
import { Person } from '../../services/api';

interface PersonNodeProps {
  data: {
    person: Person;
    onEdit: (personId: string) => void;
    onDelete?: (personId: string) => void;
  };
}

const PersonNode: React.FC<PersonNodeProps> = ({ data }) => {
  const { person, onEdit, onDelete } = data;

  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    return new Date(dateString).getFullYear();
  };

  const getLifeSpan = () => {
    const birth = formatDate(person.birth_date);
    const death = formatDate(person.death_date);
    
    if (birth && death) {
      return `${birth} - ${death}`;
    } else if (birth) {
      return `b. ${birth}`;
    } else if (death) {
      return `d. ${death}`;
    }
    return '';
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDelete && window.confirm(`Are you sure you want to delete ${person.full_name}?`)) {
      onDelete(person.id);
    }
  };

  const handleViewDetails = () => {
    onEdit(person.id);
  };

  return (
    <div className="bg-white rounded-lg border-2 border-gray-200 shadow-md hover:shadow-lg transition-shadow duration-200 min-w-[200px]">
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 !bg-blue-500 border-2 border-white"
      />
      
      <div className="p-4">
        {/* Delete button */}
        {onDelete && (
          <div className="flex justify-end mb-2">
            <button
              onClick={handleDelete}
              className="text-gray-400 hover:text-red-600 transition-colors p-1"
              title="Delete person"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        )}

        {/* Profile Photo */}
        <div className="flex justify-center mb-3">
          <div className="w-16 h-16 bg-gray-300 rounded-full flex items-center justify-center">
            {person.profile_photo_url ? (
              <img
                src={person.profile_photo_url}
                alt={person.full_name}
                className="w-full h-full rounded-full object-cover"
              />
            ) : (
              <svg className="w-8 h-8 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            )}
          </div>
        </div>

        {/* Name */}
        <div className="text-center mb-2">
          <h3 className="font-semibold text-gray-900 text-sm">
            {person.full_name}
          </h3>
          {person.maiden_name && (
            <p className="text-xs text-gray-600">
              (née {person.maiden_name})
            </p>
          )}
        </div>

        {/* Life Span */}
        {getLifeSpan() && (
          <div className="text-center mb-3">
            <p className="text-xs text-gray-600">{getLifeSpan()}</p>
          </div>
        )}

        {/* Places */}
        <div className="text-center space-y-1">
          {person.birth_place && (
            <p className="text-xs text-gray-600">
              📍 {person.birth_place}
            </p>
          )}
        </div>

        {/* Action Button */}
        <div className="mt-3 flex justify-center">
          <button
            onClick={handleViewDetails}
            className="text-xs bg-primary-600 hover:bg-primary-700 text-white px-3 py-1 rounded transition-colors"
          >
            View Details
          </button>
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 !bg-blue-500 border-2 border-white"
      />
    </div>
  );
};

export default PersonNode;