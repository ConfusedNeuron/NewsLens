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
