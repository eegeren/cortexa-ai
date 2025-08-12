// web/lib/auth.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const KEY = "ctx_token";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(KEY);
}
function setToken(t: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem(KEY, t);
}

async function fetchGuest(): Promise<string> {
  const r = await fetch(`${API_URL}/auth/guest`, { method: "POST" });
  if (!r.ok) throw new Error("guest token alınamadı");
  const j = await r.json();
  if (!j?.token) throw new Error("guest token boş geldi");
  setToken(j.token);
  return j.token;
}

// sayfa açıldığında bir kere çağır: token varsa dokunma, yoksa al
async function ensureToken(): Promise<string> {
  const t = getToken();
  if (t) return t;
  return fetchGuest();
}

// Tek yerden POST/GET vb. istek yap, header ekle ve 401'de yenile
async function api<T = any>(path: string, init: RequestInit = {}): Promise<T> {
  // token varsa kullan, yoksa al
  let token = getToken() || (await fetchGuest());

  const doFetch = async (): Promise<Response> => {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(init.headers as Record<string, string>),
    };
    if (token) headers.Authorization = `Bearer ${token}`;

    return fetch(`${API_URL}${path}`, {
      ...init,
      headers,
    });
  };

  // ilk deneme
  let res = await doFetch();

  // 401 ise bir kere token yenileyip tekrar dene
  if (res.status === 401) {
    token = await fetchGuest();
    res = await doFetch();
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }
  return (await res.json()) as T;
}

const auth = { ensureToken, api, getToken, setToken };
export default auth;