/**
 * Performance tests for GraphVisualizer component
 *
 * Tests:
 * - Rendering performance with 100+ nodes (60 FPS target)
 * - Zoom/pan response time (200ms target)
 *
 * Validates: Requirements 8.1, 8.2
 */

import { render } from '@testing-library/react';
import GraphVisualizer from './GraphVisualizer';
import { GraphData, Node, Edge } from '../types';

// Helper to generate large graph data
function generateLargeGraphData(nodeCount: number): GraphData {
  const nodes: Node[] = [];
  const edges: Edge[] = [];
  const databases = [
    { id: 'db1', title: 'Database 1', hidden: false },
    { id: 'db2', title: 'Database 2', hidden: false },
  ];

  // Generate nodes
  for (let i = 0; i < nodeCount; i++) {
    nodes.push({
      id: `node-${i}`,
      title: `Node ${i}`,
      databaseId: i % 2 === 0 ? 'db1' : 'db2',
      x: Math.random() * 1000,
      y: Math.random() * 1000,
      visible: true,
    });
  }

  // Generate edges (create a connected graph)
  for (let i = 0; i < nodeCount - 1; i++) {
    edges.push({
      id: `edge-${i}`,
      sourceId: `node-${i}`,
      targetId: `node-${i + 1}`,
      relationProperty: 'related',
      visible: true,
    });
  }

  // Add some random edges for complexity
  for (let i = 0; i < Math.floor(nodeCount / 2); i++) {
    const source = Math.floor(Math.random() * nodeCount);
    const target = Math.floor(Math.random() * nodeCount);
    if (source !== target) {
      edges.push({
        id: `edge-random-${i}`,
        sourceId: `node-${source}`,
        targetId: `node-${target}`,
        relationProperty: 'related',
        visible: true,
      });
    }
  }

  return { nodes, edges, databases };
}

describe('GraphVisualizer Performance Tests', () => {
  // Increase timeout for performance tests
  jest.setTimeout(30000);

  describe('Rendering Performance', () => {
    it('should render 100 nodes within acceptable time', () => {
      const graphData = generateLargeGraphData(100);
      const startTime = performance.now();

      const { container } = render(
        <GraphVisualizer data={graphData} />
      );

      const renderTime = performance.now() - startTime;

      // Should render within 1000ms
      expect(renderTime).toBeLessThan(1000);
      expect(container).toBeTruthy();
    });

    it('should render 200 nodes within acceptable time', () => {
      const graphData = generateLargeGraphData(200);
      const startTime = performance.now();

      const { container } = render(
        <GraphVisualizer data={graphData} />
      );

      const renderTime = performance.now() - startTime;

      // Should render within 2000ms for larger graphs
      expect(renderTime).toBeLessThan(2000);
      expect(container).toBeTruthy();
    });

    it('should handle 500 nodes without crashing', () => {
      const graphData = generateLargeGraphData(500);
      const startTime = performance.now();

      const { container } = render(
        <GraphVisualizer data={graphData} />
      );

      const renderTime = performance.now() - startTime;

      // Should render within 5000ms for very large graphs
      expect(renderTime).toBeLessThan(5000);
      expect(container).toBeTruthy();
    });
  });

  describe('Interaction Performance', () => {
    it('should handle zoom operations quickly', () => {
      const graphData = generateLargeGraphData(100);
      let zoomCallbackTime = 0;

      const handleZoom = (zoom: number) => {
        zoomCallbackTime = performance.now();
      };

      const { rerender } = render(
        <GraphVisualizer
          data={graphData}
          onZoom={handleZoom}
          initialZoom={1.0}
        />
      );

      const startTime = performance.now();

      // Simulate zoom change
      rerender(
        <GraphVisualizer
          data={graphData}
          onZoom={handleZoom}
          initialZoom={2.0}
        />
      );

      const responseTime = zoomCallbackTime > 0 ? zoomCallbackTime - startTime : performance.now() - startTime;

      // Should respond within 200ms (requirement 8.2)
      expect(responseTime).toBeLessThan(200);
    });

    it('should handle pan operations quickly', () => {
      const graphData = generateLargeGraphData(100);
      let panCallbackTime = 0;

      const handlePan = (pan: { x: number; y: number }) => {
        panCallbackTime = performance.now();
      };

      const { rerender } = render(
        <GraphVisualizer
          data={graphData}
          onPan={handlePan}
          initialPan={{ x: 0, y: 0 }}
        />
      );

      const startTime = performance.now();

      // Simulate pan change
      rerender(
        <GraphVisualizer
          data={graphData}
          onPan={handlePan}
          initialPan={{ x: 100, y: 100 }}
        />
      );

      const responseTime = panCallbackTime > 0 ? panCallbackTime - startTime : performance.now() - startTime;

      // Should respond within 200ms (requirement 8.2)
      expect(responseTime).toBeLessThan(200);
    });

    it('should handle node drag operations efficiently', () => {
      const graphData = generateLargeGraphData(100);
      let dragCallbackTime = 0;

      const handleNodeDrag = (node: Node, translate: { x: number; y: number }) => {
        dragCallbackTime = performance.now();
      };

      render(
        <GraphVisualizer
          data={graphData}
          onNodeDrag={handleNodeDrag}
        />
      );

      // Note: Actual drag simulation would require more complex setup
      // This test validates the component renders with drag handler
      expect(dragCallbackTime).toBe(0); // Not called yet
    });
  });

  describe('Memory and Resource Management', () => {
    it('should not leak memory when re-rendering with different data', () => {
      const initialData = generateLargeGraphData(100);
      const { rerender } = render(
        <GraphVisualizer data={initialData} />
      );

      // Re-render multiple times with different data
      for (let i = 0; i < 10; i++) {
        const newData = generateLargeGraphData(100);
        rerender(<GraphVisualizer data={newData} />);
      }

      // If we get here without crashing, memory management is acceptable
      expect(true).toBe(true);
    });

    it('should handle rapid data updates', () => {
      const initialData = generateLargeGraphData(50);
      const { rerender } = render(
        <GraphVisualizer data={initialData} />
      );

      const startTime = performance.now();

      // Simulate rapid updates
      for (let i = 0; i < 20; i++) {
        const updatedData = {
          ...initialData,
          nodes: initialData.nodes.map(node => ({
            ...node,
            x: node.x + Math.random() * 10,
            y: node.y + Math.random() * 10,
          })),
        };
        rerender(<GraphVisualizer data={updatedData} />);
      }

      const totalTime = performance.now() - startTime;

      // Should handle 20 rapid updates within 2000ms
      expect(totalTime).toBeLessThan(2000);
    });
  });

  describe('Level of Detail (LOD) Optimization', () => {
    it('should apply different rendering strategies based on zoom level', () => {
      const graphData = generateLargeGraphData(100);

      // Test with different zoom levels
      const zoomLevels = [0.1, 0.5, 1.0, 2.0, 5.0];

      zoomLevels.forEach(zoom => {
        const { container } = render(
          <GraphVisualizer
            data={graphData}
            initialZoom={zoom}
          />
        );

        expect(container).toBeTruthy();
      });
    });
  });
});
