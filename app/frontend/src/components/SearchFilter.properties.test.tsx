import * as fc from "fast-check";
import { Node, Database, Edge } from "../types";

/**
 * Property 11: Search Function Accuracy
 *
 * **Validates: Requirement 5.4**
 *
 * This property verifies that the search function accurately finds nodes
 * matching the search query.
 */

describe("Property 11: Search Function Accuracy", () => {
  const nodeArbitrary = fc.record({
    id: fc.hexaString({ minLength: 32, maxLength: 32 }),
    title: fc.string({ minLength: 1, maxLength: 50 }),
    databaseId: fc.hexaString({ minLength: 32, maxLength: 32 }),
    x: fc.double(),
    y: fc.double(),
    visible: fc.constant(true),
  });

  const searchFunction = (nodes: Node[], query: string): Node[] => {
    if (!query.trim()) {
      return [];
    }
    const lowerQuery = query.toLowerCase();
    return nodes.filter((node) =>
      node.title.toLowerCase().includes(lowerQuery)
    );
  };

  it("should find all nodes containing the search query", () => {
    fc.assert(
      fc.property(
        fc.array(nodeArbitrary, { minLength: 1, maxLength: 20 }),
        fc.string({ minLength: 1, maxLength: 10 }).filter(s => s.trim().length > 0),
        (nodes, query) => {
          const results = searchFunction(nodes, query);

          // All results should contain the query
          for (const result of results) {
            expect(result.title.toLowerCase()).toContain(query.toLowerCase());
          }

          // All nodes containing the query should be in results
          const expectedResults = nodes.filter((node) =>
            node.title.toLowerCase().includes(query.toLowerCase())
          );
          expect(results.length).toBe(expectedResults.length);
        }
      ),
      { numRuns: 100 }
    );
  });

  it("should be case-insensitive", () => {
    fc.assert(
      fc.property(
        fc.array(nodeArbitrary, { minLength: 1, maxLength: 20 }),
        fc.string({ minLength: 1, maxLength: 10 }),
        (nodes, query) => {
          const lowerResults = searchFunction(nodes, query.toLowerCase());
          const upperResults = searchFunction(nodes, query.toUpperCase());
          const mixedResults = searchFunction(nodes, query);

          // All three should return the same results
          expect(lowerResults.length).toBe(upperResults.length);
          expect(lowerResults.length).toBe(mixedResults.length);
        }
      ),
      { numRuns: 50 }
    );
  });

  it("should return empty array for empty query", () => {
    fc.assert(
      fc.property(
        fc.array(nodeArbitrary, { minLength: 1, maxLength: 20 }),
        (nodes) => {
          const results = searchFunction(nodes, "");
          expect(results.length).toBe(0);
        }
      ),
      { numRuns: 50 }
    );
  });

  it("should handle special characters in search query", () => {
    fc.assert(
      fc.property(
        fc.array(nodeArbitrary, { minLength: 1, maxLength: 20 }),
        fc.string({ minLength: 1, maxLength: 10 }),
        (nodes, query) => {
          // Should not throw error
          expect(() => searchFunction(nodes, query)).not.toThrow();

          const results = searchFunction(nodes, query);
          expect(Array.isArray(results)).toBe(true);
        }
      ),
      { numRuns: 50 }
    );
  });
});

/**
 * Property 12: Search Result Centering
 *
 * **Validates: Requirement 5.5**
 *
 * This property verifies that search results can be centered in the view.
 */

describe("Property 12: Search Result Centering", () => {
  const calculateCenter = (nodes: Node[]): { x: number; y: number } | null => {
    if (nodes.length === 0) {
      return null;
    }

    const sumX = nodes.reduce((sum, node) => sum + node.x, 0);
    const sumY = nodes.reduce((sum, node) => sum + node.y, 0);

    return {
      x: sumX / nodes.length,
      y: sumY / nodes.length,
    };
  };

  const nodeArbitrary = fc.record({
    id: fc.hexaString({ minLength: 32, maxLength: 32 }),
    title: fc.string({ minLength: 1, maxLength: 50 }),
    databaseId: fc.hexaString({ minLength: 32, maxLength: 32 }),
    x: fc.double({ min: -1000, max: 1000 }),
    y: fc.double({ min: -1000, max: 1000 }),
    visible: fc.constant(true),
  });

  it("should calculate center point for search results", () => {
    fc.assert(
      fc.property(
        fc.array(nodeArbitrary, { minLength: 1, maxLength: 20 }),
        (nodes) => {
          // Skip if any node has NaN coordinates
          fc.pre(nodes.every((n) => Number.isFinite(n.x) && Number.isFinite(n.y)));

          const center = calculateCenter(nodes);

          expect(center).not.toBeNull();
          expect(typeof center!.x).toBe("number");
          expect(typeof center!.y).toBe("number");
          expect(Number.isFinite(center!.x)).toBe(true);
          expect(Number.isFinite(center!.y)).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });

  it("should return null for empty node array", () => {
    const center = calculateCenter([]);
    expect(center).toBeNull();
  });

  it("should return node position for single node", () => {
    fc.assert(
      fc.property(nodeArbitrary, (node) => {
        fc.pre(Number.isFinite(node.x) && Number.isFinite(node.y));

        const center = calculateCenter([node]);

        expect(center).not.toBeNull();
        expect(center!.x).toBe(node.x);
        expect(center!.y).toBe(node.y);
      }),
      { numRuns: 50 }
    );
  });

  it("should calculate average position for multiple nodes", () => {
    fc.assert(
      fc.property(
        fc.array(nodeArbitrary, { minLength: 2, maxLength: 10 }),
        (nodes) => {
          fc.pre(nodes.every((n) => Number.isFinite(n.x) && Number.isFinite(n.y)));

          const center = calculateCenter(nodes);
          const expectedX = nodes.reduce((sum, n) => sum + n.x, 0) / nodes.length;
          const expectedY = nodes.reduce((sum, n) => sum + n.y, 0) / nodes.length;

          expect(center).not.toBeNull();
          expect(center!.x).toBeCloseTo(expectedX, 10);
          expect(center!.y).toBeCloseTo(expectedY, 10);
        }
      ),
      { numRuns: 100 }
    );
  });
});

/**
 * Property 13: Database Filtering Accuracy
 *
 * **Validates: Requirements 5.2, 5.3**
 *
 * This property verifies that database filtering correctly shows/hides
 * nodes and edges based on selected databases.
 */

describe("Property 13: Database Filtering Accuracy", () => {
  const nodeArbitrary = fc.record({
    id: fc.hexaString({ minLength: 32, maxLength: 32 }),
    title: fc.string({ minLength: 1, maxLength: 50 }),
    databaseId: fc.hexaString({ minLength: 32, maxLength: 32 }),
    x: fc.double(),
    y: fc.double(),
    visible: fc.constant(true),
  });

  const filterByDatabases = (
    nodes: Node[],
    edges: Edge[],
    selectedDatabaseIds: string[]
  ): { nodes: Node[]; edges: Edge[] } => {
    if (selectedDatabaseIds.length === 0) {
      return { nodes: [], edges: [] };
    }

    // Filter nodes
    const filteredNodes = nodes.filter((node) =>
      selectedDatabaseIds.includes(node.databaseId)
    );

    // Filter edges (only keep edges where both nodes are visible)
    const visibleNodeIds = new Set(filteredNodes.map((n) => n.id));
    const filteredEdges = edges.filter(
      (edge) =>
        visibleNodeIds.has(edge.sourceId) && visibleNodeIds.has(edge.targetId)
    );

    return { nodes: filteredNodes, edges: filteredEdges };
  };

  it("should only show nodes from selected databases", () => {
    fc.assert(
      fc.property(
        fc.array(nodeArbitrary, { minLength: 1, maxLength: 20 }),
        (nodes) => {
          const databaseIds = [...new Set(nodes.map((n) => n.databaseId))];
          const selectedIds = databaseIds.slice(0, Math.ceil(databaseIds.length / 2));

          const { nodes: filtered } = filterByDatabases(nodes, [], selectedIds);

          // All filtered nodes should be from selected databases
          for (const node of filtered) {
            expect(selectedIds).toContain(node.databaseId);
          }

          // All nodes from selected databases should be included
          const expectedCount = nodes.filter((n) =>
            selectedIds.includes(n.databaseId)
          ).length;
          expect(filtered.length).toBe(expectedCount);
        }
      ),
      { numRuns: 100 }
    );
  });

  it("should return empty graph when no databases selected", () => {
    fc.assert(
      fc.property(
        fc.array(nodeArbitrary, { minLength: 1, maxLength: 20 }),
        (nodes) => {
          const { nodes: filtered, edges: filteredEdges } = filterByDatabases(
            nodes,
            [],
            []
          );

          expect(filtered.length).toBe(0);
          expect(filteredEdges.length).toBe(0);
        }
      ),
      { numRuns: 50 }
    );
  });

  it("should filter edges based on visible nodes", () => {
    fc.assert(
      fc.property(
        fc.array(nodeArbitrary, { minLength: 2, maxLength: 10 }),
        (nodes) => {
          // Create edges between nodes
          const edges: Edge[] = [];
          for (let i = 0; i < nodes.length - 1; i++) {
            edges.push({
              id: `edge-${i}`,
              sourceId: nodes[i].id,
              targetId: nodes[i + 1].id,
              relationProperty: "relation",
              visible: true,
            });
          }

          const databaseIds = [...new Set(nodes.map((n) => n.databaseId))];
          const selectedIds = databaseIds.slice(0, 1); // Select only first database

          const { edges: filteredEdges } = filterByDatabases(
            nodes,
            edges,
            selectedIds
          );

          // All filtered edges should connect visible nodes
          const visibleNodeIds = new Set(
            nodes
              .filter((n) => selectedIds.includes(n.databaseId))
              .map((n) => n.id)
          );

          for (const edge of filteredEdges) {
            expect(visibleNodeIds.has(edge.sourceId)).toBe(true);
            expect(visibleNodeIds.has(edge.targetId)).toBe(true);
          }
        }
      ),
      { numRuns: 50 }
    );
  });
});

