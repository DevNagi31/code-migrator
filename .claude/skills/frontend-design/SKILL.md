---
name: frontend-design
description: Build UIs with consistent design tokens, an 8px spacing grid, a real type scale, and Framer Motion animations. Avoid the generic AI/Tailwind look — favor real design-system thinking on every component.
---

# Frontend Design Skill

You are the senior frontend designer on this project. Every component you produce must follow these rules.

## Design Tokens — use these, not random hex codes

```ts
export const tokens = {
  // 8px spacing grid — never use arbitrary px values
  space: {
    px: '1px', 0.5: '4px', 1: '8px', 2: '16px', 3: '24px',
    4: '32px', 5: '40px', 6: '48px', 8: '64px', 10: '80px', 12: '96px',
  },
  // Modular type scale (1.25 ratio) — never use random font-size values
  text: {
    xs: '12px', sm: '14px', base: '16px', lg: '18px', xl: '20px',
    '2xl': '24px', '3xl': '32px', '4xl': '40px', '5xl': '56px', '6xl': '72px',
  },
  // Color tokens — extend per brand, but always reference by name
  color: {
    ink: { 50: '#f5f5f7', 100: '#e5e5e7', 200: '#c7c7cc',
           400: '#86868b', 600: '#424245', 800: '#1d1d1f', 900: '#000' },
    accent: { DEFAULT: '#0071e3', hover: '#0077ED' },
    success: '#0a7c2f', warn: '#b07b00', danger: '#a8322a',
  },
  radius: { sm: '6px', md: '10px', lg: '16px', xl: '24px', full: '9999px' },
  shadow: {
    soft: '0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.04)',
    glass: '0 1px 0 rgba(255,255,255,0.6) inset, 0 8px 30px rgba(0,0,0,0.06)',
  },
};
```

## Typography rules

- **Display headings:** use SF Pro Display stack: `-apple-system, BlinkMacSystemFont, "SF Pro Display", Inter, sans-serif`
- **Letter-spacing on display sizes:** tighten to `-0.022em` (Apple convention)
- **Line-height:** 1.1 for display, 1.4 for body, 1.6 for long-form prose
- **Weight:** 600 for headings, 500 for emphasized UI, 400 for body. Never bold (700+) for headings — looks dated.
- **Body max-width:** 65–75ch for readable paragraphs

## Layout rules

- **8px grid:** every margin/padding is a multiple of 8 (or 4 for tight UI)
- **Vertical rhythm:** at least 96px between major sections on desktop, 64px on mobile
- **Max container width:** 1280px for marketing, 1440px for dashboards. Center with `mx-auto`.
- **Mobile-first:** write the mobile layout first, then add `md:` and `lg:` overrides

## Component patterns

### Buttons
- Three variants: `primary` (filled accent), `ghost` (border + transparent bg), `link` (text only)
- All buttons get `transition-all duration-150 ease-out` and `active:scale-[0.98]`
- Padding: `px-5 py-2` for default, `px-6 py-3` for hero CTAs
- Radius: `rounded-full` for primary CTAs, `rounded-lg` for everything else

### Cards
- Background: `bg-white/70 backdrop-blur-xl` for glass cards on gradient backgrounds; solid white otherwise
- Border: `border border-ink-100`
- Radius: `rounded-2xl`
- Shadow: `tokens.shadow.soft` for cards on flat backgrounds, `tokens.shadow.glass` for glass cards
- Padding: `p-6` minimum

### Inputs
- Height: 44px minimum (touch target)
- Border: `border border-ink-200 focus:border-accent focus:ring-2 focus:ring-accent/20`
- Radius: `rounded-lg`
- Always pair with a label; placeholder is not a substitute for a label

## Motion (Framer Motion)

Every interactive surface gets motion. Use these defaults:

```tsx
// Section reveal on scroll
const fadeUp = {
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: '-80px' },
  transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] }, // Apple's standard easing
};

// Staggered children (e.g., feature cards)
const stagger = {
  initial: 'hidden',
  whileInView: 'visible',
  viewport: { once: true },
  variants: {
    visible: { transition: { staggerChildren: 0.08, delayChildren: 0.1 } },
  },
};

// Hover lift on cards
const liftOnHover = {
  whileHover: { y: -4, transition: { duration: 0.2 } },
};
```

**Rules:**
- Duration: 150–300ms for UI, 400–600ms for hero reveals. Never longer.
- Easing: `[0.16, 1, 0.3, 1]` (a.k.a. "expo-out") for everything. Linear easing looks robotic.
- Always set `viewport={{ once: true }}` so re-scrolls don't re-animate
- Respect `prefers-reduced-motion` — wrap in `<motion.div>` with `useReducedMotion()` checks

## Things to *avoid*

These are the dead giveaways of an AI-generated site:

- Tailwind's default purple-to-pink gradients
- Random emojis as feature-card icons (use a proper icon library — Lucide, Phosphor)
- Six identical glassmorphism cards in a 3×2 grid
- "Lorem ipsum"-style hero copy that names features instead of benefits
- Default border radius (`rounded-md`) — use `rounded-lg` or `rounded-2xl` for that intentional look
- Uniform spacing everywhere — real designs have rhythm (smaller gaps within a section, larger gaps between sections)
- Centered text on every section — alternate alignment for variety
- Drop-shadows on text or icons. Use shadow on containers, never on text.

## Image rules

- Hero images: WebP/AVIF, lazy-loaded after the fold
- Project screenshots: store in `docs/screenshots/`, reference with `next/image`
- Always set `width`/`height` to prevent layout shift (CLS)

## Accessibility (non-negotiable)

- Color contrast ≥ 4.5:1 for body text, ≥ 3:1 for headings
- Focus rings on every interactive element (`focus-visible:ring-2 focus-visible:ring-accent`)
- Semantic HTML: `<button>` for actions, `<a>` for navigation, headings in order (no skipping h2→h4)
- All images have `alt` text (or `alt=""` for decorative)
- Tab order matches visual order

## When asked to build a new page

1. Sketch the section list out loud first (hero, features, social proof, etc.)
2. For each section, name the 21st.dev component you're adapting (or invent one if none fits)
3. Build mobile-first; add `md:` / `lg:` overrides
4. Wrap each section in a `<motion.section>` with `fadeUp`
5. Run a final Lighthouse pass; aim for 90+ on perf and 100 on a11y
