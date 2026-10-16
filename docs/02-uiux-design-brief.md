# HiveCode — UI/UX Design Brief

**Version:** 1.0
**Date:** 2026-10-16
**Source:** Derived from HiveCode PRD v1.0 and TRD v1.0
**Purpose:** Complete design specification for an AI app builder to follow without ambiguity.

---

## 1. Design Philosophy

### 1.1 Core Principle

**Trust through clarity.** Every status, outcome, and piece of evidence must be immediately legible. The user should never have to guess what happened or whether to trust a result.

### 1.2 Design Pillars

| Pillar | Meaning | Application |
|---|---|---|
| **Verification-first** | The product's promise is proof, not promises | Outcome badges are prominent, color-coded, and always sourced from API data — never derived or upgraded by the UI |
| **Evidence over assertion** | Show the work, not just the conclusion | Every claim links to check runs, logs, diffs, and traces |
| **Bounded autonomy** | The system is powerful but never unbounded | Approval flows, scope limits, and retry budgets are visible in the UI |
| **Calm urgency** | The user is informed but not anxious | Progress is shown clearly; failures are explained with next steps, not alarm |

---

## 2. Design Style

### 2.1 Overall Aesthetic

**Technical instrument panel.** HiveCode is a developer tool for high-stakes work. The aesthetic should feel like a precision instrument — dense with information, quiet in presentation, and unambiguous in meaning.

- **Matter-of-fact, not marketing-driven.** No hero sections, no gradients for decoration, no playful illustrations.
- **Information-dense but organized.** Developer tools are allowed to be dense; they must not be chaotic.
- **Dark-first, light-compatible.** The primary theme is dark (reduces eye strain during long debugging sessions). A light theme is provided for accessibility and preference.

### 2.2 Visual References

| Reference | What to borrow |
|---|---|
| **Linear** | Dense information layout, keyboard-first interaction, subtle borders, fast feel |
| **Vercel Dashboard** | Clean data tables, status badges, deployment-style timeline |
| **GitHub** | Diff rendering, PR status checks, repository card design |
| **Datadog/Grafana** | Timeline visualization, status colors, metric display |
| **Raycast** | Command palette patterns, modal design, keyboard shortcuts |

---

## 3. Color Palette

### 3.1 Dark Theme (Primary)

| Token | Hex | Usage |
|---|---|---|
| `--bg-primary` | `#0D0D0F` | App background |
| `--bg-secondary` | `#161618` | Card backgrounds, sidebar |
| `--bg-tertiary` | `#1E1E22` | Elevated surfaces, modals, hover states |
| `--bg-overlay` | `rgba(0,0,0,0.7)` | Modal backdrop |
| `--border-default` | `#2A2A2E` | Default borders, dividers |
| `--border-subtle` | `#1F1F23` | Subtle separators |
| `--border-focus` | `#3B82F6` | Focus rings, active states |
| `--text-primary` | `#E8E8EA` | Primary text |
| `--text-secondary` | `#9C9CA3` | Secondary text, labels, timestamps |
| `--text-tertiary` | `#6B6B73` | Tertiary text, disabled, placeholders |
| `--text-inverse` | `#0D0D0F` | Text on colored backgrounds |
| `--accent-primary` | `#3B82F6` | Primary actions, links, active nav |
| `--accent-hover` | `#2563EB` | Primary button hover |
| `--success` | `#22C55E` | Verified, passed |
| `--success-bg` | `#052E16` | Success badge background |
| `--error` | `#EF4444` | Failed, destructive |
| `--error-bg` | `#2A0A0A` | Error badge background |
| `--warning` | `#F59E0B` | Blocked, timed out |
| `--warning-bg` | `#2A1A00` | Warning badge background |
| `--info` | `#3B82F6` | Partially verified, info |
| `--info-bg` | `#0A1628` | Info badge background |
| `--neutral` | `#6B7280` | Skipped, unavailable, cancelled |
| `--neutral-bg` | `#1F2937` | Neutral badge background |
| `--code-bg` | `#1A1A1E` | Code blocks, diff viewer |
| `--diff-add-bg` | `#052E16` | Diff added lines |
| `--diff-add-text` | `#4ADE80` | Diff added text |
| `--diff-del-bg` | `#2A0A0A` | Diff removed lines |
| `--diff-del-text` | `#F87171` | Diff removed text |
| `--diff-hunk-bg` | `#0A1628` | Diff hunk headers |

### 3.2 Light Theme

| Token | Hex | Usage |
|---|---|---|
| `--bg-primary` | `#FFFFFF` | App background |
| `--bg-secondary` | `#F9FAFB` | Card backgrounds, sidebar |
| `--bg-tertiary` | `#F3F4F6` | Elevated surfaces, hover states |
| `--bg-overlay` | `rgba(0,0,0,0.3)` | Modal backdrop |
| `--border-default` | `#E5E7EB` | Default borders |
| `--border-subtle` | `#F3F4F6` | Subtle separators |
| `--border-focus` | `#3B82F6` | Focus rings |
| `--text-primary` | `#111827` | Primary text |
| `--text-secondary` | `#6B7280` | Secondary text |
| `--text-tertiary` | `#9CA3AF` | Tertiary text |
| `--accent-primary` | `#2563EB` | Primary actions |
| `--accent-hover` | `#1D4ED8` | Primary hover |
| `--success` | `#16A34A` | Verified, passed |
| `--success-bg` | `#F0FDF4` | Success badge background |
| `--error` | `#DC2626` | Failed |
| `--error-bg` | `#FEF2F2` | Error badge background |
| `--warning` | `#D97706` | Blocked |
| `--warning-bg` | `#FFFBEB` | Warning badge background |
| `--info` | `#2563EB` | Partially verified |
| `--info-bg` | `#EFF6FF` | Info badge background |
| `--neutral` | `#6B7280` | Skipped |
| `--neutral-bg` | `#F3F4F6` | Neutral badge background |
| `--code-bg` | `#F9FAFB` | Code blocks |
| `--diff-add-bg` | `#F0FDF4` | Diff added lines |
| `--diff-add-text` | `#16A34A` | Diff added text |
| `--diff-del-bg` | `#FEF2F2` | Diff removed lines |
| `--diff-del-text` | `#DC2626` | Diff removed text |
| `--diff-hunk-bg` | `#EFF6FF` | Diff hunk headers |

### 3.3 Semantic Color Rules

| Meaning | Dark | Light | Icon |
|---|---|---|---|
| Verified / Passed | `--success` | `--success` | Check circle (filled) |
| Failed | `--error` | `--error` | X circle (filled) |
| Blocked | `--warning` | `--warning` | Alert triangle (filled) |
| Partially verified | `--info` | `--info` | Half-filled circle |
| Skipped / Unavailable | `--neutral` | `--neutral` | Skip forward / Question mark |
| Running / In progress | `--text-tertiary` | `--text-tertiary` | Spinner (animated) |
| Cancelled | `--neutral` | `--neutral` | Ban circle |

**Critical rule:** Partially verified, Blocked, and Failed must never use green or success styling. The UI must never derive or upgrade an outcome — it renders exactly what the API returns.

---

## 4. Typography

### 4.1 Font Stack

| Use | Font | Fallback |
|---|---|---|
| UI text | Inter | system-ui, -apple-system, sans-serif |
| Code / diff / logs | JetBrains Mono | ui-monospace, "Cascadia Code", monospace |

### 4.2 Type Scale

| Element | Size | Weight | Line height | Letter spacing |
|---|---|---|---|---|
| H1 (page title) | 24px | 600 (semibold) | 32px | -0.02em |
| H2 (section title) | 18px | 600 | 28px | -0.01em |
| H3 (card title) | 16px | 600 | 24px | 0 |
| Body large | 16px | 400 | 24px | 0 |
| Body | 14px | 400 | 20px | 0 |
| Body small | 13px | 400 | 18px | 0 |
| Caption / label | 12px | 500 (medium) | 16px | 0.01em |
| Code | 13px | 400 | 20px | 0 |
| Badge | 12px | 600 | 16px | 0.02em |

### 4.3 Font Loading

- Inter: Load from Google Fonts CDN with `display=swap`
- JetBrains Mono: Load from Google Fonts CDN with `display=swap`
- Both weights 400, 500, 600 for Inter; 400 for JetBrains Mono

---

## 5. Layout Direction

### 5.1 Spacing System

Base unit: **4px**

| Token | Value | Usage |
|---|---|---|
| `--space-1` | 4px | Icon padding, inline gaps |
| `--space-2` | 8px | Tight element spacing |
| `--space-3` | 12px | Component internal padding |
| `--space-4` | 16px | Standard component padding |
| `--space-5` | 20px | Section spacing |
| `--space-6` | 24px | Card padding |
| `--space-8` | 32px | Section gaps |
| `--space-10` | 40px | Page section gaps |
| `--space-12` | 48px | Large section gaps |
| `--space-16` | 64px | Page top/bottom padding |

### 5.2 Border Radius

| Element | Radius |
|---|---|
| Buttons | 6px |
| Cards | 8px |
| Modals | 12px |
| Badges | 4px (pill for status badges: 999px) |
| Inputs | 6px |
| Code blocks | 6px |
| Avatars | 50% (circular) |

### 5.3 Shadows

| Element | Shadow |
|---|---|
| Cards | `0 1px 2px rgba(0,0,0,0.05)` (light) / none (dark, use border) |
| Modals | `0 20px 60px rgba(0,0,0,0.5)` |
| Dropdowns | `0 4px 12px rgba(0,0,0,0.15)` |
| Toast | `0 4px 12px rgba(0,0,0,0.15)` |

### 5.4 Z-Index Scale

| Layer | Z-index |
|---|---|
| Base content | 0 |
| Sticky header | 100 |
| Dropdown | 200 |
| Modal backdrop | 300 |
| Modal content | 310 |
| Toast | 400 |

---

## 6. Component Style

### 6.1 Buttons

| Variant | Style | Usage |
|---|---|---|
| **Primary** | `--accent-primary` bg, `--text-inverse` text, 6px radius, 14px/500 font. Hover: `--accent-hover`. Active: scale(0.98). | Main actions: Submit, Approve, Create PR |
| **Secondary** | `--bg-tertiary` bg, `--text-primary` text, `--border-default` border. Hover: `--border-focus`. | Secondary actions: Cancel, Retry |
| **Danger** | `--error` bg, `--text-inverse` text. Hover: darker red. | Destructive: Cancel task, Reject |
| **Ghost** | Transparent bg, `--text-secondary` text. Hover: `--bg-tertiary`. | Tertiary: Back, icon buttons |
| **Disabled** | `--bg-tertiary` bg, `--text-tertiary` text, cursor: not-allowed. | When form invalid or loading |

**Sizes:** Small (28px h), Medium (36px h), Large (44px h)

### 6.2 Inputs

| Element | Style |
|---|---|
| **Text input** | `--bg-secondary` bg, `--border-default` border, 6px radius, 14px/400 font, `--space-3` padding. Focus: `--border-focus` border + 2px focus ring. |
| **Textarea** | Same as text input, min-height 120px, resize: vertical. |
| **Select** | Same as text input with chevron icon. Dropdown: `--bg-tertiary` bg, `--border-default` border, 8px radius. |
| **Invalid** | `--error` border + error text below in `--error` color, 12px. |
| **Disabled** | `--bg-tertiary` bg, `--text-tertiary` text, cursor: not-allowed. |

### 6.3 Cards

| Element | Style |
|---|---|
| **Container** | `--bg-secondary` bg, `--border-default` border, 8px radius, `--space-6` padding. |
| **Hover** | `--border-focus` border (only when clickable). |
| **Header** | `--text-primary` 16px/600 font, `--space-4` bottom margin. |
| **Body** | `--text-secondary` 14px/400 font. |

### 6.4 Badges

| Type | Style |
|---|---|
| **Status badge** | Pill shape (999px radius), 12px/600 font, `--space-2` horizontal padding, colored bg at 15% opacity + colored text. |
| **Outcome badge** | Same as status badge but slightly larger (13px). |
| **Language badge** | 4px radius, 12px/500 font, `--bg-tertiary` bg, `--text-secondary` text. |

### 6.5 Tabs

| Element | Style |
|---|---|
| **Container** | `--border-subtle` bottom border, horizontal flex. |
| **Tab** | `--text-secondary` 14px/500 font, `--space-4` padding, transparent bg. Hover: `--text-primary`. |
| **Active tab** | `--text-primary` font, `--accent-primary` bottom border (2px). |
| **Content** | `--space-6` top padding. |

### 6.6 Tables

| Element | Style |
|---|---|
| **Header** | `--text-tertiary` 12px/600 font, uppercase, `--space-3` padding, `--border-subtle` bottom border. |
| **Row** | `--space-3` padding, `--border-subtle` bottom border. Hover: `--bg-tertiary` bg. |
| **Cell** | `--text-primary` 14px/400 font. |

### 6.7 Code Blocks & Diff Viewer

| Element | Style |
|---|---|
| **Container** | `--code-bg` bg, `--border-default` border, 6px radius, `--space-4` padding, overflow-x: auto. |
| **Font** | JetBrains Mono, 13px, `--text-primary`. |
| **Line numbers** | `--text-tertiary` color, right-aligned, `--space-4` right padding, user-select: none. |
| **Diff added** | `--diff-add-bg` bg, `--diff-add-text` text, `+` prefix. |
| **Diff removed** | `--diff-del-bg` bg, `--diff-del-text` text, `-` prefix. |
| **Diff hunk** | `--diff-hunk-bg` bg, `--text-tertiary` text, `@@` prefix. |

### 6.8 Modal

| Element | Style |
|---|---|
| **Backdrop** | `--bg-overlay` bg, flex center, padding `--space-6`. |
| **Container** | `--bg-secondary` bg, `--border-default` border, 12px radius, max-width 600px, max-height 80vh, overflow-y: auto. |
| **Header** | `--text-primary` 18px/600 font, `--space-6` padding, `--border-subtle` bottom border. |
| **Body** | `--space-6` padding, `--text-secondary` 14px/400 font. |
| **Footer** | `--space-6` padding, `--border-subtle` top border, right-aligned buttons. |
| **Close** | Top-right, ghost icon button (X). |

### 6.9 Timeline

| Element | Style |
|---|---|
| **Container** | Vertical list, `--space-2` gap. |
| **Item** | Flex row: icon (20px) + content. |
| **Connector** | 2px vertical line, `--border-default` color. Green for success, red for failure, gray for pending. |
| **Icon** | 20px circle with status color. Check for success, X for failure, spinner for running. |
| **Title** | `--text-primary` 14px/500 font. |
| **Timestamp** | `--text-tertiary` 12px font. |
| **Detail** | `--text-secondary` 13px font, expandable. |

### 6.10 Skeleton Loading

| Element | Style |
|---|---|
| **Block** | `--bg-tertiary` bg, 6px radius, pulse animation (opacity 0.4 → 0.8 → 0.4, 1.5s infinite). |
| **Text line** | Height 16px, width varies (100%, 80%, 60%). |
| **Card** | Full card shape with skeleton blocks inside. |

---

## 7. Dashboard Structure

### 7.1 Information Architecture

```
Task Detail (primary screen)
├── Overview: Objective, criteria, configuration, outcome
├── Timeline: Chronological event stream
├── Attempts: Patch history with diffs
├── Checks: Validation results with logs
├── Review: Independent reviewer findings
├── Report: Verification summary
└── Approvals: Pending/recent approvals
```

### 7.2 Visual Hierarchy

1. **Task title + outcome badge** — most prominent, always visible
2. **Action buttons** (Cancel, Create PR) — secondary prominence
3. **Tab navigation** — persistent, always accessible
4. **Tab content** — scrollable, dense but organized

### 7.3 Density Guidelines

| Element | Density |
|---|---|
| Task history cards | Compact — 3 lines per card |
| Timeline | Medium — 1-2 lines per event, expandable |
| Checks table | Compact — 1 line per check, expandable |
| Diff viewer | Full — all lines visible, scrollable |
| Report | Medium — sectioned, scannable |

---

## 8. Mobile Responsiveness

### 8.1 Breakpoints

| Breakpoint | Width | Target |
|---|---|---|
| Desktop | ≥1024px | Full layout |
| Tablet | 768–1023px | Adapted layout |
| Mobile | <768px | Stacked layout |

### 8.2 Layout Changes

| Component | Desktop | Tablet | Mobile |
|---|---|---|---|
| SideNav | Full (240px) | Icon-only (56px) | Hidden (hamburger) |
| TopBar | Full | Full | Condensed (logo + avatar only) |
| Task cards | 3-column grid | 2-column grid | 1-column stack |
| Task detail tabs | Horizontal | Horizontal | Horizontal scroll |
| Modals | Centered, max-width | Centered, 90% width | Full-screen sheet |
| New task form | 2-column (form + preview) | 1-column (preview below) | 1-column |
| Tables | Full | Full | Card-based (rows become cards) |

### 8.3 Touch Targets

- Minimum touch target: **44×44px** on mobile
- Button padding: minimum `--space-3` horizontal
- Gap between interactive elements: minimum `--space-2`

---

## 9. User Experience Principles

### 9.1 Core Principles

| # | Principle | Application |
|---|---|---|
| 1 | **Show, don't tell** | Every status has a visual indicator + text label. Never rely on color alone. |
| 2 | **Progressive disclosure** | Summary first, details on demand. Expandable sections, lazy-loaded logs. |
| 3 | **Forgiving actions** | Destructive actions (cancel, reject) require confirmation. |
| 4 | **Honest states** | Loading, empty, error, and partial states are all explicitly designed. No blank screens. |
| 5 | **Keyboard accessible** | All interactive elements reachable via keyboard. Focus visible. Tab order logical. |
| 6 | **Screen reader friendly** | Semantic HTML, ARIA labels on icon buttons, status announced via `aria-live`. |
| 7 | **No dead ends** | Every error state has a next action (retry, go back, contact support). |
| 8 | **Consistent language** | Same terms everywhere: "attempt" not "try", "outcome" not "result", "check" not "test run". |

### 9.2 Interaction Patterns

| Pattern | Behavior |
|---|---|
| **Optimistic UI** | Not used for mutations. Always wait for server confirmation. |
| **Polling** | Non-terminal tasks poll every 3s. Backoff on failure. Pause when tab hidden. |
| **Lazy loading** | Logs, diffs, and JUnit XML load on demand from signed URLs. |
| **Debounce** | Search inputs debounced 300ms. |
| **Idempotency** | Submit buttons generate idempotency keys; double-submit is safe. |

### 9.3 Accessibility (WCAG 2.1 AA)

| Requirement | Implementation |
|---|---|
| Color contrast | All text meets 4.5:1 ratio (3:1 for large text) |
| Focus indicator | 2px `--border-focus` ring on all focusable elements |
| Keyboard nav | All interactive elements reachable and operable via keyboard |
| ARIA | `aria-label` on icon buttons, `aria-expanded` on expandables, `aria-live="polite"` on status updates |
| Reduced motion | `@media (prefers-reduced-motion: reduce)` disables animations |
| Touch targets | Minimum 44×44px on mobile |

---

## 10. Page-Specific Design Notes

### 10.1 Sign In

- Centered, single-column, max-width 400px
- Generous vertical spacing
- GitHub brand color for sign-in button (`#24292F` bg, white text)
- Subtle background pattern or gradient (very subtle, not distracting)

### 10.2 Repositories

- Card grid layout (responsive columns)
- Repository cards: repo icon, name, language badge, last task summary
- Refresh button in header with sync feedback

### 10.3 New Task

- Multi-section form with numbered sections
- Sticky configuration preview on desktop (right column)
- Live validation with inline error messages
- Submit button sticky at bottom on mobile

### 10.4 Task History

- Filter bar sticky at top
- Card list with hover states
- Outcome badges prominent
- "Load more" pagination (not infinite scroll — predictable)

### 10.5 Task Detail

- Header: title, repo, outcome badge, action buttons
- Tab bar: horizontal, scrollable on mobile
- Content: scrollable, max-width 900px for readability
- Timeline: vertical, color-coded connectors
- Diff viewer: full-width, monospace, line numbers
- Checks: table with expandable rows
- Log viewer: modal, monospace, truncation indicator

---

## 11. Animation & Transitions

| Animation | Duration | Easing | Usage |
|---|---|---|---|
| Fade in | 200ms | ease-out | Page content, modal |
| Fade out | 150ms | ease-in | Modal close |
| Slide up | 200ms | ease-out | Toast entrance |
| Slide down | 200ms | ease-in | Toast exit |
| Scale | 100ms | ease-out | Button active state |
| Pulse | 1.5s | ease-in-out | Skeleton loading, running spinner |
| Tab switch | 150ms | ease-out | Tab content transition |

**Reduced motion:** All animations disabled under `prefers-reduced-motion: reduce`.

---

## 12. Icon Set

Use **Lucide React** icons (open source, consistent, tree-shakeable).

| Icon | Usage |
|---|---|
| `CheckCircle2` | Verified, passed |
| `XCircle` | Failed |
| `AlertTriangle` | Blocked, warning |
| `MinusCircle` | Partially verified |
| `SkipForward` | Skipped |
| `HelpCircle` | Unavailable |
| `Ban` | Cancelled |
| `Loader2` | Running (spin animation) |
| `Clock` | Queued, timed out |
| `GitBranch` | Repository, branch |
| `GitPullRequest` | Pull request |
| `FileText` | Files, artifacts |
| `Search` | Search |
| `Plus` | Add, new |
| `RefreshCw` | Refresh, sync |
| `X` | Close |
| `ChevronDown` | Expand, dropdown |
| `ChevronLeft` | Back |
| `Download` | Download |
| `ExternalLink` | External link |
| `User` | User avatar |
| `LogOut` | Sign out |
| `Settings` | Settings |
| `Copy` | Copy to clipboard |

---

## 13. Implementation Notes

### 13.1 CSS Approach

- **Tailwind CSS** with custom design tokens (CSS custom properties)
- Dark theme as default; light theme via `data-theme="light"` attribute
- All colors referenced as Tailwind custom properties, never hardcoded hex values

### 13.2 Component Library

- **shadcn/ui** primitives (copied into project, not runtime dependency)
- Custom components built on top: StatusBadge, CheckTable, DiffView, LogViewer, Timeline

### 13.3 Diff Rendering

- Use a maintained diff-view library (e.g., `react-diff-view` or `diff2html`)
- Render as text nodes only — never inject diff content as HTML
- Syntax highlighting via `prismjs` or `shiki`

### 13.4 State Management

- **TanStack Query v5** for server state (caching, polling, mutations)
- No global client store needed
- Local component state via React hooks

---

*End of UI/UX Design Brief*
