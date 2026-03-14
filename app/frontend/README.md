# Notion Relation View - Frontend

React + TypeScript frontend for the Notion Relation View application.

## Architecture

- **Framework**: React 18
- **Language**: TypeScript
- **Build Tool**: Vite
- **Routing**: React Router
- **HTTP Client**: Axios
- **Testing**: Vitest + React Testing Library + fast-check

## Directory Structure

```
frontend/
├── src/
│   ├── components/      # React components (to be implemented)
│   ├── contexts/        # React contexts (to be implemented)
│   ├── hooks/           # Custom hooks (to be implemented)
│   ├── services/        # API services (to be implemented)
│   ├── types/           # TypeScript types (to be implemented)
│   ├── utils/           # Utility functions (to be implemented)
│   ├── test/            # Test setup
│   ├── App.tsx          # Main App component
│   ├── App.css          # App styles
│   ├── main.tsx         # Application entry point
│   └── index.css        # Global styles
├── public/              # Static assets
├── index.html           # HTML template
├── package.json         # Dependencies and scripts
├── tsconfig.json        # TypeScript configuration
├── vite.config.ts       # Vite configuration
└── Dockerfile           # Docker configuration
```

## Setup

### Local Development

1. Install dependencies:

    ```bash
    npm install
    ```

2. Set up environment variables:

    ```bash
    # Create .env.local file
    echo "VITE_API_URL=http://localhost:8000" > .env.local
    ```

3. Start the development server:

    ```bash
    npm run dev
    ```

4. Open http://localhost:3000

### Docker Development

From the `app/` directory:

```bash
docker compose up frontend
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm test` - Run tests once
- `npm run test:watch` - Run tests in watch mode

## Testing

Run tests:

```bash
npm test
```

Run tests in watch mode:

```bash
npm run test:watch
```

## Environment Variables

- `VITE_API_URL`: Backend API URL (default: http://localhost:8000)

## Code Style

- 2 spaces indentation
- 100 character line width
- Prettier for formatting
- ESLint for linting

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES2020+ features
