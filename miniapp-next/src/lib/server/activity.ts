import { createServerFn } from "@tanstack/react-start";
import { fetchJson } from "./cache";

export type ActivityIdea = {
  activity: string;
  type?: string;
  participants?: number;
  price?: number;
  accessibility?: number;
  link?: string;
};

export const getActivity = createServerFn({ method: "GET" }).handler(async (): Promise<ActivityIdea> => {
  const raw = await fetchJson<ActivityIdea>("https://bored.api.lewagon.com/api/activity", 8000);
  if (!raw?.activity) throw new Error("Нет идеи");
  return {
    activity: raw.activity,
    type: raw.type,
    participants: raw.participants,
    price: raw.price,
    accessibility: raw.accessibility,
    link: raw.link,
  };
});
