"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { loginAction, signupAction } from "@/server/actions/auth";
import { GoogleSignInForm } from "@/components/login/google-signin-form";
import { SubmitButton } from "@/components/login/submit-button";

interface AuthFormProps {
  error?: string;
  success?: string;
  defaultTab?: "login" | "signup";
}

export function AuthForm({
  error,
  success,
  defaultTab = "login",
}: AuthFormProps) {
  return (
    <Card className="mt-4 sm:mx-auto sm:w-full sm:max-w-md">
      <CardContent>
        <div className="sm:mx-auto sm:w-full sm:max-w-sm">
          <h2 className="text-foreground text-center text-xl font-semibold">
            Log in or create account
          </h2>
          {error && (
            <div className="bg-destructive/15 text-destructive mt-4 rounded-md p-3 text-sm">
              {error}
            </div>
          )}
          {success && (
            <div className="mt-4 rounded-md bg-green-500/15 p-3 text-sm text-green-600 dark:text-green-400">
              {success}
            </div>
          )}

          <Tabs defaultValue={defaultTab} className="mt-6">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="login">Sign In</TabsTrigger>
              <TabsTrigger value="signup">Sign Up</TabsTrigger>
            </TabsList>

            <TabsContent value="login" className="mt-4 space-y-4">
              <form action={loginAction} className="space-y-4">
                <div>
                  <Label
                    htmlFor="username-login"
                    className="text-foreground dark:text-foreground text-sm font-medium"
                  >
                    Username or Email
                  </Label>
                  <Input
                    type="text"
                    id="username-login"
                    name="username"
                    autoComplete="username"
                    placeholder="username or email@example.com"
                    className="mt-2"
                    required
                  />
                </div>
                <div>
                  <Label
                    htmlFor="password-login"
                    className="text-foreground dark:text-foreground text-sm font-medium"
                  >
                    Password
                  </Label>
                  <Input
                    type="password"
                    id="password-login"
                    name="password"
                    autoComplete="current-password"
                    placeholder="**************"
                    className="mt-2"
                    required
                  />
                </div>
                <SubmitButton className="mt-4 w-full py-2 font-medium">
                  Sign in
                </SubmitButton>
              </form>

              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <Separator className="w-full" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-background text-muted-foreground px-2">
                    or with
                  </span>
                </div>
              </div>

              <GoogleSignInForm />
            </TabsContent>

            <TabsContent value="signup" className="mt-4 space-y-4">
              <form action={signupAction} className="space-y-4">
                <div>
                  <Label
                    htmlFor="name-signup"
                    className="text-foreground dark:text-foreground text-sm font-medium"
                  >
                    Name
                  </Label>
                  <Input
                    type="text"
                    id="name-signup"
                    name="name"
                    autoComplete="name"
                    placeholder="Name"
                    className="mt-2"
                    required
                  />
                </div>

                <div>
                  <Label
                    htmlFor="email-signup"
                    className="text-foreground dark:text-foreground text-sm font-medium"
                  >
                    Email
                  </Label>
                  <Input
                    type="email"
                    id="email-signup"
                    name="email"
                    autoComplete="email"
                    placeholder="email@example.com"
                    className="mt-2"
                    required
                  />
                </div>

                <div>
                  <Label
                    htmlFor="password-signup"
                    className="text-foreground dark:text-foreground text-sm font-medium"
                  >
                    Password
                  </Label>
                  <Input
                    type="password"
                    id="password-signup"
                    name="password"
                    autoComplete="new-password"
                    placeholder="Password"
                    className="mt-2"
                    required
                    minLength={8}
                  />
                </div>

                <div>
                  <Label
                    htmlFor="confirm-password-signup"
                    className="text-foreground dark:text-foreground text-sm font-medium"
                  >
                    Confirm password
                  </Label>
                  <Input
                    type="password"
                    id="confirm-password-signup"
                    name="confirm-password"
                    autoComplete="new-password"
                    placeholder="Password"
                    className="mt-2"
                    required
                    minLength={8}
                  />
                </div>

                <SubmitButton className="mt-4 w-full py-2 font-medium">
                  Create account
                </SubmitButton>
              </form>
            </TabsContent>
          </Tabs>

          <p className="text-muted-foreground dark:text-muted-foreground mt-4 text-xs">
            By signing in, you agree to our{" "}
            <a href="#" className="underline underline-offset-4">
              terms of service
            </a>{" "}
            and{" "}
            <a href="#" className="underline underline-offset-4">
              privacy policy
            </a>
            .
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
