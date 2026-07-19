import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function looksLikeImageUrl(value: string): boolean {
  const t = value.trim();
  if (!/^https?:\/\//i.test(t)) return false;
  // Accept common image extensions, optionally followed by query/hash.
  return /\.(png|jpe?g|gif|webp|bmp|svg)(?:[?#].*)?$/i.test(t);
}

function toDisplayContent(content: string): string {
  const t = content.trim();
  if (!looksLikeImageUrl(t)) return content;
  return `![Generated image](${t})`;
}

/**
 * Renders Gemini markdown replies.
 *
 * The wrapper is RTL so Hebrew text aligns to the right, while each block uses
 * `unicode-bidi: plaintext` (see .markdown in index.css) so the Unicode
 * bidirectional algorithm decides each paragraph/line's base direction from its
 * own content. That keeps embedded English words (and English-only lines or
 * code) flowing left-to-right without scrambling the surrounding Hebrew.
 */
export function Markdown({ content }: { content: string }) {
  const display = toDisplayContent(content);

  return (
    <div className="markdown" dir="rtl">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Open links in the user's browser instead of navigating the app.
          a: ({ node, ...props }) => (
            <a {...props} target="_blank" rel="noopener noreferrer" />
          ),
          img: ({ node, ...props }) => (
            <img {...props} loading="lazy" referrerPolicy="no-referrer" />
          )
        }}
      >
        {display}
      </ReactMarkdown>
    </div>
  );
}
