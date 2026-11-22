import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api/index";
import type { PublicEvent } from "@/lib/api/types/events";
import { isRealCinemaEvent, partitionGarnectProgram } from "@/lib/eventUtils";

type GarnectCache = {
  program: PublicEvent[];
  rest: PublicEvent[];
  error: string | null;
  promise: Promise<{ program: PublicEvent[]; rest: PublicEvent[] }> | null;
};

const cache: GarnectCache = { program: [], rest: [], error: null, promise: null };

async function fetchGarnectProgram(): Promise<{ program: PublicEvent[]; rest: PublicEvent[] }> {
  if (cache.promise) {
    return cache.promise;
  }

  cache.promise = api
    .getPublicEvents({ region: "pushkin_gory", limit: "80" })
    .then((response) => {
      const pushkin = response.items.filter((event) => !isRealCinemaEvent(event));
      const split = partitionGarnectProgram(pushkin);
      cache.program = split.program;
      cache.rest = split.rest;
      cache.error = null;
      return split;
    })
    .catch(() => {
      cache.error = "Афиша недоступна";
      return { program: cache.program, rest: cache.rest };
    })
    .finally(() => {
      cache.promise = null;
    });

  return cache.promise;
}

export function usePushkinGarnectProgram(enabled = true) {
  const [program, setProgram] = useState<PublicEvent[]>(enabled ? cache.program : []);
  const [rest, setRest] = useState<PublicEvent[]>(enabled ? cache.rest : []);
  const [loading, setLoading] = useState(enabled && !cache.program.length && !cache.rest.length);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!enabled) {
      setProgram([]);
      setRest([]);
      setLoading(false);
      return;
    }
    setLoading(!cache.program.length && !cache.rest.length);
    const split = await fetchGarnectProgram();
    setProgram(split.program);
    setRest(split.rest);
    setError(cache.error);
    setLoading(false);
  }, [enabled]);

  useEffect(() => {
    void load();
  }, [load]);

  return { program, rest, loading, error, refresh: load };
}
