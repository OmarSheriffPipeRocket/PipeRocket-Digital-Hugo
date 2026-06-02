import type { Context } from "https://edge.netlify.com";

// Add X-Robots-Tag: noindex on the Netlify staging subdomain
// (piperocketdigital.netlify.app and *--piperocketdigital.netlify.app
// preview URLs) so Google deindexes them and only piperocket.digital
// ranks. Production custom domain is untouched.
export default async (request: Request, context: Context) => {
  const response = await context.next();
  const host = new URL(request.url).hostname;
  if (host.endsWith(".netlify.app")) {
    response.headers.set("X-Robots-Tag", "noindex, nofollow");
  }
  return response;
};

export const config = { path: "/*" };
