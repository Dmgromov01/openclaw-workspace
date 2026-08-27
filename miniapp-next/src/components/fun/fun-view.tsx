import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Brain, Lightbulb, Shuffle } from "lucide-react";
import { getQuiz } from "@/lib/server/quiz";
import { getActivity } from "@/lib/server/activity";
import { AppShell } from "@/components/shell/app-shell";
import { Header } from "@/components/shell/header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ServiceRow } from "@/components/shell/service-row";
import { haptic } from "@/lib/haptic";

function priceLabel(p?: number) {
  if (p == null) return "";
  if (p === 0) return "бесплатно";
  if (p < 0.3) return "недорого";
  return "платно";
}

export function FunView() {
  const [reveal, setReveal] = useState(false);
  const quiz = useQuery({ queryKey: ["quiz"], queryFn: () => getQuiz() });
  const activity = useQuery({ queryKey: ["activity"], queryFn: () => getActivity() });

  return (
    <AppShell>
      <Header
        title="Викторины и идеи"
        subtitle="Вопросы и занятия"
        backTo="/"
        right={
          <Button
            variant="secondary"
            size="icon-sm"
            aria-label="Новый вопрос"
            onClick={() => {
              haptic("light");
              setReveal(false);
              void quiz.refetch();
            }}
          >
            <Shuffle className="size-4" />
          </Button>
        }
      />
      <div className="space-y-3 px-4">
        <Card>
          <ServiceRow
            accent
            icon={<Brain className="size-5" />}
            title="Вопрос для викторины"
            status="Open Trivia DB"
            chevron={false}
            trailing={
              <Button
                size="sm"
                onClick={() => {
                  haptic("light");
                  setReveal(false);
                  void quiz.refetch();
                }}
                disabled={quiz.isFetching}
              >
                {quiz.isFetching ? "…" : "Новый"}
              </Button>
            }
          />
          <div className="space-y-3 border-t border-border px-4 py-3">
            {quiz.isError ? <p className="text-sm text-destructive">Не удалось загрузить вопрос.</p> : null}
            {quiz.data ? (
              <>
                <div className="flex flex-wrap gap-1.5">
                  <Badge tone="accent">{quiz.data.category}</Badge>
                  {quiz.data.difficulty ? <Badge>{quiz.data.difficulty}</Badge> : null}
                </div>
                <p className="text-sm font-semibold leading-snug">{quiz.data.question}</p>
                {!reveal ? (
                  <Button
                    variant="solid"
                    className="w-full"
                    onClick={() => {
                      haptic("medium");
                      setReveal(true);
                    }}
                  >
                    Показать ответ
                  </Button>
                ) : (
                  <div className="rounded-xl border border-success/25 bg-success/10 p-3.5">
                    <div className="text-xs font-bold uppercase tracking-wide text-success">Ответ</div>
                    <div className="text-sm font-semibold">{quiz.data.answer}</div>
                  </div>
                )}
              </>
            ) : (
              <p className="py-6 text-center text-xs text-muted-foreground">Загружаем вопрос…</p>
            )}
          </div>
        </Card>

        <Card>
          <ServiceRow
            icon={<Lightbulb className="size-5" />}
            title="Чем заняться"
            status="Bored API"
            chevron={false}
            trailing={
              <Button
                variant="solid"
                size="sm"
                onClick={() => {
                  haptic("light");
                  void activity.refetch();
                }}
                disabled={activity.isFetching}
              >
                {activity.isFetching ? "…" : "Идея"}
              </Button>
            }
          />
          <div className="space-y-3 border-t border-border px-4 py-3">
            {activity.isError ? <p className="text-sm text-destructive">Не удалось подобрать занятие.</p> : null}
            {activity.data ? (
              <>
                <p className="text-sm font-semibold leading-snug">{activity.data.activity}</p>
                <div className="flex flex-wrap gap-1.5">
                  {activity.data.type ? <Badge tone="accent">{activity.data.type}</Badge> : null}
                  {activity.data.participants ? (
                    <Badge>
                      {activity.data.participants}{" "}
                      {activity.data.participants === 1 ? "участник" : "участника"}
                    </Badge>
                  ) : null}
                  {priceLabel(activity.data.price) ? (
                    <Badge tone="success">{priceLabel(activity.data.price)}</Badge>
                  ) : null}
                </div>
              </>
            ) : (
              <p className="py-6 text-center text-xs text-muted-foreground">Подбираем занятие…</p>
            )}
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
