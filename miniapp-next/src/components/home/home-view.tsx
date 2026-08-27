import { useNavigate } from "@tanstack/react-router";
import { Brain, Languages, Settings } from "lucide-react";
import { AppShell } from "@/components/shell/app-shell";
import { Header } from "@/components/shell/header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ServiceRow } from "@/components/shell/service-row";
import { WeatherCard } from "@/components/weather/weather-card";
import { SummaryStrip } from "@/components/home/summary-strip";
import { RatesCard } from "@/components/home/rates-card";
import { TasksCard } from "@/components/home/tasks-card";
import { CalendarCard } from "@/components/home/calendar-card";
import { PasswordCard } from "@/components/home/password-card";
import { useSettings } from "@/lib/stores/settings";
import { haptic } from "@/lib/haptic";

export function HomeView() {
  const navigate = useNavigate();
  const name = useSettings((s) => s.displayName);
  const enabled = useSettings((s) => s.enabledModules);
  const show = (id: "rates" | "tasks" | "calendar" | "passwords" | "fun" | "translate") =>
    enabled === "all" || enabled.includes(id);

  return (
    <AppShell>
      <Header
        title="R2D2"
        subtitle={name ? `Привет, ${name}` : "мини-приложение"}
        right={
          <Button
            variant="secondary"
            size="icon-sm"
            aria-label="Настройки"
            onClick={() => {
              haptic();
              navigate({ to: "/settings" });
            }}
          >
            <Settings className="size-4" />
          </Button>
        }
      />
      <div className="space-y-3">
        <SummaryStrip />
        <WeatherCard />
        {show("rates") ? (
          <div className="px-4">
            <RatesCard />
          </div>
        ) : null}
        {show("tasks") ? (
          <div className="px-4">
            <TasksCard />
          </div>
        ) : null}
        {show("calendar") ? (
          <div className="px-4">
            <CalendarCard />
          </div>
        ) : null}
        {show("passwords") ? (
          <div className="px-4">
            <PasswordCard />
          </div>
        ) : null}
        {show("fun") ? (
          <div className="px-4">
            <Card>
              <ServiceRow
                icon={<Brain className="size-5" />}
                title="Викторины и идеи"
                status="Вопросы и чем заняться"
                onClick={() => {
                  haptic("medium");
                  navigate({ to: "/fun" });
                }}
              />
            </Card>
          </div>
        ) : null}
        {show("translate") ? (
          <div className="px-4">
            <Card>
              <ServiceRow
                icon={<Languages className="size-5" />}
                title="Переводчик и словарь"
                status="EN · ES · RU"
                onClick={() => {
                  haptic("medium");
                  navigate({ to: "/translate" });
                }}
              />
            </Card>
          </div>
        ) : null}
      </div>
    </AppShell>
  );
}
