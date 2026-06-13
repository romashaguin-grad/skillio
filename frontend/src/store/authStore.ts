import { create } from "zustand";

interface AuthState {
  token: string | null;
  role: string | null;
  fullName: string | null;
  setAuth: (token: string, role: string, fullName: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  role: null,
  fullName: null,

  setAuth: (token, role, fullName) => {
    localStorage.setItem("token", token);
    localStorage.setItem("role", role);
    localStorage.setItem("fullName", fullName);
    set({ token, role, fullName });
  },

  logout: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("fullName");
    set({ token: null, role: null, fullName: null });
  },
}));