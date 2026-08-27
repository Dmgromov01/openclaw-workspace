import { createFileRoute } from "@tanstack/react-router";
import { FunView } from "@/components/fun/fun-view";

export const Route = createFileRoute("/fun")({ component: FunView });
