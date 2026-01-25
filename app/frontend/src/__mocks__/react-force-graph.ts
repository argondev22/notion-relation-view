import React from "react";

const MockForceGraph2D = React.forwardRef(() => {
  return React.createElement("div", { "data-testid": "force-graph" }, "Mock Force Graph");
});

MockForceGraph2D.displayName = "MockForceGraph2D";

export { MockForceGraph2D as ForceGraph2D };
export default MockForceGraph2D;
