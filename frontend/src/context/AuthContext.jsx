import { createContext, useContext, useState, useEffect } from "react";
import { login as loginApi } from "../api/endpoints";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    const email = localStorage.getItem("email");
    const role = localStorage.getItem("role");
    if (token && email) {
      setUser({ email, role });
    }
  }, []);

  const login = async (email, password) => {
    const data = await loginApi(email, password);
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("email", email);
    // We don't know role from token alone; fetch later or accept default
    const role = email.includes("admin") ? "admin" : "doctor";
    localStorage.setItem("role", role);
    setUser({ email, role });
    return data;
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("email");
    localStorage.removeItem("role");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);