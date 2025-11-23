"use server";

import { db } from "@/server/db";
import { users, sessions, accounts } from "@/server/db/schema";
import { eq, or } from "drizzle-orm";
import bcrypt from "bcryptjs";
import { redirect } from "next/navigation";
import { randomBytes } from "crypto";
import { cookies } from "next/headers";

async function createDatabaseSession(userId: string) {
  // Generate a session token (NextAuth format - base64url encoded random bytes)
  const sessionToken = randomBytes(32).toString("base64url");
  // Session expires in 30 days (matching NextAuth default)
  const expires = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);

  // Create session in database
  await db.insert(sessions).values({
    sessionToken,
    userId,
    expires,
  });

  return sessionToken;
}

export async function loginAction(formData: FormData) {
  const username = formData.get("username") as string;
  const password = formData.get("password") as string;

  if (!username || !password) {
    redirect("/login?error=Username/email and password are required");
  }

  // First, verify credentials and get user
  const [user] = await db
    .select()
    .from(users)
    .where(or(eq(users.username, username), eq(users.email, username)))
    .limit(1);

  if (!user?.password) {
    redirect("/login?error=Invalid username/email or password");
  }

  // Verify password
  const isValidPassword = await bcrypt.compare(password, user.password);
  if (!isValidPassword) {
    redirect("/login?error=Invalid username/email or password");
  }

  // Create database session manually (Credentials provider doesn't create DB sessions automatically)
  const sessionToken = await createDatabaseSession(user.id);

  // Set the session cookie so NextAuth recognizes it
  const cookieStore = await cookies();
  cookieStore.set("authjs.session-token", sessionToken, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 30 * 24 * 60 * 60, // 30 days
  });

  // Redirect to dashboard
  redirect("/dashboard");
}

export async function signupAction(formData: FormData) {
  const name = formData.get("name") as string;
  const email = formData.get("email") as string;
  const password = formData.get("password") as string;
  const confirmPassword = formData.get("confirm-password") as string;

  // Validation
  if (!name || !email || !password || !confirmPassword) {
    redirect("/login?error=All fields are required&mode=signup");
  }

  if (password !== confirmPassword) {
    redirect("/login?error=Passwords do not match&mode=signup");
  }

  if (password.length < 8) {
    redirect(
      "/login?error=Password must be at least 8 characters long&mode=signup",
    );
  }

  // Check if email already exists
  const [existingEmail] = await db
    .select()
    .from(users)
    .where(eq(users.email, email))
    .limit(1);

  if (existingEmail) {
    redirect("/login?error=Email already exists&mode=signup");
  }

  // Hash password - password is guaranteed to be a string at this point
  const hashedPassword: string = await bcrypt.hash(password, 10);

  // Create user (username is optional, use email as fallback)
  let newUser;
  try {
    const [insertedUser] = await db
      .insert(users)
      .values({
        name,
        email,
        username: email.split("@")[0], // Use email prefix as username
        password: hashedPassword,
        role: "user", // Set default role
      })
      .returning();
    newUser = insertedUser;

    if (!newUser) {
      console.error("User creation failed: No user returned from insert");
      redirect(
        "/login?error=Failed to create account. Please try again.&mode=signup",
      );
    }

    console.log("User created successfully:", {
      id: newUser.id,
      email: newUser.email,
    });

    // Create account record for credentials provider
    await db.insert(accounts).values({
      userId: newUser.id,
      type: "email",
      provider: "credentials",
      providerAccountId: newUser.email,
    });
  } catch (error) {
    console.error("Signup error:", error);
    redirect(
      "/login?error=Failed to create account. Please try again.&mode=signup",
    );
  }

  // Create database session manually (Credentials provider doesn't create DB sessions automatically)
  const sessionToken = await createDatabaseSession(newUser.id);

  // Set the session cookie so NextAuth recognizes it
  const cookieStore = await cookies();
  cookieStore.set("authjs.session-token", sessionToken, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 30 * 24 * 60 * 60, // 30 days
  });

  // Redirect to dashboard
  redirect("/dashboard");
}
