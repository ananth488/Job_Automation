/**
 * Helper functions to synchronize access_token with browser cookies.
 * Next.js Edge Middleware inspects request cookies to guard routes.
 */

export function setAuthCookie(token: string, days = 7) {
  if (typeof document === 'undefined') return;
  const maxAge = days * 24 * 60 * 60;
  document.cookie = `access_token=${encodeURIComponent(token)}; path=/; max-age=${maxAge}; SameSite=Lax`;
}

export function clearAuthCookie() {
  if (typeof document === 'undefined') return;
  document.cookie = 'access_token=; path=/; max-age=0; SameSite=Lax';
}

export function getAuthCookie(): string | null {
  if (typeof document === 'undefined') return null;
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [name, ...rest] = cookie.trim().split('=');
    if (name === 'access_token') {
      return decodeURIComponent(rest.join('='));
    }
  }
  return null;
}

