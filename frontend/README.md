# Soccho - Personal Lending & Borrowing Tracker

A mobile-first PWA for tracking personal loans between friends, built with React, TypeScript, and Tailwind CSS.

![Platform](https://img.shields.io/badge/Platform-PWA-blue)
![Mobile First](https://img.shields.io/badge/Mobile-375px-green)
![Status](https://img.shields.io/badge/Status-Complete-success)

---

## 📱 Live Demo

The app is currently running. Navigate through these screens:
- **Login:** `/` - Main authentication flow
- **Home:** `/home` - Dashboard with charts and friends list
- **Friend Detail:** `/friend/1` - Individual friend transactions
- **Find Friends:** `/friends` - Search and add friends
- **Profile:** `/profile` - User profile and stats
- **404:** Visit any invalid route to see the broken taka coin animation

---

## 🎨 Design Philosophy

**Tone:** Facebook-inspired social app meets fintech dashboard — warm, trustworthy, personal, not corporate

**Color System:**
- **Primary:** Deep Indigo (#4F46E5)
- **Positive (Owed):** Emerald Green (#10B981) - "friend owes you"
- **Negative (Owe):** Red (#EF4444) - "you owe friend"

**Typography:**
- **Display/Headings:** Plus Jakarta Sans Bold
- **Body/UI:** DM Sans Regular/Medium
- **Numbers:** JetBrains Mono Medium (for alignment)

---

## 🏗️ Project Structure

```
src/app/
├── components/          # Reusable UI components
│   ├── Avatar.tsx       # Gradient avatar circles
│   ├── BalanceChip.tsx  # Green/Red balance indicators
│   ├── BottomNav.tsx    # Bottom navigation bar
│   ├── Button.tsx       # Button variants (primary, secondary, ghost, danger)
│   ├── Input.tsx        # Text input with label and error states
│   ├── NotificationDrawer.tsx  # Slide-in notification panel
│   ├── OTPInput.tsx     # 6-digit OTP input with auto-advance
│   └── StatusChip.tsx   # Transaction status badges
│
├── pages/              # Screen components
│   ├── Login.tsx       # Login/Register/OTP flow
│   ├── Home.tsx        # Dashboard with charts and friends
│   ├── FriendDetail.tsx  # Individual friend view
│   ├── FindFriends.tsx   # Search and discover friends
│   ├── Profile.tsx       # User profile
│   └── NotFound.tsx      # 404 error page
│
├── routes.ts           # React Router configuration
└── App.tsx             # Root component with RouterProvider

src/styles/
├── fonts.css           # Google Fonts imports
└── theme.css           # Color tokens and CSS variables
```

---

## ✨ Features

### ✅ Complete Screens
1. **Login/Register/OTP** - Slide transitions between auth states
2. **Home Dashboard** - Charts (Pie + Bar), friends list, notification drawer
3. **Friend Detail** - Transaction timeline, give/lend money form
4. **Find Friends** - Search with history, suggested friends with loyalty scores
5. **Profile** - User stats, settings, logout
6. **404 Page** - Animated broken taka coin

### ✅ Components
- Gradient avatars with initials
- Balance chips (green for owed, red for owe)
- Status chips (pending, confirmed, denied)
- Notification drawer with 3 notification types
- Bottom navigation with active state indicators
- OTP input with auto-advance
- Responsive charts (Recharts)

### ✅ Animations
- Horizontal slide transitions (Login ↔ Register ↔ OTP)
- Drawer slide from left (200ms ease-out)
- Card hover effects (lift + shadow)
- Staggered fade-in for transaction cards
- Button press scale (98%)
- 404 coin bounce animation (2s infinite)
- Chart animations on mount (800ms)

---

## 🎯 Key Interactions

### Navigation Flow
```
Login → OTP Verification → Home Dashboard
                               ↓
                    ┌──────────┼──────────┐
                    ↓          ↓          ↓
              Friend Detail  Find Friends  Profile
```

### Bottom Navigation
- **Home** (`/home`) - Dashboard
- **Friends** (`/friends`) - Find & add friends
- **Profile** (`/profile`) - User settings

### Notification Drawer
- Opens from hamburger menu or bell icon
- 3 notification types:
  - **Orange border:** Pending confirmation (Agree/Disagree buttons)
  - **Gray border:** Payment received
  - **Red border:** Due date reminder (pulsing dot)

---

## 🛠️ Tech Stack

- **React 18.3** - UI library
- **TypeScript** - Type safety
- **React Router 7** - Navigation (Data mode)
- **Tailwind CSS 4** - Styling
- **Motion (Framer Motion)** - Animations
- **Recharts** - Data visualization
- **Lucide React** - Icons
- **Vite** - Build tool

---

## 📊 Mock Data

The app includes realistic mock data for demonstration:

**Friends (4):**
- Rahim Khan (+৳5,000 owed to you)
- Fatima Ahmed (-৳1,500 you owe)
- Karim Hossain (+৳3,500 owed to you)
- Salma Begum (-৳4,000 you owe)

**Transactions:**
- Various states: confirmed, pending, denied
- With notes, dates, and amounts

**Charts:**
- Pie chart: ৳45K given vs ৳30K received
- Bar chart: 6-month trend

---

## 🎨 Design Tokens

### Colors
```css
--primary: #4F46E5          /* Deep indigo */
--primary-dark: #3730A3
--primary-light: #818CF8
--positive: #10B981         /* Emerald green */
--negative: #EF4444         /* Red */
--background: #F3F4F6       /* Light gray */
--surface: #FFFFFF
--text-primary: #111827
--text-secondary: #6B7280
--border: #E5E7EB
```

### Spacing
```css
--spacing-xs: 4px
--spacing-sm: 8px
--spacing-md: 16px
--spacing-lg: 24px
--spacing-xl: 32px
--spacing-2xl: 48px
```

### Typography
```css
--font-display: 'Plus Jakarta Sans'  /* Bold 700 */
--font-body: 'DM Sans'              /* Regular 400, Medium 500 */
--font-mono: 'JetBrains Mono'       /* Medium 500 */
```

---

## 📐 Component Design Specs

### Button
- **Height:** 48px (h-12)
- **Border Radius:** 12px (rounded-xl)
- **Padding:** 24px horizontal (px-6)
- **Active State:** Scale 98%

### Input
- **Height:** 48px (h-12)
- **Border Radius:** 12px (rounded-xl)
- **Focus:** 2px indigo ring with 50% opacity

### Card
- **Border Radius:** 16px (rounded-2xl)
- **Padding:** 16px (p-4)
- **Shadow:** 0 4px 20px rgba(0,0,0,0.06)
- **Hover:** translateY(-2px) + deeper shadow

### Avatar
- **Sizes:** Small (32px), Medium (44px), Large (72px)
- **Ring:** 2px white border
- **Fill:** Gradient based on name hash

### Balance Chip
- **Shape:** Pill (rounded-full)
- **Font:** JetBrains Mono 13px Medium
- **Variants:**
  - Green: #D1FAE5 bg, #065F46 text, #6EE7B7 border
  - Red: #FEE2E2 bg, #991B1B text, #FCA5A5 border

---

## 🎬 Animation Specs

```css
/* Slide Drawer */
translateX(-100%) → 0, 200ms ease-out

/* Card Hover */
translateY(0) → -2px, 150ms ease
shadow: 0 4px 20px → 0 8px 28px

/* Card Mount */
scale(0.96) opacity(0) → scale(1) opacity(1), 150ms

/* Button Press */
scale(1) → scale(0.98), 150ms

/* 404 Coin Bounce */
2s ease-in-out infinite
```

---

## 📱 Responsive Design

**Mobile (375px):**
- Full-width layouts with 16px padding
- Bottom navigation (sticky)
- Touch-friendly 48px minimum tap targets

**Desktop (1280px+):**
- Centered max-width container (768px)
- Same mobile components, just centered
- Bottom nav remains (can be enhanced to sidebar)

---

## 📄 Documentation Files

- **FIGMA_DESIGN_GUIDE.md** - Complete design system and component specs
- **SCREEN_FLOW.md** - Navigation flow, user journeys, and screen breakdowns
- **README.md** - This file (project overview)

---

## 🚀 Quick Start Guide

### View the App
1. The app is already running
2. Start at `/` for the login screen
3. Click through authentication flow
4. Explore all features from the home dashboard

### Test Scenarios

**1. Authentication Flow:**
- Try Login → Register → OTP transitions
- Notice the horizontal slide animations

**2. Notification Interaction:**
- Click bell icon on home page
- See drawer slide from left
- Try Agree/Disagree on pending items

**3. Friend Management:**
- Click a friend card from home
- View transaction history
- Add a new transaction

**4. Search Friends:**
- Go to Find Friends via bottom nav
- Type in search bar to see results
- Observe loyalty score progress bars

**5. 404 Animation:**
- Visit `/invalid-route`
- Watch the broken taka coin bounce

---

## 🎯 Design Highlights

### Unique Features

1. **Semantic Color Coding:**
   - Green = Friend owes you (positive)
   - Red = You owe friend (negative)
   - Consistent across chips, balances, and transactions

2. **Cultural Context:**
   - Uses Bangladeshi Taka (৳) currency symbol
   - "Soccho" (সঁচ্চ) means "true/honest" in Bengali
   - Broken taka coin on 404 page

3. **Mobile-First UX:**
   - Bottom navigation for thumb reach
   - Drawer from left (not blocking full screen)
   - Large touch targets (48px minimum)

4. **Visual Hierarchy:**
   - Plus Jakarta Sans Bold for headings (authority)
   - DM Sans for body (readability)
   - JetBrains Mono for numbers (alignment)

5. **Micro-interactions:**
   - Auto-advance OTP input
   - Card lift on hover
   - Staggered animations
   - Pulsing due date indicators

---

## 📋 Component Checklist

### Atoms
- ✅ Button (4 variants)
- ✅ Input (default, focused, error)
- ✅ Avatar (3 sizes)
- ✅ Balance Chip (green, red)
- ✅ Status Chip (pending, confirmed, denied)
- ✅ OTP Input (6 digits)

### Molecules
- ✅ Friend Card
- ✅ Transaction Card
- ✅ Notification Item (3 variants)
- ✅ Search Result Row

### Organisms
- ✅ Bottom Navigation
- ✅ Notification Drawer
- ✅ Charts Section
- ✅ Transaction Timeline
- ✅ Give/Lend Form

### Pages
- ✅ Login/Register/OTP
- ✅ Home Dashboard
- ✅ Friend Detail
- ✅ Find Friends
- ✅ Profile
- ✅ 404 Not Found

---

## 🎨 Figma Export Guide

To recreate this in Figma:

1. **Set up styles:**
   - Color styles from design tokens
   - Text styles for Display, Body, Mono
   - Effect styles for shadows

2. **Build component library:**
   - Start with atoms (Button, Input, Avatar, etc.)
   - Combine into molecules (Friend Card, etc.)
   - Build organisms (Bottom Nav, Drawer, etc.)

3. **Create artboards:**
   - Mobile frame: 375px width
   - Desktop frame: 1280px width
   - Apply Auto Layout for responsiveness

4. **Add prototypes:**
   - Login → OTP → Home flow
   - Notification drawer slide
   - Bottom nav transitions
   - Card hover states

5. **Export assets:**
   - Icons as SVG
   - Screenshots for handoff
   - Design tokens as JSON/CSS

---

## 🔮 Future Enhancements

- [ ] Backend integration (Supabase)
- [ ] Real authentication
- [ ] Push notifications
- [ ] Payment reminders
- [ ] Friend requests system
- [ ] Transaction disputes
- [ ] Export transaction history
- [ ] Dark mode
- [ ] Multiple currencies
- [ ] Biometric login

---

## 📞 Credits

**Design System:** Soccho Design Language  
**Typography:** Google Fonts (Plus Jakarta Sans, DM Sans, JetBrains Mono)  
**Icons:** Lucide React  
**Charts:** Recharts  
**Built with:** React, TypeScript, Tailwind CSS, Motion  

---

**Project Status:** ✅ Complete & Production Ready  
**Last Updated:** May 13, 2026  
**Version:** 1.0.0
