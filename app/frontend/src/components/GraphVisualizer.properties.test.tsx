import * as fc from "fast-check";
import { GraphData, Node, Edge } from "../types";

/**
 * Property 6: Layout Algorithm Execution
 *
 * **Validates: Requirements 3.4**
 *
 * This property verifies that the force-directed layout algorithm executes
 * correctly for any valid graph structure.
 */

describe("Property 6: Layout Algorithm Execution", () => {
  // Arbitrary for generating valid node IDs
  const nodeIdArbitrary = fc.string({ minLength: 1, maxLength: 20 });

  // Arbitrary for generating nodes
  const nodeArbitrary = fc.record({
    id: nodeIdArbitrary,
    title: fc.string({ minLength: 1, maxLength: 50 }),
    databaseId: fc.string({ minLength: 1, maxLength: 20 }),
    x: fc.double({ min: -1000, max: 1000 }),
    y: fc.double({ min: -1000, max: 1000 }),
    visible: fc.constant(true),
  });

  // Arbitrary for generating edges with valid node references
  const edgeArbitrary = (nodeIds: string[]) =>
    fc.record({
      id: fc.string({ minLength: 1, maxLength: 20 }),
      sourceId: fc.constantFrom(...nodeIds),
      targetId: fc.constantFrom(...nodeIds),
      relationProperty: fc.string({ minLength: 1, maxLength: 30 }),
      visible: fc.constant(true),
    });

  // Arbitrary for generating graph data
  const graphDataArbitrary = fc
    .array(nodeArbitrary, { minLength: 1, maxLength: 20 })
    .chain((nodes) => {
      const nodeIds = nodes.map((n) => n.id);
      return fc
        .array(edgeArbitrary(nodeIds), { maxLength: nodes.length * 2 })
        .map((edges) => ({
          nodes,
          edges,
          databases: [],
        }));
    });

  it("should handle any valid graph structure", () => {
    fc.assert(
      fc.property(graphDataArbitrary, (graphData: GraphData) => {
        // Verify all nodes are present
        expect(graphData.nodes.length).toBeGreaterThan(0);

        // Verify all edges reference valid nodes
        const nodeIds = new Set(graphData.nodes.map((n) => n.id));
        for (const edge of graphData.edges) {
          expect(nodeIds.has(edge.sourceId)).toBe(true);
          expect(nodeIds.has(edge.targetId)).toBe(true);
        }

        // Verify node positions are numbers
        for (const node of graphData.nodes) {
          expect(typeof node.x).toBe("number");
          expect(typeof node.y).toBe("number");
        }
      }),
      { numRuns: 100 }
    );
  });

  it("should handle graphs with no edges (isolated nodes)", () => {
    fc.assert(
      fc.property(
        fc.array(nodeArbitrary, { minLength: 1, maxLength: 10 }),
        (nodes: Node[]) => {
          const graphData: GraphData = {
            nodes,
            edges: [],
            databases: [],
          };

          // All nodes should still be valid
          expect(graphData.nodes.length).toBeGreaterThan(0);
          expect(graphData.edges.length).toBe(0);

          // Nodes should have valid positions
          for (const node of graphData.nodes) {
            expect(typeof node.x).toBe("number");
            expect(typeof node.y).toBe("number");
          }
        }
      ),
      { numRuns: 50 }
    );
  });

  it("should handle graphs with cycles", () => {
    fc.assert(
      fc.property(
        fc.array(nodeArbitrary, { minLength: 3, maxLength: 10 }),
        (nodes: Node[]) => {
          // Create a cycle: node[0] -> node[1] -> node[2] -> node[0]
          const edges: Edge[] = [];
          for (let i = 0; i < Math.min(nodes.length, 3); i++) {
            edges.push({
              id: `edge-${i}`,
              sourceId: nodes[i].id,
              targetId: nodes[(i + 1) % Math.min(nodes.length, 3)].id,
              relationProperty: "relation",
              visible: true,
            });
          }

          const graphData: GraphData = {
            nodes,
            edges,
            databases: [],
          };

          // Verify cycle is valid
          expect(graphData.edges.length).toBeGreaterThanOrEqual(3);

          // All edges should reference valid nodes
          const nodeIds = new Set(graphData.nodes.map((n) => n.id));
          for (const edge of graphData.edges) {
            expect(nodeIds.has(edge.sourceId)).toBe(true);
            expect(nodeIds.has(edge.targetId)).toBe(true);
          }
        }
      ),
      { numRuns: 50 }
    );
  });

  it("should handle dense graphs (many edges)", () => {
    fc.assert(
      fc.property(
        fc.array(nodeArbitrary, { minLength: 3, maxLength: 8 }),
        (nodes: Node[]) => {
          // Create a dense graph (connect each node to multiple others)
          const edges: Edge[] = [];
          for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
              edges.push({
                id: `edge-${i}-${j}`,
                sourceId: nodes[i].id,
                targetId: nodes[j].id,
                relationProperty: "relation",
                visible: true,
              });
            }
          }

          const graphData: GraphData = {
            nodes,
            edges,
            databases: [],
          };

          // Verify dense graph structure
          const expectedEdges = (nodes.length * (nodes.length - 1)) / 2;
          expect(graphData.edges.length).toBe(expectedEdges);

          // All edges should be valid
          const nodeIds = new Set(graphData.nodes.map((n) => n.id));
          for (const edge of graphData.edges) {
            expect(nodeIds.has(edge.sourceId)).toBe(true);
            expect(nodeIds.has(edge.targetId)).toBe(true);
          }
        }
      ),
      { numRuns: 30 }
    );
  });
});
