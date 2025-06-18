// frontend/src/components/FamilyTree/FamilyTreeVisualization.tsx

import React, { useCallback, useEffect, useState } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
  BackgroundVariant,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { useQuery } from '@tanstack/react-query';
import { familyTreesApi, Person, RelationshipCategory } from '../../services/api';
import PersonNode from './PersonNode';
import AddPersonModal from '../Person/AddPersonModal';
import LoadingSpinner from '../UI/LoadingSpinner';

const nodeTypes = {
  person: PersonNode,
};

interface FamilyTreeVisualizationProps {
  familyTreeId: string;
}

// Enhanced edge styling for new relationship categories
const getEdgeStyleConfig = (category: RelationshipCategory) => {
  const configs = {
    family_line: {
      stroke: '#3b82f6',
      strokeWidth: 3,
      label: 'Family',
      labelBgStyle: { fill: '#3b82f6', color: 'white', fillOpacity: 0.8 },
      labelStyle: { fill: 'white', fontWeight: 600 },
      style: {},
    },
    partner: {
      stroke: '#ef4444',
      strokeWidth: 4,
      label: 'Partner',
      labelBgStyle: { fill: '#ef4444', color: 'white', fillOpacity: 0.8 },
      labelStyle: { fill: 'white', fontWeight: 600 },
      style: { strokeDasharray: '0' }, // Solid line for partners
    },
    sibling: {
      stroke: '#f59e0b',
      strokeWidth: 2,
      label: 'Sibling',
      labelBgStyle: { fill: '#f59e0b', color: 'white', fillOpacity: 0.8 },
      labelStyle: { fill: 'white', fontWeight: 600 },
      style: { strokeDasharray: '5,5' }, // Dashed line for siblings
    },
    extended_family: {
      stroke: '#10b981',
      strokeWidth: 2,
      label: 'Extended',
      labelBgStyle: { fill: '#10b981', color: 'white', fillOpacity: 0.8 },
      labelStyle: { fill: 'white', fontWeight: 600 },
      style: { strokeDasharray: '10,5' }, // Different dash pattern for extended family
    },
  };

  return configs[category] || {
    stroke: '#6b7280',
    strokeWidth: 2,
    label: 'Related',
    labelBgStyle: { fill: '#6b7280', color: 'white', fillOpacity: 0.8 },
    labelStyle: { fill: 'white', fontWeight: 600 },
    style: {},
  };
};

const FamilyTreeVisualization: React.FC<FamilyTreeVisualizationProps> = ({
  familyTreeId,
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isAddPersonModalOpen, setIsAddPersonModalOpen] = useState(false);

  // Fetch family tree graph data
  const {
    data: graphData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['familyTreeGraph', familyTreeId],
    queryFn: () => familyTreesApi.getGraph(familyTreeId),
    enabled: !!familyTreeId,
  });


  const createNodesFromData = useCallback((data: any) => {
    if (!data?.nodes) return [];

    return data.nodes.map((node: any, index: number) => ({
      id: node.id,
      type: 'person',
      position: {
        x: (index % 4) * 300 + 50, // Simple grid layout
        y: Math.floor(index / 4) * 200 + 50,
      },
      data: {
        person: node.data,
        onEdit: (personId: string) => {
          // Navigate to person detail page
          window.location.href = `/person/${personId}`;
        },
        onDelete: (personId: string) => {
          // Handle person deletion
          if (window.confirm('Are you sure you want to delete this person?')) {
            // You can implement delete logic here
            console.log('Delete person:', personId);
            refetch(); // Refresh the graph after deletion
          }
        },
        onUpdate: refetch, // Pass the refetch function
      },
    }));
  }, [refetch]);

  const createEdgesFromData = useCallback((data: any) => {
    if (!data?.edges) return [];

    return data.edges.map((edge: any) => {
      // Updated to use relationship_category instead of relationship_type
      const styleConfig = getEdgeStyleConfig(edge.data.relationship_category);
      
      // Create more detailed label based on relationship data
      let label = styleConfig.label;
      if (edge.data.relationship_subtype) {
        label += ` (${edge.data.relationship_subtype})`;
      }
      if (edge.data.relationship_category === 'family_line' && edge.data.generation_difference) {
        const genLabel = edge.data.generation_difference === -1 ? 'Parent' : 
                        edge.data.generation_difference === 1 ? 'Child' : 'Family';
        label = genLabel + (edge.data.relationship_subtype ? ` (${edge.data.relationship_subtype})` : '');
      }

      return {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label,
        style: {
          stroke: styleConfig.stroke,
          strokeWidth: styleConfig.strokeWidth,
          ...styleConfig.style,
        },
        labelStyle: styleConfig.labelStyle,
        labelBgStyle: styleConfig.labelBgStyle,
        animated: edge.data.relationship_category === 'partner', // Animate partner relationships
        type: edge.data.relationship_category === 'family_line' ? 'straight' : 'default',
      };
    });
  }, []);

  // Update nodes and edges when data changes
  useEffect(() => {
    if (graphData) {
      const newNodes = createNodesFromData(graphData);
      const newEdges = createEdgesFromData(graphData);
      
      setNodes(newNodes);
      setEdges(newEdges);
    }
  }, [graphData, createNodesFromData, createEdgesFromData, setNodes, setEdges]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const handleAddPersonSuccess = () => {
    setIsAddPersonModalOpen(false);
    refetch();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Error loading family tree
          </h3>
          <p className="text-gray-500 mb-4">
            {error instanceof Error ? error.message : 'Unknown error occurred'}
          </p>
          <button
            onClick={() => refetch()}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!graphData?.nodes || graphData.nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            No family members yet
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by adding the first person to your family tree.
          </p>
          <div className="mt-6">
            <button
              onClick={() => setIsAddPersonModalOpen(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <svg
                className="-ml-1 mr-2 h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                />
              </svg>
              Add First Person
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-96 bg-gray-50 rounded-lg overflow-hidden border">
      <div className="h-full relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          className="bg-gray-50"
          attributionPosition="bottom-left"
          fitView
          fitViewOptions={{
            padding: 0.2,
            minZoom: 0.5,
            maxZoom: 1.5,
          }}
        >
          <Controls 
            className="bg-white shadow-lg border rounded-lg"
            showInteractive={false}
          />
          <MiniMap 
            className="bg-white shadow-lg border rounded-lg"
            nodeColor={(node) => {
              return '#3b82f6';
            }}
            maskColor="rgba(255, 255, 255, 0.8)"
            pannable
            zoomable
          />
          <Background 
            variant={BackgroundVariant.Dots} 
            gap={20} 
            size={1}
            className="bg-gray-50"
          />
        </ReactFlow>

        {/* Add Person Button */}
        <div className="absolute top-4 right-4">
          <button
            onClick={() => setIsAddPersonModalOpen(true)}
            className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 shadow-lg"
          >
            <svg className="-ml-0.5 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Add Person
          </button>
        </div>

        {/* Relationship Legend */}
        <div className="absolute bottom-4 left-4 bg-white shadow-lg border rounded-lg p-3">
          <h4 className="text-xs font-medium text-gray-900 mb-2">Relationships</h4>
          <div className="space-y-1 text-xs">
            <div className="flex items-center space-x-2">
              <div className="w-4 h-0.5 bg-blue-500"></div>
              <span className="text-gray-600">Family Line</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-0.5 bg-red-500"></div>
              <span className="text-gray-600">Partner</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-0.5 bg-amber-500 border-dashed border-b-2 border-amber-500"></div>
              <span className="text-gray-600">Sibling</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-0.5 bg-emerald-500 border-dashed border-b-2 border-emerald-500"></div>
              <span className="text-gray-600">Extended Family</span>
            </div>
          </div>
        </div>
      </div>

      {/* Add Person Modal */}
      <AddPersonModal
        isOpen={isAddPersonModalOpen}
        onClose={() => setIsAddPersonModalOpen(false)}
        onSuccess={handleAddPersonSuccess}
        familyTreeId={familyTreeId}
      />
    </div>
  );
};

export default FamilyTreeVisualization;