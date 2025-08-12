// web/components/Header.tsx
"use client";

import { useEffect, useState } from "react";
import auth from "../lib/auth";  // <-- default import

export default function Header() {
  const [hasToken, setHasToken] = useState(false);

  useEffect(() => {
    const update = () => setHasToken(!!auth.getToken());
    update();
    auth.ensureToken().finally(update);
    const onTok = () => update();
    window.addEventListener("cortexa:token", onTok);
    return () => window.removeEventListener("cortexa:token", onTok);
  }, []);

  return (
    <div style={{ display: "flex", gap: 16, alignItems: "center", justifyContent: "flex-end", padding: "12px 16px" }}>
      <span>Token: <b style={{ color: hasToken ? "#059669" : "#dc2626" }}>{hasToken ? "VAR" : "YOK"}</b></span>
      <button onClick={() => auth.ensureToken()} style={{ padding: "8px 10px", borderRadius: 8, border: "1px solid #e5e7eb", background: "#f8fafc" }}>
        Quick Register / Login
      </button>
      <button onClick={() => auth.setToken(null)} style={{ padding: "8px 10px", borderRadius: 8, border: "1px solid #e5e7eb", background: "#fff" }}>
        Logout
      </button>
    </div>
  );
}