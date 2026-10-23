import type { ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { Skeleton } from "./components/ui";
import { AskProvider, RefreshProvider, SessionProvider, useSession } from "./lib/context";
import { Connect } from "./pages/Connect";
import { Landing } from "./pages/Landing";
import { Login } from "./pages/Login";
import { Overview } from "./pages/Overview";
import { Security } from "./pages/Security";
import { Transactions } from "./pages/Transactions";

function RequireAuth({ children }: { children: ReactNode }) {
  const { session } = useSession();
  if (!session) {
    return (
      <div className="mx-auto max-w-[1180px] space-y-4 p-10">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32" />
      </div>
    );
  }
  return session.authenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

export function App() {
  return (
    <BrowserRouter>
      <SessionProvider>
        <RefreshProvider>
          <AskProvider>
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={<Login />} />
              <Route
                path="/app"
                element={
                  <RequireAuth>
                    <AppShell />
                  </RequireAuth>
                }
              >
                <Route index element={<Overview />} />
                <Route path="transactions" element={<Transactions />} />
                <Route path="connect" element={<Connect />} />
                <Route path="security" element={<Security />} />
              </Route>
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </AskProvider>
        </RefreshProvider>
      </SessionProvider>
    </BrowserRouter>
  );
}
