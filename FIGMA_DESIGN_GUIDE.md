# Soccho — Figma Design Documentation

## Project Overview
**Name:** Soccho  
**Platform:** Mobile-first PWA (375px mobile primary, 1280px desktop secondary)  
**Description:** Personal lending & borrowing tracker app  
**Design Philosophy:** Facebook-inspired social app meets fintech dashboard — warm, trustworthy, personal

---

## 🎨 Design System

### Color Palette
```
Primary Colors:
- Primary:       #4F46E5 (deep indigo)
- Primary Dark:  #3730A3
- Primary Light: #818CF8

Surface Colors:
- Surface:       #FFFFFF
- Background:    #F3F4F6 (soft gray)

Semantic Colors:
- Positive/Owed: #10B981 (emerald green) — "friend owes you"
- Negative/Owe:  #EF4444 (red) — "you owe friend"

Text Colors:
- Primary:       #111827
- Secondary:     #6B7280

Borders:
- Border:        #E5E7EB
```

### Typography
```
Display/Headings:  "Plus Jakarta Sans" Bold 700
Body/UI Labels:    "DM Sans" Regular 400 / Medium 500
Numbers/Amounts:   "JetBrains Mono" Medium 500 (monospace)
Fallback:          system-ui, sans-serif
```

### Spacing System
```
Base Unit: 4px
xs:  4px
sm:  8px
md:  16px
lg:  24px
xl:  32px
2xl: 48px

Mobile padding: 16px left/right
Card padding:   16px
Section gaps:   24px
List gaps:      12px
```

---

## 🧩 Component Library

### Atoms

#### Button
- **Primary:** Full-width indigo (#4F46E5), 48px height, 12px border-radius
- **Secondary:** White bg, 1px border #E5E7EB
- **Ghost:** Transparent bg, indigo text
- **Danger:** Red (#EF4444)
- **Interactions:** Scale down to 98% on active press

#### Input Field
- **Default:** 48px height, #F3F4F6 bg, border #E5E7EB, 12px border-radius
- **Focused:** 2px ring indigo with 50% opacity
- **Error:** Red border and ring

#### Balance Chip
- **Green Variant (Owed):**
  - Background: #D1FAE5
  - Text: #065F46
  - Border: 1px #6EE7B7
- **Red Variant (Owe):**
  - Background: #FEE2E2
  - Text: #991B1B
  - Border: 1px #FCA5A5
- Font: JetBrains Mono 13px Medium, pill shape (border-radius: 999px)

#### Status Chip
- **Pending:** Amber bg (#FEF3C7), dark amber text (#92400E)
- **Confirmed:** Green bg (#D1FAE5), dark green text (#065F46)
- **Denied:** Red bg (#FEE2E2), dark red text (#991B1B)

#### Avatar Circle
Sizes: S=32px, M=44px, L=72px
- Gradient fill using color-based hash from name
- White initials, DM Sans 500
- 2px white ring border with 1px indigo outer shadow

#### OTP Input
- 6 individual digit boxes in a row
- 48px width × 56px height each
- Auto-advance on input
- JetBrains Mono font

---

### Molecules

#### Friend List Card
```
Structure:
[Avatar] [Name + Last Transaction] [Balance Chip]
         [Small text description]

Styling:
- White bg, 16px border-radius
- Shadow: 0 4px 20px rgba(0,0,0,0.06)
- Hover: translateY(-2px) + deeper shadow
- Padding: 16px
```

#### Transaction Timeline Card
```
Structure:
[Arrow Icon] [Amount + Status Chip]
             [Note text]
             [Date]

Icon Colors:
- Up Arrow (gave): Red bg (#FEE2E2)
- Down Arrow (received): Green bg (#D1FAE5)
```

#### Notification Item
3 variants with distinct left-border colors:
- **Orange (#F59E0B):** Pending confirmation with Agree/Disagree chips
- **Gray (#9CA3AF):** Payment received
- **Red (#EF4444):** Due date reminder with pulsing red dot

---

### Organisms

#### Bottom Navigation Bar
- Sticky to bottom, white bg, border-top 1px #E5E7EB
- 3 tabs: Home (house icon), Friends (people icon), Profile (person icon)
- Active tab: indigo icon + 2px indigo dot indicator at bottom
- Height: 64px

#### Notification Drawer
- Slides in from LEFT, covers 70% screen width
- Right 30% visible with 40% black scrim overlay
- White bg, rounded-r-2xl (16px on right edge)
- Animated slide: translateX(-100%) → 0, 200ms ease-out

#### Home Charts Section
```
Grid: 2 columns
Left:  Pie chart (given vs received), animated 800ms
Right: Bar chart (monthly trend), 6 bars, indigo fill
```

---

## 📱 Screens Implemented

### 1. Login / Register / OTP
**Route:** `/`

**Features:**
- Full-screen gradient background: #4F46E5 → #7C3AED (150deg)
- Centered white card (24px border-radius, max-width 360px)
- Horizontal slide transitions between screens (200ms ease-out)
- Email + password fields with animated focus rings
- Google OAuth button with logo
- 6-digit OTP input with auto-advance

**Animations:**
- Slide enter/exit: ±300px horizontal translation with opacity fade
- Focus ring: 2px indigo glow on input focus

---

### 2. Home Dashboard
**Route:** `/home`

**Features:**
- Header with hamburger menu + Soccho logo + notification bell (with badge count)
- Notification drawer (slides from left)
- Summary section with Pie + Bar charts (Chart.js)
- Friends list with scrollable cards
- Bottom navigation

**Components:**
- NotificationDrawer with 3 notification types
- Friend cards with avatars, names, last transaction, balance chips
- "Show More" button (outlined indigo)

**Data Visualizations:**
- Pie chart: Given vs Received (indigo gradient)
- Bar chart: 6-month trend with indigo bars

---

### 3. Friendship Detail Page
**Route:** `/friend/:id`

**Features:**
- Hero card: Large avatar (72px) + friend name + net balance
- Net balance: 32px JetBrains Mono, green/red based on direction
- Give/Lend Money form:
  - Large centered amount input with ৳ prefix
  - Optional due date picker
  - Note textarea
  - Submit button with scale animation
- Transaction timeline:
  - Chronological cards with fade-in on scroll
  - Direction arrows (↑ gave / ↓ received)
  - Amount, status chip, note, date

**Animations:**
- Card mount: Staggered fade-in (150ms each, 50ms delay between)
- Button press: Scale to 98%

---

### 4. Find Friends
**Route:** `/friends`

**Features:**
- Search bar with magnifier icon + clear X button
- Search history dropdown (last 10 searches with clock icons)
- Live search results (300ms debounce simulation)
- Result cards: avatar + username + mutual friends count
- Loyalty score progress bar (NOT a number)
- Suggested Friends section (sorted by loyalty score)
- "Show More" button with infinite scroll capability

**Interactions:**
- Focus shows search history
- Typing shows live results
- Each result has "Add Friend" pill button

---

### 5. Profile
**Route:** `/profile`

**Features:**
- Large avatar (72px) + name + email
- Stats grid (3 columns): Friends count, Given amount, Received amount
- Settings button
- Log out button (red)

---

### 6. 404 Error Page
**Route:** `*` (catch-all)

**Features:**
- Dark background (#111827)
- Animated broken taka coin (₳ symbol):
  - Split in half (left: #4F46E5, right: #7C3AED)
  - Zigzag crack down the middle with red glow effect
  - Bounce animation (2s ease-in-out infinite)
  - Sparkle/ping effects around crack
- Heading: "Lost your taka?" (Plus Jakarta Sans Bold 32px white)
- Subtext: "This page doesn't exist." (#9CA3AF)
- "Go Home" button (indigo)

**Animations:**
- Bounce: 2s infinite ease-in-out
- Crack glow: Red (#EF4444) with Gaussian blur filter
- Sparkle dots: Pulsing animation (staggered delays)

---

## 🎬 Animations & Interactions

All animations use CSS only (no external libraries except Motion for page transitions):

```css
/* Slide-in drawer */
translateX(-100%) → translateX(0), 200ms ease-out

/* Card hover */
translateY(0) → translateY(-2px), 150ms ease
box-shadow: 0 4px 20px rgba(0,0,0,0.06) → 0 8px 28px rgba(0,0,0,0.10)

/* Card mount */
scale(0.96) opacity(0) → scale(1) opacity(1), 150ms ease

/* Notification pulse (red dot) */
opacity: 1 → 0.4 → 1, 1.5s infinite

/* Button active press */
scale(1) → scale(0.98), 150ms ease

/* Chart animations */
Chart.js: 800ms ease-in-out on first render
```

---

## 📐 Layout Principles

### Mobile (375px)
- Full-width layouts with 16px horizontal padding
- Max-width container: 448px (md) centered
- Cards: Full width with 16px border-radius
- Bottom nav: Sticky, 64px height
- Safe area insets respected

### Desktop (1280px+)
- Centered max-width container (768px)
- Same mobile components, just centered
- Bottom nav can be replaced with sidebar (future enhancement)

---

## 🔧 Implementation Notes

### Fonts Loaded
```css
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700&family=DM+Sans:wght@400;500&family=JetBrains+Mono:wght@500&display=swap');
```

### Key Libraries Used
- **React Router:** Navigation between screens
- **Motion (Framer Motion):** Page transitions and animations
- **Recharts:** Charts (Pie and Bar)
- **Lucide React:** Icons (Bell, Home, Users, etc.)

### Routing Structure
```
/              → Login page
/home          → Home dashboard
/friend/:id    → Friend detail
/friends       → Find friends
/profile       → User profile
/*             → 404 page
```

---

## ✅ Design Checklist

All screens include:
- ✅ Correct color palette (indigo primary, green positive, red negative)
- ✅ Proper typography (Plus Jakarta Sans for headings, DM Sans for body, JetBrains Mono for numbers)
- ✅ 16px border-radius on cards (24px on login card)
- ✅ Hover states with translateY and shadow changes
- ✅ Mobile-first responsive design
- ✅ Smooth animations (200ms transitions)
- ✅ Bottom navigation on mobile screens
- ✅ Semantic color usage (green for "owed", red for "owe")

---

## 🎯 Figma Component Mapping

When recreating in Figma, build these as components:

**Atoms:**
- Button (4 variants)
- Input (3 states: default, focused, error)
- Balance Chip (2 variants: green, red)
- Status Chip (3 variants: pending, confirmed, denied)
- Avatar (3 sizes)
- OTP Input Group

**Molecules:**
- Friend Card
- Transaction Card
- Notification Item (3 variants)
- Search Result Row

**Organisms:**
- Bottom Nav Bar
- Notification Drawer
- Charts Section
- Transaction Timeline

**Pages:**
- Login/Register/OTP (3 states)
- Home Dashboard
- Friendship Detail
- Find Friends
- Profile
- 404

---

## 🚀 Next Steps

To export this as a Figma design:

1. Create a new Figma file named "Soccho - Lending Tracker"
2. Set up color styles matching the palette above
3. Set up text styles for Display, Body, and Mono fonts
4. Build component library (Atoms → Molecules → Organisms)
5. Create artboards for each screen at 375px width
6. Apply Auto Layout for responsive components
7. Add interactive prototypes for transitions
8. Export design tokens for handoff

---

**Design Status:** ✅ Complete  
**Implementation Status:** ✅ Fully Built  
**Last Updated:** May 13, 2026
