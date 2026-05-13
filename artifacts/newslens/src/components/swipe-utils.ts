import { useSwipeCard } from "@/api";

export function useSaveSwipe() {
  const swipeCard = useSwipeCard();
  return function saveSwipe(cardId: string, direction: "left" | "right") {
    swipeCard.mutate({ id: cardId, data: { direction, user_id: "default_user" } });
  };
}
