import { Link, NavLink } from "react-router-dom";
import type { PropsWithChildren } from "react";

import { useAuth } from "../hooks/useAuth";

export function AppShell({ children }: PropsWithChildren) {
  const { isAuthenticated, isLoading, signInWithGoogle, logout, user } = useAuth();

  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/" className="brand-mark">
          <span className="brand-mark__icon">MW</span>
          <span>
            <strong>MindWise</strong>
            <small>AI Video Studio</small>
          </span>
        </Link>

        <nav className="app-nav">
          <NavLink to="/">Projects</NavLink>
          <NavLink to="/projects/new">New project</NavLink>
        </nav>

        <div className="app-actions">
          {isLoading ? (
            <span className="muted">Checking session...</span>
          ) : isAuthenticated ? (
            <>
              <div className="user-chip">
                <span className="user-chip__avatar">
                  {user?.full_name?.slice(0, 1) ?? user?.email.slice(0, 1)}
                </span>
                <div>
                  <strong>{user?.full_name ?? "MindWise User"}</strong>
                  <small>{user?.email}</small>
                </div>
              </div>
              <button className="button button--ghost" onClick={logout} type="button">
                Sign out
              </button>
            </>
          ) : (
            <button className="button" onClick={() => void signInWithGoogle()} type="button">
              Sign in with Google
            </button>
          )}
        </div>
      </header>

      <main className="app-main">{children}</main>
    </div>
  );
}
