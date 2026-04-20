import { create } from "zustand";
import type { Level, QuizQuestion } from "../api/types";

export type QuestionOutcome = "correct" | "wrong" | "skipped";

export type ReportItem = {
  character_id: number;
  name_cn: string;
  main_series: string;
};

type SessionStore = {
  level: Level | null;
  questions: QuizQuestion[];
  currentIndex: number;
  outcomes: (QuestionOutcome | null)[];
  /** User's selected character_id per question (after confirm) */
  selectedIds: (number | null)[];
  revealed: boolean;
  score: number;
  setQuiz: (level: Level, questions: QuizQuestion[]) => void;
  setSelected: (characterId: number) => void;
  confirm: () => void;
  skip: () => void;
  next: () => void;
  clear: () => void;
};

function initialArrays(n: number) {
  return {
    outcomes: Array.from({ length: n }, () => null as QuestionOutcome | null),
    selectedIds: Array.from({ length: n }, () => null as number | null),
  };
}

export const useSessionStore = create<SessionStore>((set, get) => ({
  level: null,
  questions: [],
  currentIndex: 0,
  outcomes: [],
  selectedIds: [],
  revealed: false,
  score: 0,

  clear: () =>
    set({
      level: null,
      questions: [],
      currentIndex: 0,
      outcomes: [],
      selectedIds: [],
      revealed: false,
      score: 0,
    }),

  setQuiz: (level, questions) => {
    const { outcomes, selectedIds } = initialArrays(questions.length);
    set({
      level,
      questions,
      currentIndex: 0,
      outcomes,
      selectedIds,
      revealed: false,
      score: 0,
    });
  },

  setSelected: (characterId) => {
    const { currentIndex, revealed, selectedIds, questions } = get();
    if (revealed || currentIndex >= questions.length) return;
    const next = [...selectedIds];
    next[currentIndex] = characterId;
    set({ selectedIds: next });
  },

  confirm: () => {
    const {
      currentIndex,
      revealed,
      questions,
      selectedIds,
      outcomes,
      score,
    } = get();
    if (revealed || currentIndex >= questions.length) return;
    const q = questions[currentIndex];
    const selected = selectedIds[currentIndex];
    if (selected == null) return;

    const answer = q.answer_character_id;
    let delta = 0;
    let out: QuestionOutcome;
    if (selected === answer) {
      delta = 10;
      out = "correct";
    } else {
      delta = -2;
      out = "wrong";
    }
    const oc = [...outcomes];
    oc[currentIndex] = out;
    set({
      revealed: true,
      outcomes: oc,
      score: score + delta,
    });
  },

  skip: () => {
    const { currentIndex, revealed, questions, outcomes, score } = get();
    if (revealed || currentIndex >= questions.length) return;
    const oc = [...outcomes];
    oc[currentIndex] = "skipped";
    const sid = get().selectedIds;
    const nextSid = [...sid];
    nextSid[currentIndex] = null;
    set({
      revealed: true,
      outcomes: oc,
      selectedIds: nextSid,
      score,
    });
  },

  next: () => {
    const { currentIndex, questions, revealed } = get();
    if (!revealed) return;
    if (currentIndex + 1 >= questions.length) return;
    set({
      currentIndex: currentIndex + 1,
      revealed: false,
    });
  },
}));

export function buildReport(
  questions: QuizQuestion[],
  outcomes: (QuestionOutcome | null)[],
): ReportItem[] {
  const items: ReportItem[] = [];
  questions.forEach((q, i) => {
    if (outcomes[i] !== "correct") return;
    if (q.type === "image_to_name") {
      const o = q.options.find((x) => x.character_id === q.answer_character_id);
      if (o) {
        items.push({
          character_id: q.answer_character_id,
          name_cn: o.name_cn,
          main_series: o.main_series,
        });
      }
    } else {
      items.push({
        character_id: q.answer_character_id,
        name_cn: q.name_cn,
        main_series: q.main_series,
      });
    }
  });
  return items;
}

export function levelLabel(level: Level): string {
  switch (level) {
    case "easy":
      return "初级";
    case "medium":
      return "中级";
    case "hard":
      return "高级";
    default:
      return level;
  }
}
