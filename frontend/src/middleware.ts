import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Public routes accessible without authentication
const PUBLIC_PATHS = ['/login', '/register'];

export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const token = request.cookies.get('access_token')?.value;

  const isPublicPath = PUBLIC_PATHS.some(
    (path) => pathname === path || pathname.startsWith(`${path}/`)
  );

  // 1. If unauthenticated user tries to access a protected route, redirect to /login
  if (!token && !isPublicPath) {
    const loginUrl = new URL('/login', request.url);
    if (pathname !== '/') {
      loginUrl.searchParams.set('redirect', `${pathname}${search}`);
    }
    return NextResponse.redirect(loginUrl);
  }

  // 2. If authenticated user tries to access /login, /register, or the root path /, redirect to /dashboard
  if (token && (isPublicPath || pathname === '/')) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // 3. Allow valid requests
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - api routes
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - Public static files (.svg, .png, .jpg, .jpeg, .gif, .webp, .ico, .css, .js)
     */
    '/((?!api|_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico|css|js)$).*)',
  ],
};

