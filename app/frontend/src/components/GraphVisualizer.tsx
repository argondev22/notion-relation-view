import React, { useRef, useCallback, useEffect, useState } from "react";
import ForceGraph2D from "react-force-graph";
import { GraphData, Node, Edge } from "../types";

interface GraphVisualizerProps {
  data: GraphData;
  onNodeClick?: (node: Node) => void;
  onNodeDrag?: (node: Node, translate: { x: number; y: number }) => void;
  onZoom?: (zoom: number) => void;
  onPan?: (pan: { x: number; y: number }) => void;
  initialZoom?: number;
  initialPan?: { x: number; y: number };
}

interface ForceGraphNode {
  id: string;
  title: string;
  databaseId: string;
  x?: number;
  y?: number;
  visible: boolean;
}

interface ForceGraphLink {
  source: string;
  target: string;
  id: string;
  relationProperty: string;
  visible: boolean;
}

const GraphVisualizer: React.FC<GraphVisualizerProps> = ({
  data,
  onNodeClick,
  onNodeDrag,
  onZoom,
  onPan,
  initialZoom = 1,
  initialPan = { x: 0, y: 0 },
}) => {
  const graphRef = useRef<any>();
  const [graphData, setGraphData] = useState<{
    nodes: ForceGraphNode[];
    links: ForceGraphLink[];
  }>({ nodes: [], links: [] });

  // Transform data for react-force-graph
  useEffect(() => {
    const nodes: ForceGraphNode[] = data.nodes
      .filter((node) => node.visible)
      .map((node) => ({
        id: node.id,
        title: node.title,
        databaseId: node.databaseId,
        x: node.x || undefined,
        y: node.y || undefined,
        visible: node.visible,
      }));

    const links: ForceGraphLink[] = data.edges
      .filter((edge) => edge.visible)
      .map((edge) => ({
        source: edge.sourceId,
        target: edge.targetId,
        id: edge.id,
        relationProperty: edge.relationProperty,
        visible: edge.visible,
      }));

    setGraphData({ nodes, links });
  }, [data]);

  // Set initial zoom and pan
  useEffect(() => {
    if (graphRef.current) {
      graphRef.current.zoom(initialZoom);
      graphRef.current.centerAt(initialPan.x, initialPan.y, 0);
    }
  }, [initialZoom, initialPan]);

  const handleNodeClick = useCallback(
    (node: any) => {
      if (onNodeClick) {
        const originalNode = data.nodes.find((n) => n.id === node.id);
        if (originalNode) {
          onNodeClick(originalNode);
        }
      }
    },
    [data.nodes, onNodeClick]
  );

  const handleNodeDrag = useCallback(
    (node: any) => {
      if (onNodeDrag) {
        const originalNode = data.nodes.find((n) => n.id === node.id);
        if (originalNode) {
          onNodeDrag(originalNode, { x: node.x, y: node.y });
        }
      }
    },
    [data.nodes, onNodeDrag]
  );

  const handleZoom = useCallback(
    (zoom: number) => {
      if (onZoom) {
        onZoom(zoom);
      }
    },
    [onZoom]
  );

  const nodeCanvasObject = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const label = node.title;
    const fontSize = 12 / globalScale;
    ctx.font = `${fontSize}px Sans-Serif`;

    // Draw node circle
    ctx.beginPath();
    ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI, false);
    ctx.fillStyle = "#646cff";
    ctx.fill();

    // Draw label
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillStyle = "#ffffff";
    ctx.fillText(label, node.x, node.y + 10);
  }, []);

  const linkCanvasObject = useCallback((link: any, ctx: CanvasRenderingContext2D) => {
    ctx.beginPath();
    ctx.moveTo(link.source.x, link.source.y);
    ctx.lineTo(link.target.x, link.target.y);
    ctx.strokeStyle = "#666";
    ctx.lineWidth = 1;
    ctx.stroke();
  }, []);

  return (
    <div className="graph-visualizer">
      <ForceGraph2D
        ref={graphRef}
        graphData={graphData}
        nodeLabel="title"
        nodeCanvasObject={nodeCanvasObject}
        linkCanvasObject={linkCanvasObject}
        onNodeClick={handleNodeClick}
        onNodeDragEnd={handleNodeDrag}
        onZoom={handleZoom}
        enableNodeDrag={true}
        enableZoomInteraction={true}
        enablePanInteraction={true}
        cooldownTicks={100}
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.3}
      />
    </div>
  );
};

export default GraphVisualizer;
