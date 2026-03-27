import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { useAuth } from "../hooks/useAuth";

export function AuthCallbackPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const { completeGoogleCallback } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = params.get("code");
    const state = params.get("state");
    if (!code || !state) {
      setError("Google did not return the required callback parameters.");
      return;
    }

    const run = async () => {
      try {
        await completeGoogleCallback(code, state);
        navigate("/", { replace: true });
      } catch (callbackError) {
        setError((callbackError as Error).message);
      }
    };

    void run();
  }, [completeGoogleCallback, navigate, params]);

  return (
    <section className="panel panel--empty">
      <h1>Signing you in</h1>
      <p>{error ?? "Finishing the Google OAuth flow and creating your MindWise session."}</p>
    </section>
  );
}
