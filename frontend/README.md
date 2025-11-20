# AI Ad Video Generator - Frontend

This is the frontend application for the AI Ad Video Generator, built with the [T3 Stack](https://create.t3.gg/). It provides a user interface for generating AI-powered product advertisement videos through an interactive, multi-stage workflow.

## Overview

The frontend enables users to:

- Generate product images from text prompts
- Select approved images for video generation
- Generate video clips from selected images
- Compose final videos with text overlays and audio
- Track costs and progress in real-time

## Tech Stack

This project uses the following technologies:

- **[Bun](https://bun.sh)** - Fast JavaScript runtime and package manager
- **[Next.js 15](https://nextjs.org)** - React framework with App Router
- **[NextAuth.js v5](https://next-auth.js.org)** - Authentication
- **[Drizzle ORM](https://orm.drizzle.team)** - Type-safe database ORM
- **[tRPC](https://trpc.io)** - End-to-end typesafe APIs
- **[Tailwind CSS](https://tailwindcss.com)** - Styling
- **[TypeScript](https://www.typescriptlang.org)** - Type safety

## Project Structure

```
pipeline/
├── src/
│   ├── app/              # Next.js App Router pages
│   │   ├── api/          # API routes (auth, tRPC)
│   │   ├── login/        # Login page
│   │   └── page.tsx      # Home page
│   ├── server/           # Server-side code
│   │   ├── api/          # tRPC router
│   │   ├── auth/         # NextAuth configuration
│   │   └── db/           # Database schema and client
│   ├── trpc/             # tRPC client setup
│   └── styles/           # Global styles
├── public/               # Static assets
└── package.json          # Dependencies
```

## Getting Started

### Prerequisites

- [Bun](https://bun.sh) (recommended) or Node.js 18+
- PostgreSQL database (or use Docker)
- Environment variables configured

### Installation

1. **Install dependencies:**

```bash
bun install
```

2. **Set up environment variables:**

Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL="postgresql://user:password@localhost:5432/pipeline"

# NextAuth
NEXTAUTH_SECRET="your-secret-key-here"
NEXTAUTH_URL="http://localhost:3000"

# Backend API
NEXT_PUBLIC_API_URL="http://localhost:8000"

# Optional: Add other environment variables
```

3. **Set up the database:**

```bash
# Generate migrations
bun run db:generate

# Push schema to database
bun run db:push

# Or use migrations
bun run db:migrate
```

4. **Run the development server:**

```bash
bun dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Available Scripts

- `bun dev` - Start development server
- `bun run build` - Build for production
- `bun run start` - Start production server
- `bun run lint` - Run ESLint
- `bun run typecheck` - Run TypeScript type checking
- `bun run db:generate` - Generate Drizzle migrations
- `bun run db:push` - Push schema changes to database
- `bun run db:migrate` - Run database migrations
- `bun run db:studio` - Open Drizzle Studio

> **Note:** This project uses Bun as the package manager and runtime. You can use `npm` or `yarn` as alternatives, but Bun is recommended for optimal performance.

## Integration with Backend Orchestrator

This frontend integrates with the AI Video Generation Orchestrator backend service. The orchestrator handles:

- Job creation and management
- Microservice coordination (Prompt Parser, Image Gen, Video Gen, Composition)
- Real-time progress updates
- Cost tracking
- Error handling

See the [Architecture Documentation](../ARCHITECTURE.md) and [PRD](../prd.md) for more details about the backend system.

## Features

### Authentication

- NextAuth.js v5 with database sessions
- Secure session management
- Protected routes
- Token exchange pattern for backend integration (see [Authentication Architecture](#authentication-architecture) below)

### Database

- Drizzle ORM for type-safe database queries
- PostgreSQL for data persistence
- Automatic migrations

### API Layer

- tRPC for end-to-end type safety
- Server-side API routes
- Client-side data fetching with React Query

## Authentication Architecture

This frontend uses a **token exchange pattern** to bridge NextAuth.js sessions with the backend's JWT-based authentication system. This approach was chosen for several reasons:

### Why Token Exchange?

1. **Backend Independence**: The backend doesn't need to know about NextAuth.js or any specific frontend authentication provider. It maintains its own JWT-based authentication system.

2. **Single Source of Truth**: The backend JWT remains the authoritative authentication mechanism for all backend API calls, ensuring consistent security policies.

3. **OAuth2 Standard**: This pattern follows established OAuth2 token exchange patterns, making it familiar to developers and compatible with industry standards.

4. **Extensibility**: Easy to add other authentication providers (Google, GitHub, etc.) without modifying backend code. The backend only needs to validate that a user exists before issuing a token.

5. **Security**: The backend validates that users exist in its database before issuing tokens, preventing unauthorized access.

### Authentication Flow

1. **User Login**: User logs in via NextAuth.js (Google OAuth, Credentials, etc.)
2. **Session Creation**: NextAuth.js creates a session and stores it in the database
3. **Token Exchange**: Frontend calls `/api/auth/exchange` with the user's email from the NextAuth session
4. **Backend Validation**: Backend validates the user exists in its database by email
5. **JWT Issuance**: Backend returns a JWT token compatible with its authentication system
6. **Token Caching**: Frontend caches the JWT token to avoid repeated exchanges
7. **API Calls**: All backend API calls include the JWT token in the `Authorization: Bearer <token>` header
8. **Backend Validation**: Backend validates the JWT using its existing middleware

### Implementation Details

- **Token Exchange Endpoint**: `POST /api/auth/exchange` (backend)
- **Token Management**: `frontend/src/lib/auth-token.ts` handles token exchange and caching
- **Token Caching**: Tokens are cached in memory with expiration (25 minutes, refreshed 5 minutes before expiry)
- **tRPC Integration**: tRPC procedures automatically fetch and include backend tokens in API requests

### Alternative Approaches Considered

1. **Direct NextAuth Token Forwarding**: Would require backend to understand NextAuth tokens, coupling the systems
2. **Backend Accepts NextAuth Sessions**: Would require backend changes every time frontend auth changes
3. **Shared JWT Secret**: Would create tight coupling between frontend and backend authentication systems

The token exchange pattern provides the best balance of security, maintainability, and flexibility.

### Setup Instructions

1. Ensure the backend API is running and accessible at the URL specified in `NEXT_PUBLIC_API_URL`
2. Users must exist in both the frontend (NextAuth) database and the backend database
3. The backend `/api/auth/exchange` endpoint must be accessible from the frontend

## Learn More

To learn more about the technologies used in this project:

- [Next.js Documentation](https://nextjs.org)
- [NextAuth.js Documentation](https://next-auth.js.org)
- [Drizzle ORM Documentation](https://orm.drizzle.team)
- [tRPC Documentation](https://trpc.io)
- [Tailwind CSS Documentation](https://tailwindcss.com)

## Project Documentation

- [Product Requirements Document](../Docs/MVP_PRD.md) - Complete PRD for the AI Ad Video Generator
- [Architecture Document](../ARCHITECTURE.md) - System architecture and design decisions
- [PRD Summary](../prd.md) - High-level product requirements

## Deployment

### Vercel (Recommended)

1. Push your code to GitHub
2. Import your repository in [Vercel](https://vercel.com)
3. Configure environment variables
4. Deploy!

### Other Platforms

This Next.js application can be deployed to any platform that supports Node.js or Bun:

- [Netlify](https://www.netlify.com)
- [Railway](https://railway.app)
- [Docker](https://www.docker.com)

> **Note:** Most platforms support Bun. Check the platform's documentation for Bun-specific configuration if needed.

See the [Next.js deployment documentation](https://nextjs.org/docs/deployment) for more details.

## Contributing

This project is part of the Gauntlet AI Video Generation Challenge. For contribution guidelines, please refer to the main project documentation.

## License

See the main project repository for license information.
