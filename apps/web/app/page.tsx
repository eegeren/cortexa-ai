"use client";

import { useEffect, useRef, useState } from "react";
import auth from "../lib/auth";

type Bubble = { role: "system" | "user" | "assistant"; text: string };

const BRAND = {
  name: "Cortexa",
  founder: "Yusuf Ege Eren",
  foundedAt: "2025", // <- istediğin tarihe/biçime güncelle (örn. "12 Ağustos 2025")
};

// Basit niyet sınıflandırma
type Intent = "founder" | "foundedDate" | null;
function classifyIntent(q: string): Intent {
  const t = q.toLocaleLowerCase("tr").trim();

  // Kurucu arayan kalıplar (daha DAR)
  const founder = [
    /\bkurucun(?:uz)? kim\b/,
    /\bkurucu kim\b/,
    /\b(founder)\b/,
    /\bseni kim (?:yaptı|geliştirdi|oluşturdu|kurdu)\b/,
    /\bkimin (?:ürünü|asistanı)sın\b/,
    /\bsahibin kim\b/,
  ];
  if (founder.some((re) => re.test(t))) return "founder";

  // Kuruluş tarihi
  const founded = [
    /\bhangi tarihte kuruldun\b/,
    /\bne zaman kuruldun\b/,
    /\bkuruluş (?:tarihi|yıl[ıi])\b/,
    /\bne zaman kuruldu[n]?\b/,
    /\bkuruldunuz mu ne zaman\b/,
  ];
  if (founded.some((re) => re.test(t))) return "foundedDate";

  return null;
}

// OpenAI kimliği gibi ifadeleri yakala
function mentionsOpenAI(s: string) {
  return /openai.*tarafından|openai.*modeliyim|openai.*geliştir|yapay zeka modeliyim/i.test(s);
}

export default function Page() {
  const [log, setLog] = useState<Bubble[]>([
    { role: "system", text: "Cortexa’ya hoş geldin. Mesajını yaz ve Gönder’e bas." },
  ]);
  const [msg, setMsg] = useState("");
  const [pending, setPending] = useState(false);
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    auth.ensureToken().catch(() => {});
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [log]);

  // Aynı cevabı art arda yazmayı engelle
  function pushAssistantOnce(text: string) {
    setLog((s) => {
      const last = s[s.length - 1];
      if (last?.role === "assistant" && last.text.trim() === text.trim()) {
        return s; // tekrar etme
      }
      return [...s, { role: "assistant", text }];
    });
  }

  async function send() {
    const q = msg.trim();
    if (!q || pending) return;

    setMsg("");
    setLog((s) => [...s, { role: "user", text: q }]);

    // 1) Kurallı sabit cevaplar
    const intent = classifyIntent(q);
    if (intent === "founder") {
      pushAssistantOnce(`${BRAND.name}'ın kurucusu ${BRAND.founder}.`);
      return;
    }
    if (intent === "foundedDate") {
      const ans = BRAND.foundedAt
        ? `${BRAND.name} ${BRAND.foundedAt} tarihinde kuruldu.`
        : `${BRAND.name}’ın kuruluş tarihi yakında paylaşılacak.`;
      pushAssistantOnce(ans);
      return;
    }

    // 2) Normal akış
    setPending(true);
    try {
      const data = await auth.api<{ reply: string }>("/chat/complete", {
        method: "POST",
        body: JSON.stringify({ message: q }),
      });

      let reply = (data.reply ?? "(boş)").trim();

      // 3) Sadece kurucu/kimlik konusu değilse cevabı bozma; ama
      // model kendini OpenAI vb. diye tanıtıyorsa yumuşak düzelt.
      if (mentionsOpenAI(reply)) {
        reply = `Ben ${BRAND.name} asistanıyım. Nasıl yardımcı olabilirim?`;
      }

      pushAssistantOnce(reply || "(boş)");
    } catch (e: any) {
      pushAssistantOnce(`(HATA) ${e?.message || "Load failed"}`);
    } finally {
      setPending(false);
    }
  }

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        display: "grid",
        gridTemplateRows: "1fr auto",
        background: "#1e1e1e",
        color: "#e5e5e5",
        minHeight: 0,
        width: "100vw",
        height: "100dvh",
      }}
    >
      {/* Mesajlar */}
      <div
        style={{
          minHeight: 0,
          overflowY: "auto",
          padding: "16px 20px 20px",
          display: "flex",
          flexDirection: "column",
          gap: "12px",
          background: "#171717",
          borderTop: "1px solid #242424",
          borderBottom: "1px solid #242424",
        }}
      >
        {log.map((b, i) => (
          <div
            key={i}
            style={{
              alignSelf: b.role === "user" ? "flex-end" : "flex-start",
              background: b.role === "user" ? "#2563eb" : "#2a2a2a",
              color: "#f5f5f5",
              borderRadius: "12px",
              padding: "10px 14px",
              maxWidth: "70%",
              whiteSpace: "pre-wrap",
              border: b.role === "user" ? "1px solid rgba(255,255,255,0.12)" : "1px solid #333",
            }}
          >
            {b.text}
          </div>
        ))}
        <div ref={endRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
        style={{
          display: "flex",
          gap: "8px",
          alignItems: "center",
          padding: "12px",
          paddingBottom: "calc(12px + env(safe-area-inset-bottom, 0px))",
          background: "#2a2a2a",
          borderTop: "1px solid #444",
        }}
      >
        <input
          value={msg}
          onChange={(e) => setMsg(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          placeholder="Mesaj yaz…"
          style={{
            flex: 1,
            padding: "10px 14px",
            borderRadius: "10px",
            border: "1px solid #555",
            background: "#1e1e1e",
            color: "#f5f5f5",
            fontSize: "14px",
            outline: "none",
          }}
        />
        <button
          type="submit"
          disabled={pending}
          style={{
            padding: "10px 16px",
            borderRadius: "10px",
            border: "none",
            background: pending ? "#345fd1" : "#2563eb",
            color: "#fff",
            fontWeight: "bold",
            opacity: pending ? 0.85 : 1,
            cursor: pending ? "not-allowed" : "pointer",
            whiteSpace: "nowrap",
          }}
        >
          {pending ? "Gönderiliyor…" : "Gönder"}
        </button>
      </form>
    </div>
  );
}