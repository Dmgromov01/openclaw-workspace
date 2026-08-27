import { createFileRoute } from "@tanstack/react-router";
import { ArchiveView } from "@/components/tasks/archive-view";

export const Route = createFileRoute("/archive")({ component: ArchiveView });
