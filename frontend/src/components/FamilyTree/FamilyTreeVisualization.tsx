import React, { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  BackgroundVariant,
  NodeTypes,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { FamilyTreeGraph, peopleApi } from '../../services/api';
import PersonNode from './PersonNode';

interface FamilyTreeVisualizationProps {
  graphData: FamilyTreeGraph;
  familyTreeId: string;
}

const nodeTypes: NodeTypes = {
  person: PersonNode,
};

const FamilyTreeVisualization: React.FC<FamilyTreeVisualizationProps> = ({
  graphData,
  familyTreeId,
}) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: peopleApi.delete,
    onSuccess: () => {
      // Refresh the graph data after deletion
      queryClient.invalidateQueries({ queryKey: ['familyTreeGraph', familyTreeId] });
      queryClient.refetchQueries({ queryKey: ['familyTreeGraph', familyTreeId] });
    },
    onError: (error) => {
      console.error('Failed to delete person:', error);
      alert('Failed to delete person. Please try again.');
    },
  });

  const handleDeletePerson = (personId: string) => {
    deleteMutation.mutate(personId);
  };

  // Convert API data to React Flow format
  const createNodesFromData = (data: FamilyTreeGraph) => {
    return data.nodes.map((node, index) => ({
      id: node.id,
      type: 'person',
      position: { 
        x: (index % 4) * 300 + 100, 
        y: Math.floor(index / 4) * 200 + 100 
      },
      data: {
        person: node.data,
        onEdit: (personId: string) => navigate(`/person/${personId}`),
        onDelete: handleDeletePerson,
      },
    }));
  };

  const createEdgesFromData = (data: FamilyTreeGraph) => {
    return data.edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: 'smoothstep',
      label: edge.data.relationship_type,
      labelStyle: { fontSize: 12, fontWeight: 600 },
      style: { 
        strokeWidth: 2,
        stroke: getEdgeColor(edge.data.relationship_type),
      },
    }));
  };

  const [nodes, setNodes, onNodesChange] = useNodesState(createNodesFromData(graphData));
  const [edges, setEdges, onEdgesChange] = useEdgesState(createEdgesFromData(graphData));

  // Update nodes and edges when graphData changes
  useEffect(() => {
    setNodes(createNodesFromData(graphData));
    setEdges(createEdgesFromData(graphData));
  }, [graphData, setNodes, setEdges]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
      >
        <Controls />
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
      </ReactFlow>
    </div>
  );
};

function getEdgeColor(relationshipType: string): string {
  switch (relationshipType) {
    case 'spouse':
      return '#ef4444'; // red
    case 'parent':
    case 'child':
      return '#3b82f6'; // blue
    case 'adopted_parent':
    case 'adopted_child':
      return '#10b981'; // green
    default:
      return '#6b7280'; // gray
  }
}

export default FamilyTreeVisualization;