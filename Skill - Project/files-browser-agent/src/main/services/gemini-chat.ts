import path from 'node:path';
import { homedir } from 'node:os';
import { GoogleGenAI } from '@google/genai';
import type { BrowserWindow } from 'electron';
import type { ChatMessage, ChatStreamEvent, SelectionContext } from '@shared/types';
import { clearStoredApiKey, getApiKeyWithSource } from '../secrets';
import { getSelection } from './selection-state';
import { describeSelection } from './selection-context';
import { makeTools, type LocalTool } from './agent-tools';

// Default Gemini model for tool calling + streaming.
const MODEL = 'gemini-2.5-flash';
const MAX_TOKENS = 4096;
const MAX_ITERATIONS = 20; // safety bound on the tool loop (skills run several commands)

const controllers = new Map<string, AbortController>();

type Emit = (e: ChatStreamEvent) => void;

function mapGeminiError(err: unknown): string {
  const raw = err instanceof Error ? err.message : String(err);
  const lower = raw.toLowerCase();

  if (lower.includes('reported as leaked') || lower.includes('api key was reported as leaked')) {
    return (
      'Google rejected this API key because it was flagged as leaked. ' +
      'Create a new key in Google AI Studio, update GOOGLE_API_KEY (or save it in-app), and try again.'
    );
  }

  if (lower.includes('permission_denied') || lower.includes('forbidden') || lower.includes('403')) {
    return (
      'Gemini request was denied (403). Verify the API key is valid, active, and from Google AI Studio.'
    );
  }

  return raw;
}

type GeminiContent = {
  role: 'user' | 'model';
  parts: Array<Record<string, unknown>>;
};

function toGeminiMessages(messages: ChatMessage[]): GeminiContent[] {
  return messages.map((m) => ({
    role: m.role === 'assistant' ? 'model' : 'user',
    parts: [{ text: m.content }]
  }));
}

function toFunctionDeclarations(tools: LocalTool[]): Array<Record<string, unknown>> {
  return tools.map((tool) => ({
    name: tool.name,
    description: tool.description,
    parameters: tool.inputSchema
  }));
}

/**
 * The folder where run_command runs by default: the selected folder, or the
 * folder containing the selected file. Falls back to the user's home directory.
 */
function workDirFor(sel: SelectionContext): string {
  if (!sel.path) return homedir();
  return sel.kind === 'directory' ? sel.path : path.dirname(sel.path);
}

function buildSystemPrompt(metadata: string): string {
  return (
    'You are an assistant embedded in a Windows file browser.\n\n' +
    "You are given METADATA about the user's current selection (below) plus tools. " +
    'Choose the cheapest path that answers the question:\n' +
    '- Answer directly from the metadata when you can (names, sizes, types, modified times, folder contents).\n' +
    '- Use get_file_info / list_dir / read_text_file for more detail on folders and text files.\n' +
    "- Call load_file ONLY when you must see a file's actual content. " +
    'It is token-expensive - avoid it when metadata or a cheaper tool suffices.\n\n' +
    'Paths are absolute Windows paths. Be concise.\n\n' +
    '== Current selection metadata ==\n' +
    metadata
  );
}

/** Runs the agent: metadata-first context + load-on-demand tools, streamed to the UI. */
export async function runChat(
  win: BrowserWindow,
  conversationId: string,
  messages: ChatMessage[]
): Promise<void> {
  const emit: Emit = (e) => win.webContents.send('chat:event', e);

  const { key: apiKey, source } = await getApiKeyWithSource();
  if (!apiKey) {
    emit({ type: 'error', message: 'No API key set.' });
    return;
  }

  const client = new GoogleGenAI({ apiKey });
  const controller = new AbortController();
  controllers.set(conversationId, controller);

  try {
    const selection = getSelection();
    const workDir = workDirFor(selection);
    const metadata = await describeSelection(selection);
    const systemPrompt = buildSystemPrompt(metadata);
    const tools = makeTools(emit, workDir);
    const declarations = toFunctionDeclarations(tools);
    const toolMap = new Map(tools.map((t) => [t.name, t]));

    const contents = toGeminiMessages(messages);

    for (let turn = 0; turn < MAX_ITERATIONS; turn++) {
      if (controller.signal.aborted) {
        emit({ type: 'done', stopReason: 'aborted' });
        return;
      }

      const responseStream = await client.models.generateContentStream({
        model: MODEL,
        contents,
        config: {
          maxOutputTokens: MAX_TOKENS,
          systemInstruction: systemPrompt,
          tools: [{ functionDeclarations: declarations }]
        }
      });

      let assistantText = '';
      let finalResponse: Record<string, unknown> | null = null;

      for await (const chunk of responseStream) {
        if (controller.signal.aborted) {
          emit({ type: 'done', stopReason: 'aborted' });
          return;
        }

        const delta = typeof chunk.text === 'string' ? chunk.text : '';
        if (delta) {
          assistantText += delta;
          emit({ type: 'text', delta });
        }

        finalResponse =
          (chunk.candidates?.[0]?.content as Record<string, unknown> | undefined) ?? finalResponse;
      }

      const parts =
        (finalResponse?.parts as Array<Record<string, unknown>> | undefined) ??
        (assistantText ? [{ text: assistantText }] : []);

      if (parts.length > 0) {
        contents.push({ role: 'model', parts });
      }

      const functionCalls = parts
        .map((part) =>
          part.functionCall as { name?: string; args?: Record<string, unknown> } | undefined
        )
        .filter(
          (fc): fc is { name: string; args?: Record<string, unknown> } =>
            Boolean(fc && typeof fc.name === 'string')
        );

      if (functionCalls.length === 0) {
        emit({ type: 'done', stopReason: 'end_turn' });
        return;
      }

      const toolResponseParts: Array<Record<string, unknown>> = [];

      for (const call of functionCalls) {
        const tool = toolMap.get(call.name);
        const args = call.args ?? {};

        if (!tool) {
          toolResponseParts.push({
            functionResponse: {
              name: call.name,
              response: { result: `Error: Unknown tool '${call.name}'.` }
            }
          });
          continue;
        }

        const result = await tool.run(args);
        toolResponseParts.push({
          functionResponse: {
            name: call.name,
            response: { result: typeof result === 'string' ? result : JSON.stringify(result) }
          }
        });
      }

      contents.push({ role: 'user', parts: toolResponseParts });
    }

    emit({ type: 'done', stopReason: 'max_iterations' });
  } catch (err) {
    if (controller.signal.aborted) {
      emit({ type: 'done', stopReason: 'aborted' });
    } else {
      const raw = err instanceof Error ? err.message : String(err);
      const leaked = raw.toLowerCase().includes('reported as leaked');
      if (leaked && source === 'session') {
        await clearStoredApiKey();
      }
      const message = mapGeminiError(err);
      emit({ type: 'error', message });
    }
  } finally {
    controllers.delete(conversationId);
  }
}

export function abortChat(conversationId: string): void {
  controllers.get(conversationId)?.abort();
}