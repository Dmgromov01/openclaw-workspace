import type { ReactNode } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@/lib/query-client";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "sonner";

export function AuthProvider({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        {children}
        <Toaster
          position="bottom-center"
          toastOptions={{
            className:
              "!bg-foreground !text-background !border-none !rounded-xl !text-sm !font-medium",
          }}
        />
      </ThemeProvider>
    </QueryClientProvider>
  );
}
