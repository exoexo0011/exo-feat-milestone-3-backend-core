import { afterEach, describe, expect, it, vi } from 'vitest';

import { api, ApiError } from './client';

function fakeResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: '',
    json: async () => body,
  } as unknown as Response;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('api client', () => {
  it('sends the expected request and parses JSON', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        fakeResponse([{ id: '1', title: 't', archived: false, created_at: '', updated_at: '' }]),
      );
    vi.stubGlobal('fetch', fetchMock);

    const conversations = await api.listConversations();

    expect(conversations).toHaveLength(1);
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/chat/conversations?include_archived=false',
      expect.objectContaining({
        headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
      }),
    );
  });

  it('throws ApiError carrying the backend detail', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(fakeResponse({ detail: 'not found' }, 404)));

    await expect(api.listMessages('x')).rejects.toBeInstanceOf(ApiError);
    await expect(api.listMessages('x')).rejects.toMatchObject({
      status: 404,
      message: 'not found',
    });
  });

  it('wraps network failures as ApiError with status 0', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')));

    await expect(api.health()).rejects.toMatchObject({ status: 0 });
  });
});
