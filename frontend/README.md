# Ed-Tech Content Creation Platform - Frontend

This is the frontend application for the AI-Powered Educational Content Creation Platform, built with the [T3 Stack](https://create.t3.gg/). It provides an interactive, multi-stage workflow for creating engaging educational content with AI assistance.

## Overview

The frontend enables educators to:

- Extract key facts and concepts from documents (text or PDF uploads)
- Generate age-appropriate educational narratives with AI
- Create structured scripts with hooks, concept explanations, and conclusions
- Build and edit educational videos with an advanced timeline editor
- Manage content assets and track session history

## Tech Stack

This project uses the following technologies:

- **[Next.js 16](https://nextjs.org)** - React 19 framework with App Router and Turbo
- **[React 19](https://react.dev)** - UI library with latest features
- **[NextAuth.js v5](https://next-auth.js.org)** - Authentication (Google OAuth)
- **[Drizzle ORM](https://orm.drizzle.team)** - Type-safe database ORM
- **[tRPC](https://trpc.io)** - End-to-end typesafe APIs
- **[Vercel AI SDK](https://sdk.vercel.ai)** - AI/LLM integration with OpenAI
- **[Remotion](https://remotion.dev)** - Programmatic video creation and editing
- **[React Flow](https://reactflow.dev)** - Node-based workflow diagrams
- **[Zustand](https://zustand-demo.pmnd.rs)** - State management
- **[Tailwind CSS v4](https://tailwindcss.com)** - Styling
- **[shadcn/ui](https://ui.shadcn.com)** - UI components (Radix-based)
- **[Material UI](https://mui.com)** - Additional UI components
- **[Motion](https://motion.dev)** - Animations (Framer Motion successor)
- **[PDF.js](https://mozilla.github.io/pdf.js/)** - PDF document parsing
- **[TypeScript](https://www.typescriptlang.org)** - Type safety

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── api/                # API routes (auth, tRPC)
│   │   ├── dashboard/          # Protected dashboard routes
│   │   │   ├── admin/          # Admin interface
│   │   │   ├── assets/         # Asset gallery/management
│   │   │   ├── create/         # Main creation workflow
│   │   │   ├── editing/[id]/   # Video editor
│   │   │   └── history/        # Session history
│   │   └── login/              # Authentication page
│   ├── components/             # React components
│   │   ├── agent-create/       # Creation workflow UI
│   │   ├── ai-elements/        # AI chat UI components
│   │   ├── content/            # Content gallery components
│   │   ├── video-editor/       # Timeline-based video editor
│   │   └── ui/                 # shadcn/ui components
│   ├── hooks/                  # Custom React hooks
│   ├── lib/                    # Utility functions
│   ├── server/                 # Server-side code
│   │   ├── agents/             # AI agents (fact extraction, narrative)
│   │   ├── api/                # tRPC router and procedures
│   │   ├── auth/               # NextAuth configuration
│   │   ├── db/                 # Database schema and client
│   │   └── services/           # Business logic services
│   ├── stores/                 # Zustand state stores
│   ├── styles/                 # Global styles
│   ├── trpc/                   # tRPC client setup
│   └── types/                  # TypeScript type definitions
├── public/                     # Static assets
├── drizzle/                    # Database migrations
└── package.json                # Dependencies
```

## Getting Started

### Prerequisites

- [Bun](https://bun.sh) - JavaScript runtime and package manager
- PostgreSQL database (Neon recommended)
- Google OAuth credentials
- OpenAI API key
- AWS S3 bucket for asset storage

### Installation

1. **Install dependencies:**

```bash
bun install
```

2. **Set up environment variables:**

Copy `.env.example` to `.env` and configure:

```env
# Authentication
AUTH_SECRET=your-auth-secret

# Google OAuth
AUTH_GOOGLE_ID=your-google-client-id
AUTH_GOOGLE_SECRET=your-google-client-secret

# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:password@host/database?sslmode=require

# Replicate (for image/video generation)
REPLICATE_API_KEY=your-replicate-key

# OpenAI
OPENAI_API_KEY=your-openai-key

# AWS S3
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
S3_BUCKET_NAME=your-bucket-name
AWS_REGION=us-east-2

# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Webhook Secret
WEBHOOK_SECRET=your-webhook-secret
```

3. **Set up the database:**

```bash
# Push schema to database
bun run db:push

# Or generate and run migrations
bun run db:generate
bun run db:migrate
```

4. **Run the development server:**

```bash
bun dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Available Scripts

| Command                | Description                         |
| ---------------------- | ----------------------------------- |
| `bun dev`              | Start development server with Turbo |
| `bun run build`        | Build for production                |
| `bun run start`        | Start production server             |
| `bun run check`        | Run lint and typecheck              |
| `bun run lint`         | Run ESLint                          |
| `bun run lint:fix`     | Run ESLint with auto-fix            |
| `bun run typecheck`    | Run TypeScript type checking        |
| `bun run format:check` | Check code formatting               |
| `bun run format:write` | Format code with Prettier           |
| `bun run db:generate`  | Generate Drizzle migrations         |
| `bun run db:push`      | Push schema changes to database     |
| `bun run db:migrate`   | Run database migrations             |
| `bun run db:studio`    | Open Drizzle Studio                 |
| `bun run preview`      | Build and start for preview         |

## Features

### AI-Powered Content Creation

- **Fact Extraction**: Upload PDFs or paste text to extract key educational concepts using AI
- **Narrative Building**: Generate structured educational narratives with hooks, explanations, and conclusions
- **Age-Appropriate Content**: AI considers target audience age and interests for appropriate content

### Video Editor

- **Timeline-Based Editing**: Drag-and-drop timeline with multiple tracks
- **Media Library**: Manage images, videos, and audio assets
- **Real-Time Preview**: Preview video compositions with Remotion
- **Export**: Generate final video compositions

### Content Management

- **Asset Gallery**: Browse and manage all generated assets
- **Session History**: Track previous creation sessions
- **Final Videos**: Access completed video compositions

### Authentication

- Google OAuth via NextAuth.js v5
- Database-backed sessions with Drizzle
- Protected dashboard routes via middleware

### Database

- Drizzle ORM for type-safe queries
- PostgreSQL for data persistence
- Schema includes: users, sessions, video assets, conversations, error reports

### API Layer

- tRPC for end-to-end type safety
- React Query for data fetching and caching
- Server actions for mutations

## Workflow Stages

The content creation workflow progresses through these stages:

1. **CREATED** - Initial session creation
2. **IMAGE_GENERATION** - Generate visual assets from scripts
3. **IMAGE_SELECTION** - User approves generated images
4. **CLIP_GENERATION** - Generate video clips from selected images
5. **CLIP_SELECTION** - User approves video clips
6. **FINAL_COMPOSITION** - Compose final video with overlays and audio
7. **COMPLETE** - Finished content ready for export

## Learn More

To learn more about the technologies used:

- [Next.js Documentation](https://nextjs.org/docs)
- [NextAuth.js Documentation](https://authjs.dev)
- [Drizzle ORM Documentation](https://orm.drizzle.team)
- [tRPC Documentation](https://trpc.io/docs)
- [Remotion Documentation](https://www.remotion.dev/docs)
- [Vercel AI SDK](https://sdk.vercel.ai/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [shadcn/ui Documentation](https://ui.shadcn.com)

## Project Documentation

- [Product Requirements Document](../Docs/MVP_PRD.md) - Complete PRD
- [Architecture Document](../ARCHITECTURE.md) - System architecture and design decisions

## Deployment

### Vercel (Recommended)

1. Push your code to GitHub
2. Import your repository in [Vercel](https://vercel.com)
3. Configure environment variables
4. Deploy

### Other Platforms

This Next.js application can be deployed to any platform that supports Node.js:

- [Railway](https://railway.app)
- [Render](https://render.com)
- [Docker](https://www.docker.com)

See the [Next.js deployment documentation](https://nextjs.org/docs/deployment) for details.

## License

See the main project repository for license information.
