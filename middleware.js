import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

// Protect these routes only
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

// ✅ This matcher avoids capturing groups (Next.js 15 requirement)
export const config = {
  matcher: [
    "/((?!_next/).*)",        // run on all app routes except _next
    "/(api|trpc)(.*)",        // allow API routing
  ],
};
