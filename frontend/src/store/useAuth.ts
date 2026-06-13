"use client";

import { useEffect } from "react";
import { useAuthStore } from "./authStore";

export function useAuthInit() {
  const setAuth = useAuthStore((s) => s.setAuth);

  useEffect(() => {
    const token = localStorage.getItem("token");
    const role = localStorage.getItem("role");
    const fullName = localStorage.getItem("fullName");
    if (token && role && fullName) {
      setAuth(token, role, fullName);
    }
  }, []);
}