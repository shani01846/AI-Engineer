import { app } from 'electron';
import { promises as fs } from 'node:fs';
import path from 'node:path';

// API key is kept in-memory for the current app session only.
// This forces a fresh key prompt on every app restart.

function keyFilePath(): string {
  return path.join(app.getPath('userData'), 'google-ai-studio.key.enc');
}

export type ApiKeySource = 'session' | 'none';
let sessionApiKey: string | null = null;

export async function setApiKey(key: string): Promise<void> {
  const trimmed = key.trim();
  if (!trimmed) throw new Error('API key cannot be empty.');
  sessionApiKey = trimmed;
}

export async function getApiKeyWithSource(): Promise<{ key: string | null; source: ApiKeySource }> {
  if (sessionApiKey) return { key: sessionApiKey, source: 'session' };

  return { key: null, source: 'none' };
}

export async function getApiKey(): Promise<string | null> {
  const { key } = await getApiKeyWithSource();
  return key;
}

export async function hasApiKey(): Promise<boolean> {
  return (await getApiKey()) !== null;
}

export async function clearStoredApiKey(): Promise<void> {
  sessionApiKey = null;
  try {
    // Cleanup legacy persisted key file from previous versions.
    await fs.unlink(keyFilePath());
  } catch (err) {
    const code = (err as NodeJS.ErrnoException).code;
    if (code !== 'ENOENT') throw err;
  }
}
