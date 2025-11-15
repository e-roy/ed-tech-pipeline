"use server";

import { signIn } from "@/server/auth";

export async function handleGoogleSignIn() {
  await signIn("google", { redirectTo: "/dashboard" });
}

