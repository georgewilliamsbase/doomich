import { DependencyList, useCallback, useEffect, useState } from 'react';

import { errorText } from './api';

type LoadState<T> = { data?: T; error?: string; loading: boolean };

/** Загрузка данных при монтировании и при смене зависимостей, плюс ручная перезагрузка. */
export function useLoad<T>(fn: () => Promise<T>, deps: DependencyList) {
  const [state, setState] = useState<LoadState<T>>({ loading: true });
  const [tick, setTick] = useState(0);
  useEffect(() => {
    let alive = true;
    fn().then(
      (data) => alive && setState({ data, loading: false }),
      (e) => alive && setState({ error: errorText(e), loading: false }),
    );
    return () => {
      alive = false;
    };
    // fn пересоздаётся на каждый рендер, следим только за явными зависимостями
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);
  const reload = useCallback(() => {
    setState((s) => ({ ...s, loading: true }));
    setTick((t) => t + 1);
  }, []);
  return { ...state, reload };
}
