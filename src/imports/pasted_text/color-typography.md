PROJECT: Soccho — Personal Lending & Borrowing Tracker
PLATFORM: Mobile-first PWA (primary: 375px wide mobile, secondary: 1280px desktop)
TONE: Facebook-inspired social app meets fintech dashboard — warm, trustworthy, personal, not corporate.

─────────────────────────────────────────
COLOR SYSTEM
─────────────────────────────────────────
Primary:         #4F46E5  (deep indigo)
Primary dark:    #3730A3
Primary light:   #818CF8
Surface:         #FFFFFF
Background:      #F3F4F6  (soft gray)
Positive/owed:   #10B981  (emerald green) — "friend owes you"
Negative/owe:    #EF4444  (red) — "you owe friend"
Text primary:    #111827
Text secondary:  #6B7280
Border:          #E5E7EB

─────────────────────────────────────────
TYPOGRAPHY
─────────────────────────────────────────
Display / headings: "Plus Jakarta Sans" Bold 700
Body / UI labels:   "DM Sans" Regular 400 / Medium 500
Numbers & amounts:  "JetBrains Mono" Medium 500  (monospace for alignment)
Fallback:           system-ui, sans-serif

─────────────────────────────────────────
COMPONENT LANGUAGE
─────────────────────────────────────────
Cards:
  - white surface
  - border-radius: 16px
  - box-shadow: 0 4px 20px rgba(0,0,0,0.06)
  - hover: translateY(-2px) + shadow deepens to 0 8px 28px rgba(0,0,0,0.10)
  - 3D depth achieved via layered shadows, NOT gradients

Balance Chip (on friend list cards):
  - pill shape, border-radius: 999px
  - Green variant: bg #D1FAE5, text #065F46, border 1px #6EE7B7
  - Red variant:   bg #FEE2E2, text #991B1B, border 1px #FCA5A5
  - Font: JetBrains Mono 13px Medium

Avatar Circles:
  - 44px diameter
  - Gradient fill using primary color ramp
  - White initials, DM Sans 500 16px
  - Ring border: 2px solid white with 1px outer indigo shadow

Bottom Navigation (mobile):
  - Sticky to bottom, white bg, border-top 1px #E5E7EB
  - 3 tabs: Home (house icon), Friends (people icon), Profile (person icon)
  - Active tab: indigo icon + 2px indigo underline indicator dot

─────────────────────────────────────────
SCREENS TO DESIGN
─────────────────────────────────────────

[SCREEN 1] Login / Register
  - Full-screen gradient background: #4F46E5 → #7C3AED (top to bottom, 150deg)
  - Centered white card (border-radius 24px, max-width 360px)
  - "Soccho" wordmark at top in Plus Jakarta Sans Bold
  - Email + password fields with animated focus rings (indigo glow)
  - Primary CTA button: full-width, indigo, border-radius 12px, 48px height
  - Google OAuth button: white bg, border 1px #E5E7EB, Google logo left-aligned
  - Slide transition between login ↔ register ↔ OTP entry screens (horizontal slide)
  - OTP screen: 6 individual digit input boxes in a row, auto-advance on input

[SCREEN 2] Home Dashboard (mobile)
  - Status bar + notification bell (top right, badge count circle in red)
  - Notification Drawer: slides in from LEFT, covers 70% screen width
    → Overlay: 30% right remains visible with 40% black scrim
    → Drawer bg: white, border-radius 0 16px 16px 0 on right edge
    → 3 notification types with distinct left-border colors:
       Orange (#F59E0B) = pending confirmation with Agree/Disagree chips
       Gray  (#9CA3AF) = payment received
       Red   (#EF4444) = due date reminder, pulsing red dot indicator
  - Summary section: two Chart.js charts side by side
    → Left: Pie chart (given vs received), animated on mount
    → Right: Bar chart (monthly trend), 6 bars, indigo fill
  - Friends list: scrollable cards
    → Each card: avatar circle + name + last transaction preview + balance chip
    → Cursor-style "Show More" button at bottom (indigo outlined, not filled)
  - Sticky bottom nav

[SCREEN 3] Friendship Detail Page
  - Hero card at top: friend's avatar (large, 72px) + name + net balance in large JetBrains Mono
    → Net balance font size: 32px, green or red depending on direction
  - "Give / Lend Money" form:
    → Amount field: large, centered, monospace, currency symbol prefix
    → Optional due date picker (date input, understated)
    → Animated submit button: scale + ripple on press
  - Transaction timeline below:
    → Cards in chronological order, fade-in on scroll
    → Each: amount (monospace), direction arrow (↑ you gave / ↓ you received), date, status chip
    → Status chips: "Pending" (amber), "Confirmed" (green), "Denied" (red)

[SCREEN 4] Find Friends
  - Search bar: full-width, border-radius 12px, magnifier icon left, clear X right
  - Below bar on focus: search history dropdown (last 10, Redis-backed)
    → Rows with clock icon, query text, subtle separator
  - Live results appear as user types (HTMX keyup, 300ms debounce)
    → Result cards: avatar + username + mutual friends count
    → "Add Friend" button: indigo, pill shape
  - "Suggested Friends" section below search results
    → Sorted by loyalty score
    → Each card shows loyalty score as a small progress-bar indicator (NOT a number)
    → "Show More" button with HTMX infinite scroll

[SCREEN 5] 404 Page
  - Centered layout, dark background #111827
  - Hero: animated SVG of a broken taka coin (₳ symbol, cracked down the middle)
    → Bounce animation on coin, 2s ease-in-out infinite
    → Crack glow effect in red
  - Heading: "Lost your taka?" — Plus Jakarta Sans Bold 32px white
  - Subtext: "This page doesn't exist." — DM Sans 16px #9CA3AF
  - CTA: "Go Home" button — indigo, border-radius 12px

─────────────────────────────────────────
ANIMATIONS & INTERACTIONS
─────────────────────────────────────────
All animations use CSS @keyframes only — no libraries.

Slide-in drawer:        translateX(-100%) → translateX(0),  200ms ease-out
Card hover:             translateY(0) → translateY(-2px),   150ms ease
Card mount:             scale(0.96) opacity(0) → scale(1) opacity(1), 150ms ease
Balance number count-up: JS requestAnimationFrame, 600ms duration
Skeleton loaders:        shimmer gradient animation on load placeholder rects
Notification pulse:      opacity 1 → 0.4 → 1, 1.5s infinite (red dot on due reminders)
Chart.js:               animated on first render, 800ms ease-in-out

─────────────────────────────────────────
SPACING SYSTEM
─────────────────────────────────────────
Base unit: 4px
xs: 4px  |  sm: 8px  |  md: 16px  |  lg: 24px  |  xl: 32px  |  2xl: 48px

Mobile screen padding: 16px left/right
Card internal padding: 16px
Section gaps: 24px
List item gaps: 12px

─────────────────────────────────────────
FIGMA COMPONENTS TO BUILD
─────────────────────────────────────────
Atoms:
  Button (primary, secondary, ghost, danger)
  Input field (default, focused, error)
  Balance chip (green, red)
  Status chip (pending, confirmed, denied)
  Avatar circle (S=32px, M=44px, L=72px)
  Notification dot (unread badge)
  Skeleton loader (rect variants)

Molecules:
  Friend list card
  Transaction timeline card
  Notification item (3 variants)
  Search result row
  OTP input group (6 boxes)
  Amount input with currency prefix

Organisms:
  Bottom navigation bar
  Notification drawer (full state)
  Home charts section
  Friends list section
  Friendship hero card
  Give/Lend money form

Pages:
  Login
  Register
  OTP verification
  Home dashboard
  Friendship detail
  Find friends
  404
