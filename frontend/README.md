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

### Database

- Drizzle ORM for type-safe database queries
- PostgreSQL for data persistence
- Automatic migrations

### API Layer

- tRPC for end-to-end type safety
- Server-side API routes
- Client-side data fetching with React Query

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
