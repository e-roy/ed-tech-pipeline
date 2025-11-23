import { DrizzleAdapter } from "@auth/drizzle-adapter";
import { type DefaultSession, type NextAuthConfig } from "next-auth";
import DiscordProvider from "next-auth/providers/discord";
import GoogleProvider from "next-auth/providers/google";
import Credentials from "next-auth/providers/credentials";

import { db } from "@/server/db";
import {
  accounts,
  sessions,
  users,
  verificationTokens,
} from "@/server/db/schema";
import { eq, or } from "drizzle-orm";
import bcrypt from "bcryptjs";
import { env } from "@/env";
import { UserRole } from "@/types";

/**
 * Module augmentation for `next-auth` types. Allows us to add custom properties to the `session`
 * object and keep type safety.
 *
 * @see https://next-auth.js.org/getting-started/typescript#module-augmentation
 */
declare module "next-auth" {
  interface Session extends DefaultSession {
    user: {
      id: string;
      role: UserRole;
    } & DefaultSession["user"];
  }

  interface User {
    role: UserRole;
  }
}

declare module "@auth/core/adapters" {
  interface AdapterUser {
    role: UserRole;
  }
}

/**
 * Options for NextAuth.js used to configure adapters, providers, callbacks, etc.
 *
 * @see https://next-auth.js.org/configuration/options
 */
export const authConfig = {
  providers: [
    DiscordProvider,
    GoogleProvider({
      clientId: env.AUTH_GOOGLE_ID,
      clientSecret: env.AUTH_GOOGLE_SECRET,
    }),
    Credentials({
      name: "credentials",
      credentials: {
        username: { label: "Username or Email", type: "text" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.username || !credentials?.password) {
          return null;
        }

        const usernameOrEmail = credentials.username as string;
        const password = credentials.password as string;

        // Find user by username or email
        const [user] = await db
          .select()
          .from(users)
          .where(
            or(
              eq(users.username, usernameOrEmail),
              eq(users.email, usernameOrEmail),
            ),
          )
          .limit(1);

        if (!user?.password) {
          return null;
        }

        // Verify password
        const isValidPassword = await bcrypt.compare(password, user.password);

        if (!isValidPassword) {
          return null;
        }

        // Return user object in the format NextAuth expects
        return {
          id: user.id,
          email: user.email,
          name: user.name,
          username: user.username,
          image: user.image,
          role: (user.role ?? "user") as UserRole,
        };
      },
    }),
  ],
  adapter: DrizzleAdapter(db, {
    usersTable: users,
    accountsTable: accounts,
    sessionsTable: sessions,
    verificationTokensTable: verificationTokens,
  }),
  session: {
    strategy: "database", // Force database sessions when adapter is present
  },
  callbacks: {
    async signIn() {
      // For Credentials provider, we need to ensure the user exists in the database
      // The user should already exist since we're using our own users table
      // Return true to allow sign in
      return true;
    },
    async session({ session, user }) {
      // With database sessions, user is always available
      if (user) {
        session.user = {
          ...session.user,
          id: user.id,
          role: (user as any).role as UserRole || UserRole.USER,
        };
      }
      return session;
    },
  },
} satisfies NextAuthConfig;
