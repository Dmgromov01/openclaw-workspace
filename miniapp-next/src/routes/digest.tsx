import { createFileRoute } from "@tanstack/react-router";
import { DigestView } from "@/components/digest/digest-view";

export const Route = createFileRoute("/digest")({ component: DigestView });
