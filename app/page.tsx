'use client';
import { useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Loader2, Copy, Check } from 'lucide-react';

const MIGRATIONS = [
  { id: 'jquery_to_fetch', label: 'jQuery → fetch + async/await', language: 'javascript' },
  { id: 'python2_to_python3', label: 'Python 2 → Python 3', language: 'python' },
  { id: 'callbacks_to_async_await', label: 'Callbacks → async/await', language: 'javascript' },
  { id: 'class_to_hooks', label: 'React Class → Hooks', language: 'javascript' },
  { id: 'var_to_const_let', label: 'var → const/let', language: 'javascript' },
  { id: 'commonjs_to_esm', label: 'CommonJS → ES Modules', language: 'javascript' },
] as const;

const SAMPLES: Record<string, string> = {
  jquery_to_fetch: `$.ajax({
  url: '/api/users',
  method: 'GET',
  success: function(data) {
    console.log(data);
  },
  error: function(err) {
    console.error('failed', err);
  }
});`,
  python2_to_python3: `def greet(name):
    print 'hello,', name

for i in xrange(3):
    greet('world')`,
  callbacks_to_async_await: `function loadUser(id, callback) {
  db.query('SELECT * FROM users WHERE id = ?', [id], function(err, rows) {
    if (err) return callback(err);
    callback(null, rows[0]);
  });
}`,
  class_to_hooks: `class Counter extends React.Component {
  constructor(props) {
    super(props);
    this.state = { count: 0 };
  }
  increment = () => {
    this.setState({ count: this.state.count + 1 });
  };
  render() {
    return <button onClick={this.increment}>{this.state.count}</button>;
  }
}`,
  var_to_const_let: `function totalize(items) {
  var sum = 0;
  for (var i = 0; i < items.length; i++) {
    var item = items[i];
    sum += item.price * item.qty;
  }
  return sum;
}`,
  commonjs_to_esm: `const express = require('express');
const { Router } = require('express');
const router = Router();

function setup(app) {
  app.use('/api', router);
}

module.exports = { setup };`,
};

const easing = [0.16, 1, 0.3, 1] as const;

export default function Home() {
  const [migration, setMigration] = useState<(typeof MIGRATIONS)[number]>(MIGRATIONS[0]);
  const [legacy, setLegacy] = useState(SAMPLES[MIGRATIONS[0].id]);
  const [output, setOutput] = useState('');
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function migrate() {
    setError(null);
    setOutput('');
    setRunning(true);
    try {
      const res = await fetch('/api/migrate', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ legacy, migration_type: migration.id }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
      } else {
        setOutput(body.migrated);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setRunning(false);
    }
  }

  function pickMigration(m: (typeof MIGRATIONS)[number]) {
    setMigration(m);
    setLegacy(SAMPLES[m.id]);
    setOutput('');
    setError(null);
  }

  async function copyOutput() {
    if (!output) return;
    await navigator.clipboard.writeText(output);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <main className="mx-auto max-w-6xl px-6 py-12">
      <motion.section
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: easing }}
        className="text-center"
      >
        <h1 className="text-[44px] font-semibold leading-none tracking-tightest text-ink-800 md:text-[56px]">
          Modernize code,{' '}
          <span className="bg-gradient-to-br from-accent to-violet-500 bg-clip-text text-transparent">
            line by line.
          </span>
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-[15px] text-ink-600">
          A QLoRA fine-tuning project for Qwen 2.5 Coder 7B on six classic migration tasks. The
          training pipeline + eval harness (BLEU, parse rate, AST similarity) are shipped; this
          live demo uses Claude with a few-shot prompt until you train your own checkpoint on
          Kaggle.
        </p>
      </motion.section>

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: easing, delay: 0.1 }}
        className="mt-10 flex flex-wrap gap-2"
      >
        {MIGRATIONS.map((m) => {
          const active = m.id === migration.id;
          return (
            <button
              key={m.id}
              onClick={() => pickMigration(m)}
              className={`rounded-full px-3 py-1.5 text-[12px] transition ${
                active
                  ? 'bg-accent text-white'
                  : 'bg-ink-100 text-ink-600 hover:bg-ink-200'
              }`}
            >
              {m.label}
            </button>
          );
        })}
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, ease: easing, delay: 0.2 }}
        className="mt-6 grid gap-4 lg:grid-cols-2"
      >
        <div className="card overflow-hidden">
          <div className="flex items-center justify-between border-b border-ink-100 px-4 py-2 text-[11px] uppercase tracking-[0.08em] text-ink-400">
            <span>Legacy input</span>
            <span className="font-mono">{migration.language}</span>
          </div>
          <textarea
            value={legacy}
            onChange={(e) => setLegacy(e.target.value)}
            className="h-72 w-full resize-none bg-white p-4 font-mono text-[13px] text-ink-800 focus:outline-none"
            spellCheck={false}
            disabled={running}
          />
        </div>

        <div className="card overflow-hidden">
          <div className="flex items-center justify-between border-b border-ink-100 px-4 py-2 text-[11px] uppercase tracking-[0.08em] text-ink-400">
            <span>Migrated output</span>
            {output && (
              <button
                type="button"
                onClick={copyOutput}
                className="inline-flex items-center gap-1 text-ink-600 transition hover:text-ink-800"
              >
                {copied ? (
                  <>
                    <Check className="h-3 w-3 text-success" /> copied
                  </>
                ) : (
                  <>
                    <Copy className="h-3 w-3" /> copy
                  </>
                )}
              </button>
            )}
          </div>
          <pre className="h-72 overflow-auto bg-ink-50 p-4 font-mono text-[13px] text-ink-800">
            {output || (running ? 'Generating…' : ' ')}
          </pre>
        </div>
      </motion.div>

      <div className="mt-6 flex items-center justify-between">
        <button onClick={migrate} disabled={running || !legacy.trim()} className="btn-primary">
          {running ? (
            <>
              <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" /> Migrating
            </>
          ) : (
            <>
              <Sparkles className="mr-1 h-3.5 w-3.5" /> Migrate
            </>
          )}
        </button>
        <span className="text-[11px] text-ink-400">
          Demo backend: Claude few-shot. Swap for your fine-tuned adapter in <code className="font-mono">app/api/migrate</code>.
        </span>
      </div>

      {error && (
        <div className="mt-4 rounded-2xl border-l-4 border-danger bg-danger/5 p-4 text-[13px] text-danger">
          {error}
        </div>
      )}

      <section className="mt-16 grid gap-4 md:grid-cols-3">
        {[
          {
            title: 'Curated dataset',
            body: 'GitHub scraper + quality filter (permissive licenses, parse-checked, signal-matched). 10K+ real PR pairs targeted; sample set of 10 shipped for tests.',
          },
          {
            title: 'QLoRA on free GPUs',
            body: 'Qwen 2.5 Coder 7B fine-tuned via Unsloth with 4-bit quantization and LoRA r=16. Fits in 16 GB; runs on Kaggle\'s free T4.',
          },
          {
            title: 'Three-axis eval',
            body: 'BLEU (surface), parse rate (syntactic well-formedness), and AST Jaccard similarity (structural). 19 unit tests verify the math on synthetic inputs.',
          },
        ].map((card) => (
          <div key={card.title} className="glass p-5">
            <h3 className="text-[16px] font-semibold tracking-tightest text-ink-800">{card.title}</h3>
            <p className="mt-2 text-[13px] text-ink-600">{card.body}</p>
          </div>
        ))}
      </section>

      <footer className="mt-16 border-t border-ink-100 pt-6 text-center text-[11px] text-ink-400">
        Built with Next.js 15 · Framer Motion · Unsloth QLoRA · Anthropic Claude (demo backend)
      </footer>
    </main>
  );
}
