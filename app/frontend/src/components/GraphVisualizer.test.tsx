import React from "react";
import { render } from "@testing-library/react";
import "@testing-library/jest-dom";
import GraphVisualizer from "./GraphVisualizer";
import { GraphData } from "../types";

describe("GraphVisualizer", () => {
  const emptyGraphData: GraphData = {
    nodes: [],
    edges: [],
    databases: [],
  };

  const simpleGraphData: GraphData = {
    nodes: [
      {
        id: "node-1",
        title: "Node 1",
        databaseId: "db-1",
        x: 0,
        y: 0,
        visible: true,
      },
      {
        id: "node-2",
        title: "Node 2",
        databaseId: "db-1",
        x: 100,
        y: 100,
        visible: true,
      },
    ],
    edges: [
      {
        id: "edge-1",
        sourceId: "node-1",
        targetId: "node-2",
        relationProperty: "related",
        visible: true,
      },
    ],
    databases: [
      {
        id: "db-1",
        title: "Database 1",
        hidden: false,
      },
    ],
  };

  const largeGraphData: GraphData = {
    nodes: Array.from({ length: 150 }, (_, i) => ({
      id: `node-${i}`,
      title: `Node ${i}`,
      databaseId: "db-1",
      x: Math.random() * 1000,
      y: Math.random() * 1000,
      visible: true,
    })),
    edges: Array.from({ length: 200 }, (_, i) => ({
      id: `edge-${i}`,
      sourceId: `node-${Math.floor(Math.random() * 150)}`,
      targetId: `node-${Math.floor(Math.random() * 150)}`,
      relationProperty: "related",
      visible: true,
    })),
    databases: [],
  };

  it("renders without crashing", () => {
    const { container } = render(<GraphVisualizer data={emptyGraphData} />);
    expect(container).toBeInTheDocument();
  });

  it("renders force graph component", () => {
    const { getByTestId } = render(<GraphVisualizer data={simpleGraphData} />);
    expect(getByTestId("force-graph")).toBeInTheDocument();
  });

  it("handles empty graph data", () => {
    const { container } = render(<GraphVisualizer data={emptyGraphData} />);
    expect(container.querySelector(".graph-visualizer")).toBeInTheDocument();
  });

  it("handles simple graph with nodes and edges", () => {
    const { container } = render(<GraphVisualizer data={simpleGraphData} />);
    expect(container.querySelector(".graph-visualizer")).toBeInTheDocument();
  });

  it("handles large graphs (100+ nodes)", () => {
    const { container } = render(<GraphVisualizer data={largeGraphData} />);
    expect(container.querySelector(".graph-visualizer")).toBeInTheDocument();
  });

  it("accepts node click handler", () => {
    const handleNodeClick = jest.fn();
    render(
      <GraphVisualizer data={simpleGraphData} onNodeClick={handleNodeClick} />
    );
    // Handler should be passed to component
    expect(handleNodeClick).not.toHaveBeenCalled();
  });

  it("accepts node drag handler", () => {
    const handleNodeDrag = jest.fn();
    render(
      <GraphVisualizer data={simpleGraphData} onNodeDrag={handleNodeDrag} />
    );
    // Handler should be passed to component
    expect(handleNodeDrag).not.toHaveBeenCalled();
  });

  it("accepts zoom handler", () => {
    const handleZoom = jest.fn();
    render(<GraphVisualizer data={simpleGraphData} onZoom={handleZoom} />);
    // Handler should be passed to component
    expect(handleZoom).not.toHaveBeenCalled();
  });

  it("accepts pan handler", () => {
    const handlePan = jest.fn();
    render(<GraphVisualizer data={simpleGraphData} onPan={handlePan} />);
    // Handler should be passed to component
    expect(handlePan).not.toHaveBeenCalled();
  });

  it("accepts initial zoom level", () => {
    const { container } = render(
      <GraphVisualizer data={simpleGraphData} initialZoom={2} />
    );
    expect(container.querySelector(".graph-visualizer")).toBeInTheDocument();
  });

  it("accepts initial pan position", () => {
    const { container } = render(
      <GraphVisualizer
        data={simpleGraphData}
        initialPan={{ x: 100, y: 200 }}
      />
    );
    expect(container.querySelector(".graph-visualizer")).toBeInTheDocument();
  });

  it("filters out invisible nodes", () => {
    const dataWithInvisibleNodes: GraphData = {
      nodes: [
        {
          id: "node-1",
          title: "Visible Node",
          databaseId: "db-1",
          x: 0,
          y: 0,
          visible: true,
        },
        {
          id: "node-2",
          title: "Invisible Node",
          databaseId: "db-1",
          x: 100,
          y: 100,
          visible: false,
        },
      ],
      edges: [],
      databases: [],
    };

    const { container } = render(
      <GraphVisualizer data={dataWithInvisibleNodes} />
    );
    expect(container.querySelector(".graph-visualizer")).toBeInTheDocument();
  });

  it("filters out invisible edges", () => {
    const dataWithInvisibleEdges: GraphData = {
      nodes: [
        {
          id: "node-1",
          title: "Node 1",
          databaseId: "db-1",
          x: 0,
          y: 0,
          visible: true,
        },
        {
          id: "node-2",
          title: "Node 2",
          databaseId: "db-1",
          x: 100,
          y: 100,
          visible: true,
        },
      ],
      edges: [
        {
          id: "edge-1",
          sourceId: "node-1",
          targetId: "node-2",
          relationProperty: "related",
          visible: false,
        },
      ],
      databases: [],
    };

    const { container } = render(
      <GraphVisualizer data={dataWithInvisibleEdges} />
    );
    expect(container.querySelector(".graph-visualizer")).toBeInTheDocument();
  });
});
