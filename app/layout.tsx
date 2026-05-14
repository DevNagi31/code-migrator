import './globals.css';
import type { Metadata } from 'next';
import { Nav } from '@/components/nav';

export const metadata: Metadata = {
  title: 'CodeMigrator — Fine-Tuned LLM for Legacy Code Migration',
  description:
    'QLoRA fine-tuning of Qwen 2.5 Coder 7B on real GitHub migration PRs. BLEU + parse-rate + AST-similarity eval harness, demo UI backed by Claude until you train your own checkpoint.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="bg-ink-50">
      <body className="bg-ink-50 text-ink-800 antialiased font-sans">
        <Nav />
        {children}
      </body>
    </html>
  );
}
