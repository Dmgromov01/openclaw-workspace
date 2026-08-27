import { createFileRoute } from "@tanstack/react-router";
import { TranslateView } from "@/components/translate/translate-view";

export const Route = createFileRoute("/translate")({ component: TranslateView });
