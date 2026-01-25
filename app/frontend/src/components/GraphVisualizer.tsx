import React, { useRef, useCallback, useEffect, useState, useMemo } from "react";
import ForceGraph2D from "react-force-graph-2d";
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

interface PerformanceMetrics {
  fps: number;
  renderTime: number;
  nodeCount: number;
  edgeCount: number;
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
  const [currentZoom, setCurrentZoom] = useState<number>(initialZoom);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics>({
    fps: 60,
    renderTime: 0,
    nodeCount: 0,
    edgeCount: 0,
  });

  // Performance monitoring
  const lastFrameTime = useRef<number>(Date.now());
  const frameCount = useRef<number>(0);
  const fpsUpdateInterval = useRef<number | null>(null);

  // Level of Detail (LOD) thresholds
  const LOD_THRESHOLDS = {
    HIGH_DETAIL: 2.0,    // Show all details when zoomed in
    MEDIUM_DETAIL: 0.5,  // Show simplified details
    LOW_DETAIL: 0.2,     // Show minimal details when zoomed out
  };

  // Determine current LOD based on zoom level
  const currentLOD = useMemo(() => {
    if (currentZoom >= LOD_THRESHOLDS.HIGH_DETAIL) return 'high';
    if (currentZoom >= LOD_THRESHOLDS.MEDIUM_DETAIL) return 'medium';
    return 'low';
  }, [currentZoom]);

  // Memoize visible nodes and edges to avoid unnecessary recalculations
  const visibleGraphData = useMemo(() => {
    const startTime = performance.now();

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

    const renderTime = performance.now() - startTime;

    setPerformanceMetrics(prev => ({
      ...prev,
      renderTime,
      nodeCount: nodes.length,
      edgeCount: links.length,
    }));

    return { nodes, links };
  }, [data.nodes, data.edges]);

  // Transform data for react-force-graph with lazy loading
  useEffect(() => {
    setGraphData(visibleGraphData);
  }, [visibleGraphData]);

  // Set initial zoom and pan
  useEffect(() => {
    if (graphRef.current) {
      graphRef.current.zoom(initialZoom);
      graphRef.current.centerAt(initialPan.x, initialPan.y, 0);
      setCurrentZoom(initialZoom);
    }
  }, [initialZoom, initialPan]);

  // FPS monitoring
  useEffect(() => {
    fpsUpdateInterval.current = window.setInterval(() => {
      const now = Date.now();
      const elapsed = now - lastFrameTime.current;
      const fps = Math.round((frameCount.current * 1000) / elapsed);

      setPerformanceMetrics(prev => ({ ...prev, fps }));

      frameCount.current = 0;
      lastFrameTime.current = now;
    }, 1000);

    return () => {
      if (fpsUpdateInterval.current) {
        clearInterval(fpsUpdateInterval.current);
      }
    };
  }, []);

  // Track frame rendering
  const trackFrame = useCallback(() => {
    frameCount.current++;
  }, []);

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
      setCurrentZoom(zoom);
      if (onZoom) {
        onZoom(zoom);
      }
    },
    [onZoom]
  );

  // Optimized node rendering with LOD
  const nodeCanvasObject = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    trackFrame();

    const label = node.title;
    const nodeRadius = 5;

    // Draw node circle
    ctx.beginPath();
    ctx.arc(node.x, node.y, nodeRadius, 0, 2 * Math.PI, false);
    ctx.fillStyle = "#646cff";
    ctx.fill();

    // LOD-based label rendering
    if (currentLOD === 'high') {
      // High detail: Show all labels with full quality
      const fontSize = 12 / globalScale;
      ctx.font = `${fontSize}px Sans-Serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillStyle = "#ffffff";
      ctx.fillText(label, node.x, node.y + 10);
    } else if (currentLOD === 'medium') {
      // Medium detail: Show labels only for nodes with few connections or when zoomed moderately
      if (globalScale > 0.5) {
        const fontSize = 10 / globalScale;
        ctx.font = `${fontSize}px Sans-Serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillStyle = "#ffffff";
        // Truncate long labels
        const maxLength = 20;
        const displayLabel = label.length > maxLength ? label.substring(0, maxLength) + '...' : label;
        ctx.fillText(displayLabel, node.x, node.y + 10);
      }
    }
    // Low detail: No labels, just nodes
  }, [currentLOD, trackFrame]);

  // Optimized link rendering with LOD
  const linkCanvasObject = useCallback((link: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    // Adjust line width based on zoom level
    const lineWidth = currentLOD === 'high' ? 1.5 : currentLOD === 'medium' ? 1 : 0.5;

    ctx.beginPath();
    ctx.moveTo(link.source.x, link.source.y);
    ctx.lineTo(link.target.x, link.target.y);
    ctx.strokeStyle = currentLOD === 'low' ? "#444" : "#666";
    ctx.lineWidth = lineWidth / globalScale;
    ctx.stroke();
  }, [currentLOD]);

  return (
    <div className="graph-visualizer" style={{ position: 'relative', width: '100%', height: '100%' }}>
      {/* Performance metrics overlay (only in development) */}
      {process.env.NODE_ENV === 'development' && (
        <div style={{
          position: 'absolute',
          top: 10,
          right: 10,
          background: 'rgba(0, 0, 0, 0.7)',
          color: 'white',
          padding: '10px',
          borderRadius: '5px',
          fontSize: '12px',
          zIndex: 1000,
          fontFamily: 'monospace'
        }}>
          <div>FPS: {performanceMetrics.fps}</div>
          <div>Render: {performanceMetrics.renderTime.toFixed(2)}ms</div>
          <div>Nodes: {performanceMetrics.nodeCount}</div>
          <div>Edges: {performanceMetrics.edgeCount}</div>
          <div>LOD: {currentLOD}</div>
          <div>Zoom: {currentZoom.toFixed(2)}</div>
        </div>
      )}

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
        // Performance optimizations
        warmupTicks={0}
        cooldownTime={3000}
        // Reduce physics calculations for large graphs
        d3AlphaMin={0.001}
      />
    </div>
  );
};

export default GraphVisualizer;
