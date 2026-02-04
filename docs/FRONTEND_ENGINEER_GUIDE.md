# Frontend Engineer Guide
## Endurance Dashboard - Multi-Service Monitoring

---

## Current Status ✅

| Component | Status | Location |
|-----------|--------|----------|
| Basic Chat UI | ✅ Done | `dashboard/src/App.tsx` |
| Metrics Panel | ✅ Done | Single-query display |
| CSS Styling | ✅ Done | `dashboard/src/index.css` |

**Current Limitation**: Dashboard shows metrics for ONE query at a time.

---

## Vision: Multi-Service Monitoring Dashboard

The production dashboard needs to monitor **multiple AI services simultaneously**, each with multiple parallel conversations.

### Target Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ENDURANCE MONITORING DASHBOARD                   │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  MONITORED SERVICES                    [+ Add Service]       │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │  │
│  │  │ RTI Chatbot │ │ HR Bot     │ │ Legal Bot   │            │  │
│  │  │ Score: 87.2 │ │ Score: 92.1 │ │ Score: 78.5 │            │  │
│  │  │ 24 sessions │ │ 156 sessions│ │ 42 sessions │            │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  LIVE SESSION FEED                    Filter: All Services   │  │
│  │  ┌────────────────────────────────────────────────────────┐  │  │
│  │  │ 🔴 Session #abc123 | RTI Chatbot | Score: 45.2 | ALERT │  │  │
│  │  │ 🟢 Session #def456 | HR Bot      | Score: 91.3 | OK    │  │  │
│  │  │ 🟡 Session #ghi789 | Legal Bot   | Score: 68.7 | WARN  │  │  │
│  │  └────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────┐ ┌────────────────────────────┐   │
│  │  DIMENSION TRENDS (24h)    │ │  ALERTS & VIOLATIONS       │   │
│  │  [Animated Line Charts]    │ │  • 3 hallucinations        │   │
│  │  - Bias: ████████ 78%     │ │  • 2 low groundedness      │   │
│  │  - Ground: ██████████ 92% │ │  • 1 PII exposure attempt  │   │
│  └─────────────────────────────┘ └────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Required Features

### 1. Service Management

```typescript
interface MonitoredService {
  id: string;
  name: string;
  endpoint: string;               // e.g., "https://rti-bot.aws/chat"
  apiKey?: string;                // For authentication
  integrationMode: 'sdk' | 'webhook' | 'docker';
  status: 'active' | 'paused' | 'error';
  createdAt: string;
}
```

**UI Components Needed**:
- Service registration form
- Service list with status indicators
- Per-service configuration panel

### 2. Real-Time Session Feed

```typescript
interface LiveSession {
  sessionId: string;
  serviceId: string;
  query: string;
  response: string;
  overallScore: number;
  dimensions: Record<string, number>;
  hallucinations: number;
  timestamp: string;
  status: 'ok' | 'warning' | 'alert';
}
```

**Implementation**:
- WebSocket connection to Endurance API
- Auto-updating session list
- Color-coded status (🟢 green > 80, 🟡 yellow 60-80, 🔴 red < 60)

### 3. Session Detail Modal

When clicking a session, show:
- Full query and response
- All 9 dimension scores with visual bars
- Extracted claims with verification status
- Source documents used
- Human feedback submission form

### 4. Analytics Dashboard

- 24-hour trend charts per dimension
- Aggregate scores by service
- Alert frequency over time
- Top issues summary

---

## API Endpoints to Use

### Endurance API (port 8000)

```typescript
// Get all sessions
GET /v1/sessions
Response: { sessions: LiveSession[] }

// Get session details
GET /v1/sessions/{session_id}
Response: { session: SessionDetail }

// Subscribe to real-time updates (WebSocket)
WS /v1/stream
Events: { type: 'new_session', data: LiveSession }

// Register a service
POST /v1/services
Body: { name, endpoint, integration_mode }

// Get service stats
GET /v1/services/{service_id}/stats
Response: { avgScore, sessionCount, alerts }
```

---

## Component Structure

```
dashboard/src/
├── App.tsx                    # Main layout
├── components/
│   ├── Header.tsx             # Nav + service switcher
│   ├── ServiceList.tsx        # Registered services
│   ├── SessionFeed.tsx        # Live session stream
│   ├── SessionDetail/
│   │   ├── Overview.tsx       # Score + dimensions
│   │   ├── Claims.tsx         # Extracted claims
│   │   ├── Sources.tsx        # RAG documents
│   │   └── Feedback.tsx       # Human review form
│   ├── Analytics/
│   │   ├── TrendChart.tsx     # Time-series charts
│   │   ├── DimensionBars.tsx  # Score bars
│   │   └── AlertList.tsx      # Recent alerts
│   └── common/
│       ├── ScoreRing.tsx      # Circular progress
│       ├── StatusBadge.tsx    # OK/WARN/ALERT
│       └── Modal.tsx          # Reusable modal
├── hooks/
│   ├── useWebSocket.ts        # Real-time updates
│   ├── useSessions.ts         # Session management
│   └── useServices.ts         # Service CRUD
└── types/
    └── index.ts               # TypeScript interfaces
```

---

## Tech Stack Recommendations

| Need | Recommendation |
|------|---------------|
| Charts | Recharts or Chart.js |
| State | Zustand (lightweight) or Redux |
| WebSocket | socket.io-client or native WS |
| UI Components | Keep vanilla CSS or add shadcn/ui |
| Data Fetching | TanStack Query (React Query) |

---

## Priority Order

1. **P0 (Must Have)**:
   - Multi-session list with scores
   - Session detail view
   - Real-time updates

2. **P1 (Should Have)**:
   - Service registration
   - Alert filtering
   - Dimension trends

3. **P2 (Nice to Have)**:
   - Export reports
   - Slack/email alerts
   - Dark/light theme toggle

---

## Design Tokens (Already in CSS)

```css
--primary: #6366f1;
--success: #10b981;
--warning: #f59e0b;
--danger: #ef4444;
--background: #0f172a;
--surface: #1e293b;
```

---

## Questions for Frontend Engineer

1. **State Management**: Zustand preferred or Redux?
2. **Charts**: Any preference for charting library?
3. **Mobile**: Need responsive design for tablets?

---

**Contact**: Slack for questions or design clarifications.
