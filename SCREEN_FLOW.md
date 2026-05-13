# Soccho - Screen Flow & Navigation

## 🗺️ Application Map

```
┌─────────────────────────────────────────────────────────┐
│                     AUTHENTICATION                       │
│                                                          │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐   │
│  │   Login    │ ←→ │  Register  │ → │    OTP     │   │
│  │            │    │            │    │ Verify     │   │
│  └────────────┘    └────────────┘    └────────────┘   │
│                                            │            │
│                                            ↓            │
└────────────────────────────────────────────┼────────────┘
                                             │
                    ┌────────────────────────┘
                    │
                    ↓
┌─────────────────────────────────────────────────────────┐
│                   MAIN APPLICATION                       │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │             Home Dashboard                       │   │
│  │  • Notification Drawer (slides from left)       │   │
│  │  • Summary Charts (Pie + Bar)                   │   │
│  │  • Friends List                                 │   │
│  │  • Bottom Navigation                            │   │
│  └─────────────────────────────────────────────────┘   │
│         │              │              │                 │
│         │              │              │                 │
│    ┌────┘         ┌────┘         ┌────┘                │
│    ↓              ↓              ↓                      │
│  ┌──────┐    ┌──────────┐    ┌─────────┐              │
│  │Friend│    │  Find    │    │ Profile │              │
│  │Detail│    │ Friends  │    │         │              │
│  └──────┘    └──────────┘    └─────────┘              │
│                                                         │
└─────────────────────────────────────────────────────────┘

                         ↓ (invalid route)

              ┌────────────────────┐
              │     404 Page       │
              │  (Broken Taka)     │
              └────────────────────┘
```

---

## 📱 Screen Breakdown

### 1️⃣ Login/Register Flow (`/`)
**Screen States:**
- Login (default)
- Register
- OTP Verification

**Navigation:**
- Login ↔ Register (horizontal slide)
- Either → OTP (after form submit)
- OTP → Home Dashboard (after verification)

**Key Interactions:**
- Slide animations between states
- Google OAuth quick login
- Auto-advance OTP input

---

### 2️⃣ Home Dashboard (`/home`)
**Features:**
- Hamburger menu → Notification Drawer
- Bell icon (with badge) → Notification Drawer
- Charts: Pie (given/received) + Bar (monthly trend)
- Friend cards → Click to Friend Detail
- Bottom nav: Home | Friends | Profile

**Navigation Paths:**
- Click friend card → `/friend/:id`
- Bottom nav "Friends" → `/friends`
- Bottom nav "Profile" → `/profile`

---

### 3️⃣ Friend Detail (`/friend/:id`)
**Features:**
- Back button → `/home`
- Hero card with large avatar + net balance
- Give/Lend money form
- Transaction timeline (chronological)
- Bottom navigation

**Actions:**
- Submit money transaction
- View transaction history
- Navigate via bottom nav

---

### 4️⃣ Find Friends (`/friends`)
**Features:**
- Back button → `/home`
- Search bar with history dropdown
- Live search results
- Suggested friends (sorted by loyalty)
- Loyalty score progress bars
- "Add Friend" buttons
- Bottom navigation

**Interactions:**
- Focus search → Shows history
- Type → Shows results (debounced)
- Clear X → Clears search
- Add friend → Sends request

---

### 5️⃣ Profile (`/profile`)
**Features:**
- Back button → `/home`
- Large avatar + user info
- Stats grid (Friends, Given, Received)
- Settings button
- Log out button → `/` (login)
- Bottom navigation

**Actions:**
- Log out → Returns to login screen
- Settings → (Future: settings page)

---

### 6️⃣ 404 Not Found (`*`)
**Features:**
- Animated broken taka coin
- "Lost your taka?" heading
- "Go Home" button → `/home`

**When Shown:**
- Any invalid route
- User manually enters wrong URL

---

## 🎯 Bottom Navigation

Available on all main screens (Home, Friends, Profile, Friend Detail):

```
┌──────────────────────────────────────────┐
│  [Home]      [Friends]      [Profile]    │
│   🏠            👥              👤        │
│   ●             -              -          │ ← Active indicator
└──────────────────────────────────────────┘
```

**Routes:**
- Home icon → `/home`
- Friends icon → `/friends`
- Profile icon → `/profile`

**Active State:**
- Indigo icon color (#4F46E5)
- Dot indicator below icon

---

## 🔄 Animation Flow

### Page Transitions
```
Login ↔ Register ↔ OTP
  ↓ (horizontal slide, 200ms)

Home Dashboard
  ↓ (fade/slide based on direction)

Sub-pages (Friend Detail, Find Friends, Profile)
  ↓ (standard navigation, no special transition)

404 Page
  ↓ (fade in)
```

### Component Animations
- **Notification Drawer:** Slide from left (200ms)
- **Friend Cards:** Hover lift (-2px) + shadow deepen
- **Transaction Cards:** Staggered fade-in on mount
- **Charts:** Animate on first render (800ms)
- **Buttons:** Scale to 98% on press
- **404 Coin:** Continuous bounce (2s infinite)

---

## 📊 Data Flow

### Mock Data Locations

**Home Dashboard:**
- `pieData`: Given vs Received (45K vs 30K)
- `barData`: 6-month trend
- `friends`: 4 sample friends with balances
- `notifications`: 3 sample notifications

**Friend Detail:**
- `transactions`: 4 sample transactions
- `friendName`: "Rahim Khan"
- `netBalance`: 5000 (positive)

**Find Friends:**
- `searchHistory`: Last 3 searches
- `searchResults`: 3 people
- `suggestedFriends`: 4 people with loyalty scores

**Profile:**
- `userName`: "Your Name"
- `userEmail`: "you@example.com"
- Stats: 12 friends, 45K given, 30K received

---

## 🎨 Visual Hierarchy

### Color Coding by Screen

**Login/Register/OTP:**
- Background: Indigo gradient (#4F46E5 → #7C3AED)
- Card: White
- Primary actions: Indigo buttons

**Home Dashboard:**
- Background: Light gray (#F3F4F6)
- Cards: White with shadow
- Charts: Indigo color scheme
- Balance chips: Green (owed) / Red (owe)

**Friend Detail:**
- Hero card: White with large colored balance
- Forms: Light gray inputs
- Timeline: White cards with colored icons

**Find Friends:**
- Search bar: White with border
- Cards: White with progress bars
- Loyalty bars: Indigo gradient

**Profile:**
- Stats cards: White grid
- Stats: Color-coded (Indigo, Green, Red)

**404:**
- Background: Dark (#111827)
- Coin: Indigo gradient with red crack
- Text: White/gray

---

## 🚀 User Journeys

### Journey 1: New User Sign Up
```
1. Land on Login page (/)
2. Click "Sign up"
3. Enter name, email, password
4. Submit form
5. Receive OTP
6. Enter 6-digit code
7. Verify → Redirect to Home (/home)
```

### Journey 2: Lend Money to Friend
```
1. On Home Dashboard
2. Click friend card
3. Navigate to Friend Detail (/friend/:id)
4. Fill in amount + optional due date + note
5. Click "Submit"
6. Transaction added to timeline
```

### Journey 3: Add New Friend
```
1. Click "Friends" in bottom nav
2. Navigate to Find Friends (/friends)
3. Search by name or browse suggestions
4. Click "Add" button
5. Friend request sent
```

### Journey 4: Handle Notification
```
1. See notification badge on bell icon
2. Click bell or hamburger menu
3. Notification drawer slides in from left
4. Review pending confirmation
5. Click "Agree" or "Disagree"
6. Drawer closes
```

---

## 🔐 Protected Routes (Future Enhancement)

Currently all routes are accessible. For production:

```tsx
Protected Routes:
- /home
- /friend/:id
- /friends
- /profile

Public Routes:
- / (login)
- * (404)
```

Implement auth guard to redirect unauthenticated users to `/`.

---

## 📱 Mobile-First Design

All screens designed for 375px mobile width:
- Bottom navigation (sticky)
- Full-width cards with 16px padding
- Touch-friendly button sizes (48px height minimum)
- Swipe gestures (drawer slide)

Desktop (1280px+):
- Same mobile layout, centered
- Max-width container (768px)
- Bottom nav can be replaced with sidebar (future)

---

## ✨ Interactive Elements

### Clickable Components
- ✅ Buttons (primary, secondary, ghost, danger)
- ✅ Friend cards (entire card is clickable)
- ✅ Navigation items (bottom nav icons)
- ✅ Search results (entire row clickable)
- ✅ Notification items (action buttons)
- ✅ Back buttons (arrow icons in headers)
- ✅ "Show More" buttons (load more content)

### Hover States
- ✅ Cards: Lift + shadow deepen
- ✅ Buttons: Background darken
- ✅ Links: Color change + underline
- ✅ Icons: Background highlight circle

### Focus States
- ✅ Inputs: Indigo ring (2px)
- ✅ Buttons: Indigo outline
- ✅ Search bar: Ring + border color change

---

**Navigation Status:** ✅ Complete  
**All Screens:** ✅ Built & Connected  
**Last Updated:** May 13, 2026
