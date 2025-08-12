// web/lib/api.ts
import { ensureToken, getToken } from "./auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function doPost(path: string, body: any) {
  const token = getToken();
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });
  return res;
}

export async function apiPost(path: string, body: any) {
  // token yoksa veya expired ise otomatik al
  await ensureToken();
  let res = await doPost(path, body);

  // 401 alırsak token’ı yenileyip tek kez daha dene
  if (res.status === 401) {
    await ensureToken();
    res = await doPost(path, body);
  }

  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText} ${txt}`);
  }
  return res.json();
}