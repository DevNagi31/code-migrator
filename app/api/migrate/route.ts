/**
 * POST /api/migrate
 *
 * Body: { legacy: string, migration_type: MigrationType }
 * Calls Claude with a few-shot prompt as the demo predictor. Once a fine-tuned
 * checkpoint exists, swap this for a request to the vLLM-served adapter at
 * the same endpoint — the response shape is identical.
 */
import Anthropic from '@anthropic-ai/sdk';
import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';

const MIGRATION_LABELS: Record<string, string> = {
  jquery_to_fetch: 'jQuery AJAX call',
  python2_to_python3: 'Python 2 snippet',
  callbacks_to_async_await: 'callback-style JavaScript function',
  class_to_hooks: 'React class component',
  var_to_const_let: 'ES5 var-declaration block',
  commonjs_to_esm: 'CommonJS module',
};

const FEW_SHOT: Record<string, Array<[string, string]>> = {
  jquery_to_fetch: [
    [
      "$.ajax({ url: '/api/x', success: function(d){ cb(d); } });",
      "const r = await fetch('/api/x');\nconst d = await r.json();\ncb(d);",
    ],
  ],
  python2_to_python3: [
    ['print "hello"', 'print("hello")'],
    ['for i in xrange(n): pass', 'for i in range(n): pass'],
  ],
  callbacks_to_async_await: [
    [
      'fn(arg, function(err, res){ if (err) return cb(err); cb(null, res); });',
      'const res = await fn(arg);\ncb(null, res);',
    ],
  ],
  class_to_hooks: [],
  var_to_const_let: [['var x = 1; var y = 2;', 'const x = 1;\nconst y = 2;']],
  commonjs_to_esm: [
    ["const a = require('a');\nmodule.exports = b;", "import a from 'a';\nexport default b;"],
  ],
};

export async function POST(req: NextRequest) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return NextResponse.json(
      { error: 'ANTHROPIC_API_KEY is not set on the server' },
      { status: 503 },
    );
  }
  const { legacy, migration_type } = (await req.json()) as {
    legacy?: string;
    migration_type?: string;
  };
  if (!legacy || !migration_type) {
    return NextResponse.json({ error: 'missing legacy or migration_type' }, { status: 400 });
  }
  const label = MIGRATION_LABELS[migration_type];
  if (!label) {
    return NextResponse.json({ error: `unknown migration_type: ${migration_type}` }, { status: 400 });
  }
  const examples = FEW_SHOT[migration_type] ?? [];
  const examplesStr =
    examples.map(([l, m]) => `Input:\n${l}\n\nOutput:\n${m}`).join('\n\n') ||
    '(none for this migration type)';
  const prompt = `You are an expert code-modernization assistant. Given a ${label}, output only the migrated code — no commentary, no explanation, no Markdown fences.

Examples:

${examplesStr}

Now migrate this:

${legacy}`;
  const client = new Anthropic({ apiKey });
  const response = await client.messages.create({
    model: process.env.ANTHROPIC_MODEL ?? 'claude-sonnet-4-6',
    max_tokens: 1024,
    messages: [{ role: 'user', content: prompt }],
  });
  const text = response.content
    .filter((b): b is Extract<typeof b, { type: 'text' }> => b.type === 'text')
    .map((b) => b.text)
    .join('\n');
  return NextResponse.json({
    migrated: stripFences(text).trim(),
    backend: 'claude-fewshot',
    model: process.env.ANTHROPIC_MODEL ?? 'claude-sonnet-4-6',
  });
}

function stripFences(s: string): string {
  let t = s.trim();
  if (t.startsWith('```')) t = t.split('\n', 2)[1] ?? '';
  if (t.endsWith('```')) t = t.replace(/```$/, '');
  return t;
}
