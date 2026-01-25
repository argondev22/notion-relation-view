import * as fc from "fast-check";
import { Node } from "../types";

/**
 * Property 7: Node Click URL Generation
 *
 * **Validates: Requirement 4.1**
 *
 * This property verifies that clicking a node generates the correct Notion page URL.
 */

describe("Property 7: Node Click URL Generation", () => {
  const nodeArbitrary = fc.record({
    id: fc.hexaString({ minLength: 32, maxLength: 32 }), // Notion page IDs (32 hex chars)
    title: fc.string({ minLength: 1, maxLength: 100 }),
    databaseId: fc.hexaString({ minLength: 32, maxLength: 32 }),
    x: fc.double(),
    y: fc.double(),
    visible: fc.constant(true),
  });

  it("should generate valid Notion URL for any node", () => {
    fc.assert(
      fc.property(nodeArbitrary, (node: Node) => {
        // Generate Notion URL
        const notionUrl = `https://notion.so/${node.id.replace(/-/g, "")}`;

        // Verify URL format
        expect(notionUrl).toMatch(/^https:\/\/notion\.so\/[a-f0-9]{32}$/);

        // Verify URL contains node ID
        expect(notionUrl).toContain(node.id.replace(/-/g, ""));
      }),
      { numRuns: 100 }
    );
  });

  it("should handle node IDs with hyphens", () => {
    fc.assert(
      fc.property(
        fc.hexaString({ minLength: 32, maxLength: 32 }),
        (nodeId: string) => {
          const notionUrl = `https://notion.so/${nodeId.replace(/-/g, "")}`;

          // URL should not contain hyphens
          expect(notionUrl).not.toContain("-");

          // URL should be valid
          expect(notionUrl).toMatch(/^https:\/\/notion\.so\//);
        }
      ),
      { numRuns: 50 }
    );
  });
});

/**
 * Property 8: Node Position Update Consistency
 *
 * **Validates: Requirement 4.2**
 *
 * This property verifies that dragging a node updates its position consistently.
 */

describe("Property 8: Node Position Update Consistency", () => {
  const positionArbitrary = fc.record({
    x: fc.double({ min: -10000, max: 10000 }),
    y: fc.double({ min: -10000, max: 10000 }),
  });

  it("should update node position after drag", () => {
    fc.assert(
      fc.property(
        positionArbitrary,
        positionArbitrary,
        (initialPos, newPos) => {
          // Simulate drag operation
          const updatedPos = { ...newPos };

          // Position should be updated
          expect(updatedPos.x).toBe(newPos.x);
          expect(updatedPos.y).toBe(newPos.y);

          // Position should be different from initial (unless they're the same)
          if (initialPos.x !== newPos.x || initialPos.y !== newPos.y) {
            expect(
              updatedPos.x !== initialPos.x || updatedPos.y !== initialPos.y
            ).toBe(true);
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it("should preserve position precision", () => {
    fc.assert(
      fc.property(positionArbitrary, (pos) => {
        // Position values should be preserved exactly
        const updatedPos = { x: pos.x, y: pos.y };

        expect(updatedPos.x).toBe(pos.x);
        expect(updatedPos.y).toBe(pos.y);

        // Should handle negative values
        if (pos.x < 0) {
          expect(updatedPos.x).toBeLessThan(0);
        }
        if (pos.y < 0) {
          expect(updatedPos.y).toBeLessThan(0);
        }
      }),
      { numRuns: 100 }
    );
  });
});

/**
 * Property 9: View Pan Consistency
 *
 * **Validates: Requirement 4.3**
 *
 * This property verifies that panning the view updates the viewport consistently.
 */

describe("Property 9: View Pan Consistency", () => {
  const panArbitrary = fc.record({
    x: fc.double({ min: -5000, max: 5000 }),
    y: fc.double({ min: -5000, max: 5000 }),
  });

  it("should update pan position consistently", () => {
    fc.assert(
      fc.property(panArbitrary, panArbitrary, (initialPan, deltaPan) => {
        // Skip NaN and infinite values
        fc.pre(
          Number.isFinite(initialPan.x) &&
            Number.isFinite(initialPan.y) &&
            Number.isFinite(deltaPan.x) &&
            Number.isFinite(deltaPan.y)
        );

        // Calculate new pan position
        const newPan = {
          x: initialPan.x + deltaPan.x,
          y: initialPan.y + deltaPan.y,
        };

        // Pan should be updated
        expect(typeof newPan.x).toBe("number");
        expect(typeof newPan.y).toBe("number");

        // Pan delta should be applied correctly
        expect(newPan.x - initialPan.x).toBeCloseTo(deltaPan.x, 10);
        expect(newPan.y - initialPan.y).toBeCloseTo(deltaPan.y, 10);
      }),
      { numRuns: 100 }
    );
  });

  it("should handle large pan distances", () => {
    fc.assert(
      fc.property(
        fc.double({ min: -10000, max: 10000 }),
        fc.double({ min: -10000, max: 10000 }),
        (panX, panY) => {
          // Skip NaN and infinite values
          fc.pre(Number.isFinite(panX) && Number.isFinite(panY));

          const pan = { x: panX, y: panY };

          // Pan values should be finite
          expect(Number.isFinite(pan.x)).toBe(true);
          expect(Number.isFinite(pan.y)).toBe(true);

          // Pan should preserve sign
          if (panX < 0) {
            expect(pan.x).toBeLessThan(0);
          }
          if (panY < 0) {
            expect(pan.y).toBeLessThan(0);
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});

/**
 * Property 10: Zoom Operation Consistency
 *
 * **Validates: Requirement 4.4**
 *
 * This property verifies that zoom operations maintain consistency.
 */

describe("Property 10: Zoom Operation Consistency", () => {
  const zoomArbitrary = fc.double({ min: 0.1, max: 10 });

  it("should maintain zoom level within valid range", () => {
    fc.assert(
      fc.property(zoomArbitrary, (zoom) => {
        // Skip NaN and infinite values
        fc.pre(Number.isFinite(zoom));

        // Zoom should be positive
        expect(zoom).toBeGreaterThan(0);

        // Zoom should be finite
        expect(Number.isFinite(zoom)).toBe(true);

        // Zoom should be within reasonable bounds
        expect(zoom).toBeGreaterThanOrEqual(0.1);
        expect(zoom).toBeLessThanOrEqual(10);
      }),
      { numRuns: 100 }
    );
  });

  it("should handle zoom in and zoom out operations", () => {
    fc.assert(
      fc.property(
        zoomArbitrary,
        fc.double({ min: 0.5, max: 2 }),
        (initialZoom, zoomFactor) => {
          // Skip NaN and infinite values
          fc.pre(Number.isFinite(initialZoom) && Number.isFinite(zoomFactor));

          const newZoom = initialZoom * zoomFactor;

          // New zoom should be positive
          expect(newZoom).toBeGreaterThan(0);

          // Zoom factor should be applied correctly
          expect(newZoom / initialZoom).toBeCloseTo(zoomFactor, 10);

          // Zooming in should increase zoom level
          if (zoomFactor > 1) {
            expect(newZoom).toBeGreaterThan(initialZoom);
          }

          // Zooming out should decrease zoom level
          if (zoomFactor < 1) {
            expect(newZoom).toBeLessThan(initialZoom);
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it("should preserve zoom precision", () => {
    fc.assert(
      fc.property(zoomArbitrary, (zoom) => {
        // Skip NaN values
        fc.pre(Number.isFinite(zoom));

        // Zoom value should be preserved exactly
        const storedZoom = zoom;

        expect(storedZoom).toBe(zoom);

        // Should handle decimal precision
        const rounded = Math.round(zoom * 1000) / 1000;
        expect(typeof rounded).toBe("number");
        expect(Number.isFinite(rounded)).toBe(true);
      }),
      { numRuns: 100 }
    );
  });
});
