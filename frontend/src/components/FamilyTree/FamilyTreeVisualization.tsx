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

// ENHANCED FOR PHASE 1 - Comprehensive edge styling configuration
function getEdgeStyleConfig(relationshipType: string) {
  const configs: { [key: string]: any } = {
    partner: {
      color: '#ef4444', // red
      strokeWidth: 3,
      strokeDasharray: 'none',
      label: '❤️',
      labelBgColor: '#fef2f2',
      labelBorderColor: '#ef4444'
    },
    parent: {
      color: '#3b82f6', // blue
      strokeWidth: 2,
      strokeDasharray: 'none',
      label: '👨‍👩‍👧‍👦',
      labelBgColor: '#eff6ff',
      labelBorderColor: '#3b82f6'
    },
    child: {
      color: '#3b82f6', // blue
      strokeWidth: 2,
      strokeDasharray: 'none',
      label: '🧒',
      labelBgColor: '#eff6ff',
      labelBorderColor: '#3b82f6'
    },
    sibling: {
      color: '#f59e0b', // amber/orange
      strokeWidth: 2,
      strokeDasharray: '5,5',
      label: '👫',
      labelBgColor: '#fffbeb',
      labelBorderColor: '#f59e0b'
    },
    adopted_parent: {
      color: '#10b981', // green
      strokeWidth: 2,
      strokeDasharray: '3,3',
      label: '👨‍👩‍👧‍👦✨',
      labelBgColor: '#f0fdf4',
      labelBorderColor: '#10b981'
    },
    adopted_child: {
      color: '#10b981', // green
      strokeWidth: 2,
      strokeDasharray: '3,3',
      label: '🧒✨',
      labelBgColor: '#f0fdf4',
      labelBorderColor: '#10b981'
    }
  };

  return configs[relationshipType] || {
    color: '#6b7280', // gray
    strokeWidth: 1,
    strokeDasharray: 'none',
    label: '?',
    labelBgColor: '#f9fafb',
    labelBorderColor: '#6b7280'
  };
}

// ENHANCED FOR PHASE 1 - Better edge color function (backwards compatible)
function getEdgeColor(relationshipType: string): string {
  return getEdgeStyleConfig(relationshipType).color;
}

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

  // ENHANCED FOR PHASE 1 - Improved node positioning with better spacing
  const createNodesFromData = (data: FamilyTreeGraph) => {
    return data.nodes.map((node, index) => {
      // Enhanced grid layout with more spacing for better visualization
      const cols = Math.ceil(Math.sqrt(data.nodes.length));
      const row = Math.floor(index / cols);
      const col = index % cols;
      
      return {
        id: node.id,
        type: 'person',
        position: { 
          x: col * 350 + 100, // Increased horizontal spacing
          y: row * 250 + 100  // Increased vertical spacing
        },
        data: {
          person: node.data,
          onEdit: (personId: string) => navigate(`/person/${personId}`),
          onDelete: handleDeletePerson,
        },
      };
    });
  };

  // ENHANCED FOR PHASE 1 - Comprehensive edge styling
  const createEdgesFromData = (data: FamilyTreeGraph) => {
    return data.edges.map((edge) => {
      const styleConfig = getEdgeStyleConfig(edge.data.relationship_type);
      
      return {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: 'smoothstep',
        label: styleConfig.label,
        labelStyle: { 
          fontSize: 12, 
          fontWeight: 600,
        },
        style: { 
          strokeWidth: styleConfig.strokeWidth,
          stroke: styleConfig.color,
          strokeDasharray: styleConfig.strokeDasharray,
        },
      };
    });
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

export default FamilyTreeVisualization;