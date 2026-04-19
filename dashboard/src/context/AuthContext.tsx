import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";
import api from "../api/client";
import type { User } from "../api/types";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    fullName: string
  ) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("rally_token");
    if (token) {
      api
        .get("/auth/me")
        .then((res) => setUser(res.data))
        .catch(() => localStorage.removeItem("rally_token"))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const res = await api.post("/auth/login", { email, password });
    localStorage.setItem("rally_token", res.data.access_token);
    const me = await api.get("/auth/me");
    setUser(me.data);
  };

  const register = async (
    email: string,
    password: string,
    fullName: string
  ) => {
    await api.post("/auth/register", {
      email,
      password,
      full_name: fullName,
    });
    await login(email, password);
  };

  const logout = () => {
    localStorage.removeItem("rally_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be inside AuthProvider");
  return ctx;
}
