# Product Overview

## Notion Relation View

A web application that visualizes Notion page relationships as an interactive graph, similar to Obsidian's graph view. Users can explore connections between Notion pages through nodes and edges representing relations.

### Core Features

- **Graph Visualization**: Display Notion pages as nodes with relation-based connections
- **Interactive Navigation**: Click nodes to open pages, drag to reposition, pan/zoom canvas
- **View Management**: Create, save, and share multiple view configurations with unique URLs
- **Notion Embedding**: Embed views directly in Notion pages via URL
- **Database Filtering**: Select specific databases to display in the graph
- **Search & Highlight**: Find and focus on specific pages

### Monetization

Two-tier subscription model:
- **Free Plan**: 1 view, 100 nodes, basic features
- **Pro Plan**: $10/month, unlimited views/nodes, export (PNG/SVG), custom themes, advanced filtering, layout algorithms

### Technical Approach

- Web-based application accessible across all Notion platforms (web, desktop, mobile)
- Connects via Notion API with user-provided tokens
- Stores API tokens and view configurations server-side
- Real-time data updates from Notion workspace
