import { afterEach, describe, expect, it, vi } from 'vitest';

import { api, ApiError, errorText, setUnauthorizedHandler, tokenStore } from './api';

function respond(status: number, body: unknown) {
  return vi.fn().mockResolvedValue(
    new Response(body === undefined ? null : JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } }),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
  tokenStore.clear();
});

describe('api', () => {
  it('подставляет токен и путь админ-API', async () => {
    const fetchMock = respond(200, { ok: 1 });
    vi.stubGlobal('fetch', fetchMock);
    tokenStore.set('t1');
    expect(await api.get('/me')).toEqual({ ok: 1 });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/admin/v1/me');
    expect(init.headers.Authorization).toBe('Bearer t1');
  });

  it('разбирает ошибку сервера', async () => {
    vi.stubGlobal('fetch', respond(422, { error: { code: 'validation', message: 'неверные данные', details: { fields: [{ field: 'count', msg: 'больше 5000' }] } } }));
    const err = (await api.post('/x', { count: 9000 }).catch((e: unknown) => e)) as ApiError;
    expect(err).toBeInstanceOf(ApiError);
    expect(err.code).toBe('validation');
    expect(errorText(err)).toBe('неверные данные: count больше 5000');
  });

  it('при 401 забывает токен и сообщает приложению', async () => {
    vi.stubGlobal('fetch', respond(401, { error: { code: 'unauthorized', message: 'нужен вход' } }));
    const handler = vi.fn();
    setUnauthorizedHandler(handler);
    tokenStore.set('old');
    await api.get('/me').catch(() => undefined);
    expect(tokenStore.get()).toBeNull();
    expect(handler).toHaveBeenCalledOnce();
  });

  it('отправляет FormData без JSON-заголовка', async () => {
    const fetchMock = respond(200, { applied: false });
    vi.stubGlobal('fetch', fetchMock);
    const fd = new FormData();
    fd.append('dry_run', 'true');
    await api.post('/tenants/1/schedule/import', fd);
    const [, init] = fetchMock.mock.calls[0];
    expect(init.body).toBe(fd);
    expect(init.headers['Content-Type']).toBeUndefined();
  });
});
