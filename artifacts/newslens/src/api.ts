import {
  setBaseUrl,
  listCards,
  getCard,
  getUserProfile,
  updateUserProfile,
  swipeCard,
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
// null keeps fetch calls relative to the current origin.
setBaseUrl(null);

// ---------------------------------------------------------------------------
// Typed API facade — all backend calls go through these functions.
// Mirrors api.js from the UI spec (section 14), adapted for TypeScript.
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

export { setBaseUrl };
export type { Card, CardList, ListCardsParams, ApiUserProfile, UserProfileInput };
