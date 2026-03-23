import { useState, useEffect } from "react";
import type { StudentResults, HackathonConfig } from "./types";

export function useStudentResults() {
  const [data, setData] = useState<StudentResults | null>(null);
  const [lastFetch, setLastFetch] = useState<Date | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(`/student-results.json?t=${Date.now()}`);
        if (res.status === 404) { setNotFound(true); return; }
        if (!res.ok) return;
        const json: StudentResults = await res.json();
        setData(json);
        setLastFetch(new Date());
        setNotFound(false);
      } catch {
        // réseau indisponible, on réessaie dans 3s
      }
    };
    load();
    const id = setInterval(load, 3000);
    return () => clearInterval(id);
  }, []);

  return { data, lastFetch, notFound };
}

export function useHackathonConfig() {
  const [config, setConfig] = useState<HackathonConfig | null>(null);

  useEffect(() => {
    fetch("/hackathon-config.json")
      .then((r) => r.json())
      .then(setConfig)
      .catch(() => {});
  }, []);

  return config;
}
