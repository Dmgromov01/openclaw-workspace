import { createFileRoute } from "@tanstack/react-router";
import { CalendarView } from "@/components/calendar/calendar-view";

export const Route = createFileRoute("/calendar")({ component: CalendarView });
