import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isProtectedRoute = createRouteMatcher([
  "/dashboard(.*)",
  "/account(.*)",
  "/transaction(.*)",
]);

export default clerkMiddleware((auth, req) => {
  if (isProtectedRoute(req)) {
    auth().protect();
  }
});

// IMPORTANT: This matcher MUST be EXACT for Clerk apps
export const config = {
  matcher: [
    "/((?!.+\\.(js|css|png|jpg|jpeg|gif|svg|ico|webp|woff|woff2)$|_next).*)",
    "/",
    "/(api|trpc)(.*)",
  ],
};
