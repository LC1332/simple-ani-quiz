import type {
  ExploreCharacter,
  ExploreSearchResponse,
  Level,
  QuizResponse,
  RegenerateCosResponse,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function cosImageUrl(cosImageId: number): string {
  return `${API_BASE}/images/cos/${cosImageId}.jpg`;
}

export function portraitUrl(characterId: number): string {
  return `${API_BASE}/images/portrait/${characterId}.jpg`;
}

export async function fetchBanner(limit = 60): Promise<number[]> {
  const data = await getJson<{ cos_image_ids: number[] }>(
    `/api/banner?limit=${limit}`,
  );
  return data.cos_image_ids;
}

export async function fetchQuiz(level: Level, n = 10): Promise<QuizResponse> {
  return getJson<QuizResponse>(`/api/quiz?level=${level}&n=${n}`);
}

export async function fetchExploreCharacter(
  id: number,
): Promise<ExploreCharacter | null> {
  const res = await fetch(`${API_BASE}/api/explore/character/${id}`);
  if (res.status === 404) return null;
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json() as Promise<ExploreCharacter>;
}

export async function fetchExploreRandom(): Promise<ExploreCharacter> {
  return getJson<ExploreCharacter>(`/api/explore/random`);
}

export async function searchExplore(
  q: string,
  limit = 20,
): Promise<ExploreSearchResponse> {
  const params = new URLSearchParams({ q, limit: String(limit) });
  return getJson<ExploreSearchResponse>(`/api/explore/search?${params}`);
}

export async function regenerateCos(body: {
  character_id: number;
  prompt: string;
  size: string;
  api_key?: string;
}): Promise<RegenerateCosResponse> {
  const res = await fetch(`${API_BASE}/api/explore/regenerate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const data = (await res.json().catch(() => ({}))) as { detail?: string };
    throw new Error(data?.detail || `HTTP ${res.status}`);
  }
  return res.json() as Promise<RegenerateCosResponse>;
}
