import { createServerFn } from "@tanstack/react-start";
import { fetchJson } from "./cache";
import { decodeEntities } from "@/lib/sanitize";

export type QuizClue = {
  question: string;
  answer: string;
  category: string;
  difficulty?: string;
};

type Trivia = {
  results?: {
    question: string;
    correct_answer: string;
    category: string;
    difficulty: string;
  }[];
};

export const getQuiz = createServerFn({ method: "GET" }).handler(async (): Promise<QuizClue> => {
  const raw = await fetchJson<Trivia>("https://opentdb.com/api.php?amount=1&type=multiple", 8000);
  const row = raw.results?.[0];
  if (!row) throw new Error("Нет вопроса");
  return {
    question: decodeEntities(row.question),
    answer: decodeEntities(row.correct_answer),
    category: decodeEntities(row.category),
    difficulty: row.difficulty,
  };
});
