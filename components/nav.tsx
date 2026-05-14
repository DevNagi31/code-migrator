import Link from 'next/link';
import { GitMerge } from 'lucide-react';

export function Nav() {
  return (
    <header className="sticky top-0 z-40 nav-blur">
      <div className="mx-auto flex h-12 max-w-6xl items-center justify-between px-6 text-[13px]">
        <Link href="/" className="flex items-center gap-2 font-medium tracking-tight text-ink-800">
          <span className="inline-flex h-6 w-6 items-center justify-center rounded-md bg-gradient-to-br from-accent to-violet-500">
            <GitMerge className="h-3.5 w-3.5 text-white" />
          </span>
          <span>CodeMigrator</span>
        </Link>
        <span className="hidden text-[12px] text-ink-400 md:inline">
          Fine-tuned LLM for legacy code migration
        </span>
        <a
          href="https://github.com/DevNagi31/code-migrator"
          target="_blank"
          rel="noopener noreferrer"
          className="text-ink-600 transition hover:text-ink-800"
        >
          GitHub
        </a>
      </div>
    </header>
  );
}
