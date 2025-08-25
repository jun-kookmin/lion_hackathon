# Overview

This is a full-stack web application built with React on the frontend and Express.js on the backend. The application appears to be a location-based service or recommendation platform, featuring a mobile-first design with Korean language support. The frontend uses modern React patterns with TypeScript, while the backend provides REST API endpoints with PostgreSQL database integration through Drizzle ORM.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Framework**: React 18 with TypeScript and Vite for build tooling
- **Styling**: Tailwind CSS with shadcn/ui component library for consistent design system
- **Routing**: Wouter for lightweight client-side routing
- **State Management**: TanStack Query (React Query) for server state management
- **Form Handling**: React Hook Form with Zod validation schemas
- **UI Components**: Extensive use of Radix UI primitives wrapped in custom shadcn/ui components

## Backend Architecture
- **Runtime**: Node.js with Express.js framework
- **Language**: TypeScript with ES modules
- **API Design**: RESTful API structure with `/api` prefix for all endpoints
- **Development**: tsx for TypeScript execution and hot reloading
- **Build Process**: esbuild for production bundling with external package handling

## Data Storage
- **Database**: PostgreSQL with Neon serverless database driver
- **ORM**: Drizzle ORM for type-safe database operations
- **Schema Management**: Drizzle Kit for migrations and schema management
- **Current Schema**: Basic user table with id, username, and password fields
- **Development Storage**: In-memory storage implementation for development/testing

## Authentication & Session Management
- **Session Storage**: PostgreSQL-based sessions using connect-pg-simple
- **Session Configuration**: Prepared for cookie-based session management

## Development Tools & Configuration
- **Build System**: Vite with React plugin and custom path aliases
- **Code Quality**: TypeScript strict mode with comprehensive type checking
- **Styling**: PostCSS with Tailwind CSS and autoprefixer
- **Asset Handling**: Support for attached assets and Figma exports
- **Development Enhancements**: Replit-specific plugins for error overlay and cartographer

# External Dependencies

## Core Framework Dependencies
- **@neondatabase/serverless**: Serverless PostgreSQL driver for Neon database
- **drizzle-orm**: Type-safe ORM for database operations
- **express**: Web application framework for Node.js
- **react**: UI library for building user interfaces
- **vite**: Fast build tool and development server

## UI Component Libraries
- **@radix-ui/react-***: Comprehensive set of headless UI primitives (accordion, dialog, dropdown, forms, etc.)
- **@tanstack/react-query**: Server state management and caching
- **tailwindcss**: Utility-first CSS framework
- **class-variance-authority**: Utility for creating type-safe component variants
- **lucide-react**: Icon library for React components

## Development & Build Tools
- **typescript**: Static type checking
- **tsx**: TypeScript execution engine
- **esbuild**: Fast JavaScript bundler
- **drizzle-kit**: Database schema management and migration tool
- **@replit/vite-plugin-***: Replit-specific development enhancements

## Form & Validation
- **react-hook-form**: Forms with easy validation
- **@hookform/resolvers**: Validation resolvers for react-hook-form
- **zod**: Schema validation library
- **drizzle-zod**: Integration between Drizzle ORM and Zod

## Utility Libraries
- **date-fns**: Date manipulation library
- **clsx** & **tailwind-merge**: Utility functions for conditional CSS classes
- **wouter**: Minimalist routing for React
- **cmdk**: Command palette component