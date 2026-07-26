import {
  setBaseUrl,
  listCards,
  getCard,
  getUserProfile,
  updateUserProfile,
  swipeCard,
  // React Query hooks — re-exported so all components import from this module
  useListCards,
  getListCardsQueryKey,
  useUpdateUserProfile,
  useSwipeCard,
  useGetCard,
  useGetUserProfile,
} from "@workspace/api-client-react";
import { useQuery } from "@tanstack/react-query";
import type {
  Card,
  CardList,
  ListCardsParams,
  GetUserProfileParams,
  UserProfile as ApiUserProfile,
  UserProfileInput,
  SwipeInputDirection,
} from "@workspace/api-client-react";

// All API calls use relative paths (/api/...).
// In development, Vite proxies /api → FastAPI on port 8000.
// In production, the Replit proxy routes /api → the api-server → FastAPI.
// The backend registers all routes under the /api prefix (e.g. /api/cards, /api/user/profile).
// null keeps fetch calls relative to the current origin — correct in both environments.
setBaseUrl(null);

// ---------------------------------------------------------------------------
// Typed async facade — mirrors api.js from UI_SPEC section 14.
// All backend I/O goes through these functions.
// ---------------------------------------------------------------------------

export async function getCards(params?: ListCardsParams): Promise<CardList> {
  return listCards(params);
}

// ---------------------------------------------------------------------------
// Personalized feed
//
// HAND-WRITTEN, not generated. `/cards/personalized` is declared in
// lib/api-spec/openapi.yaml, but the checked-in Orval output predates it. Re-run
// `pnpm orval` and this block can be deleted in favour of the generated hook.
// Kept deliberately thin so that swap is a one-line change at the call site.
// ---------------------------------------------------------------------------

export interface PersonalizedCardsParams {
  user_id: string;
  domain?: string | null;
  geo?: string | null;
  limit?: number;
  page?: number;
}

export async function getPersonalizedCards(
  params: PersonalizedCardsParams,
): Promise<CardList> {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
  });

  const res = await fetch(`/api/cards/personalized?${qs.toString()}`);
  if (!res.ok) {
    throw new Error(`Personalized feed failed (${res.status})`);
  }
  return (await res.json()) as CardList;
}

export function getPersonalizedCardsQueryKey(params: PersonalizedCardsParams) {
  return ["/api/cards/personalized", params] as const;
}

/**
 * Personalized feed, with the plain feed as a fallback.
 *
 * `enabled` is what keeps this honest: until a profile exists on the server there
 * is nothing to personalize against, so the query never fires and the caller falls
 * back to useListCards. A 404 (no profile) is not retried.
 */
export function usePersonalizedCards(
  params: PersonalizedCardsParams,
  options?: { enabled?: boolean },
) {
  return useQuery({
    queryKey: getPersonalizedCardsQueryKey(params),
    queryFn: () => getPersonalizedCards(params),
    enabled: options?.enabled ?? true,
    retry: false,
  });
}

export async function fetchCard(id: string): Promise<Card> {
  return getCard(id);
}

export async function getProfile(
  params?: GetUserProfileParams,
): Promise<ApiUserProfile | null> {
  try {
    return await getUserProfile(params as GetUserProfileParams);
  } catch {
    return null;
  }
}

export async function saveProfile(data: UserProfileInput): Promise<ApiUserProfile> {
  return updateUserProfile(data);
}

export async function recordSwipe(
  cardId: string,
  direction: SwipeInputDirection,
): Promise<void> {
  await swipeCard(cardId, { direction });
}

// ---------------------------------------------------------------------------
// React Query hook exports — import from here, not from @workspace/api-client-react
// ---------------------------------------------------------------------------
export {
  useListCards,
  getListCardsQueryKey,
  useUpdateUserProfile,
  useSwipeCard,
  useGetCard,
  useGetUserProfile,
  setBaseUrl,
};

export type {
  Card,
  CardList,
  ListCardsParams,
  ApiUserProfile,
  UserProfileInput,
  SwipeInputDirection,
};
