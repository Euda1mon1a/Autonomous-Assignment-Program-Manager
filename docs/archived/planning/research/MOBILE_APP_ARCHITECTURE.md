# Mobile App Architecture Research

**Project:** Residency Scheduler Mobile Application
**Author:** Terminal 6 - Mobile App Architecture Research
**Date:** 2025-12-19
**Status:** Research & Recommendations

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Technology Decision](#technology-decision)
3. [Offline-First Architecture](#offline-first-architecture)
4. [Push Notifications](#push-notifications)
5. [Authentication & Security](#authentication--security)
6. [Architecture Patterns](#architecture-patterns)
7. [Development Considerations](#development-considerations)
8. [Technology Stack Recommendation](#technology-stack-recommendation)
9. [Implementation Timeline](#implementation-timeline)
10. [Sources & References](#sources--references)

---

## Executive Summary

The Residency Scheduler mobile app will provide medical professionals with on-the-go access to schedules, swap requests, compliance monitoring, and emergency notifications. Given the healthcare context and HIPAA requirements, our architecture prioritizes **security, offline capability, and reliability**.

### Key Recommendations

| Decision Area | Recommendation | Rationale |
|--------------|----------------|-----------|
| **Framework** | Expo Managed Workflow | Faster development, easier maintenance, sufficient for requirements |
| **Local Database** | WatermelonDB | High performance, reactive, built for offline-first |
| **State Management** | Zustand + TanStack Query | Lightweight local state + server state management |
| **Push Notifications** | Expo Notifications + FCM | Easy setup, enterprise-ready, cost-effective |
| **Authentication** | expo-local-authentication + react-native-keychain | Biometric support + secure token storage |
| **Navigation** | React Navigation v6 | Industry standard, excellent TypeScript support |

---

## 1. Technology Decision

### Expo Managed Workflow vs Bare Workflow vs React Native CLI

#### Current State (2025)

The distinction between Expo managed and bare workflows has evolved significantly. As of 2025, **the only real difference is whether you generate native folders (ios/android) on demand via config plugins (managed) or commit them to source control (bare)**. With the introduction of Config Plugins and Continuous Native Generation (CNG), most customizations can be done in the managed workflow without ejecting.

#### Comparison Matrix

| Factor | Expo Managed | Expo Bare | React Native CLI |
|--------|--------------|-----------|------------------|
| **Setup Time** | Minutes | Hours | Hours |
| **Native Code Access** | Via config plugins | Full access | Full access |
| **Dependency Management** | Automatic | Manual | Manual |
| **EAS Build Support** | Native | Native | Via integration |
| **OTA Updates** | Built-in | Built-in | Requires setup |
| **Development Speed** | Fastest | Medium | Medium |
| **Customization** | High (via plugins) | Unlimited | Unlimited |
| **Maintenance Burden** | Low | Medium | Medium |

#### Recommendation: **Expo Managed Workflow**

**Rationale:**

1. **Sufficient Customization**: With config plugins, we can implement all required features (biometrics, push notifications, offline storage) without native code
2. **Faster Time to Market**: No need for Xcode or Android Studio setup; one command to start
3. **Easier Maintenance**: Expo handles dependency upgrades and native code changes
4. **EAS Integration**: Seamless cloud builds and OTA updates
5. **Team Scalability**: New developers can onboard in minutes, not days
6. **Future Flexibility**: Can always move to bare workflow if truly needed (though rarely necessary)

**Trade-offs Accepted:**

- Slightly less control over native build process (not a concern for our use case)
- Dependency on Expo's ecosystem (acceptable given their stability and enterprise adoption)

#### Exit Strategy

If we later need custom native modules beyond what config plugins support, we can:
- Use Local Expo Modules (write custom native code in managed workflow)
- Or transition to bare workflow (seamless process, just generates and commits native folders)

---

## 2. Offline-First Architecture

### Why Offline-First Matters

Medical professionals work in environments with:
- **Unreliable connectivity** (hospital basements, rural clinics, during emergencies)
- **Need for instant access** (viewing schedules, accepting swaps, checking coverage)
- **Critical operations** that can't wait for network availability

### Local Database: WatermelonDB

#### Why WatermelonDB?

WatermelonDB is the **clear winner** for React Native offline-first apps in 2025:

**Performance:**
- Built on SQLite with lazy loading and observable queries
- Queries run on separate native thread (no JS bridge blocking)
- Most queries resolve instantly (even with thousands of records)
- Optimized for complex, data-heavy applications

**Architecture:**
- Reactive queries (automatic UI updates when data changes)
- Integrates perfectly with React's component model
- First-class TypeScript support
- Designed specifically for React Native

**Offline Capabilities:**
- Local-first by design (data stored locally, synced when online)
- Built-in sync primitives and adapters
- Conflict resolution support

#### Alternatives Considered

| Database | Pros | Cons | Verdict |
|----------|------|------|---------|
| **AsyncStorage** | Simple, built-in | No querying, slow at scale | ❌ Too limited |
| **SQLite** | Fast, SQL queries | Requires manual React integration | ⚠️ More work |
| **Realm** | Good performance | Large bundle, complex setup | ⚠️ Heavier than needed |
| **WatermelonDB** | Reactive, fast, React-native | Requires sync endpoint | ✅ **Recommended** |

### Synchronization Strategy

#### Architecture

```
┌─────────────────────────────────────────┐
│         Mobile App (React Native)        │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │      UI Components (React)         │ │
│  └──────────────┬─────────────────────┘ │
│                 │                        │
│  ┌──────────────▼─────────────────────┐ │
│  │   WatermelonDB (Observable Queries)│ │
│  │   - Local SQLite Database          │ │
│  │   - Lazy Loading                   │ │
│  │   - Reactive Updates               │ │
│  └──────────────┬─────────────────────┘ │
│                 │                        │
│  ┌──────────────▼─────────────────────┐ │
│  │      Sync Manager                  │ │
│  │   - Queue local changes            │ │
│  │   - Background sync                │ │
│  │   - Conflict resolution            │ │
│  └──────────────┬─────────────────────┘ │
└─────────────────┼─────────────────────┘
                  │
                  │ HTTPS (JWT Auth)
                  │
        ┌─────────▼──────────┐
        │  Backend API       │
        │  - Push changes    │
        │  - Pull changes    │
        │  - Conflict res.   │
        └─────────┬──────────┘
                  │
        ┌─────────▼──────────┐
        │  PostgreSQL        │
        │  (Source of Truth) │
        └────────────────────┘
```

#### Sync Protocol

**Push Endpoint** (`POST /api/v1/sync/push`):
```json
{
  "changes": {
    "assignments": {
      "created": [...],
      "updated": [...],
      "deleted": [...]
    },
    "swaps": {
      "created": [...],
      "updated": [...]
    }
  },
  "lastPulledAt": "2025-12-19T10:30:00Z"
}
```

**Pull Endpoint** (`GET /api/v1/sync/pull?lastPulledAt=...`):
```json
{
  "changes": {
    "assignments": [...],
    "swaps": [...],
    "persons": [...]
  },
  "timestamp": "2025-12-19T10:35:00Z"
}
```

#### Sync Triggers

1. **On App Launch**: Pull latest changes
2. **On Network Reconnect**: Push local changes, then pull remote
3. **Background Sync**: Every 15 minutes (using `expo-background-fetch`)
4. **User-Initiated**: Pull-to-refresh gesture
5. **After Local Write**: Queue push for next sync window

#### Conflict Resolution Strategy

**Last-Write-Wins with Server Authority:**

```typescript
// Conflict resolution logic
if (localRecord.updatedAt > remoteRecord.updatedAt) {
  // Local is newer - will be pushed to server
  // Server decides final outcome
} else {
  // Remote is newer - accept server version
  applyRemoteChanges(remoteRecord);
}
```

**Special Cases:**

| Conflict Type | Resolution Strategy |
|---------------|---------------------|
| Schedule Assignment | Server wins (ACGME compliance validated server-side) |
| Swap Request | Server wins (business logic complex) |
| User Preferences | Last-write-wins (safe, user-specific) |
| Leave Request | Server wins (requires approval workflow) |

#### Background Sync Implementation

```typescript
import * as BackgroundFetch from 'expo-background-fetch';
import * as TaskManager from 'expo-task-manager';

const BACKGROUND_SYNC_TASK = 'background-sync';

TaskManager.defineTask(BACKGROUND_SYNC_TASK, async () => {
  try {
    await syncManager.pushChanges();
    await syncManager.pullChanges();
    return BackgroundFetch.BackgroundFetchResult.NewData;
  } catch (error) {
    logError('Background sync failed', error);
    return BackgroundFetch.BackgroundFetchResult.Failed;
  }
});

await BackgroundFetch.registerTaskAsync(BACKGROUND_SYNC_TASK, {
  minimumInterval: 15 * 60, // 15 minutes
  stopOnTerminate: false,
  startOnBoot: true,
});
```

### Data Storage Size Estimates

| Data Type | Records/Year | Storage/Record | Total |
|-----------|--------------|----------------|-------|
| Assignments | 50,000 | 500 bytes | 25 MB |
| Persons | 500 | 2 KB | 1 MB |
| Swaps | 2,000 | 1 KB | 2 MB |
| Blocks | 730 | 300 bytes | 219 KB |
| **Total** | | | **~30 MB/year** |

WatermelonDB easily handles this scale with instant query performance.

---

## 3. Push Notifications

### Strategy: Expo Notifications + Firebase Cloud Messaging (FCM)

#### Hybrid Approach

**Development & Testing:**
- Use Expo Push Notification service for rapid prototyping
- No FCM setup needed during early development
- Works seamlessly with Expo Go

**Production:**
- Migrate to FCM for reliability and enterprise features
- Free tier with generous limits (no cost concern)
- Direct control over delivery infrastructure

#### Notification Categories

Healthcare-specific notification types:

| Category | Priority | Use Case | Example |
|----------|----------|----------|---------|
| **Emergency** | Critical | Staff shortages, emergencies | "URGENT: Coverage needed in ER - 2 residents called out" |
| **Schedule Changes** | High | Swap approvals, assignments | "Your swap request has been approved" |
| **Reminders** | Medium | Upcoming shifts, deadlines | "Your shift starts in 2 hours" |
| **Administrative** | Low | System updates, announcements | "New training module available" |

#### Implementation

```typescript
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';

// Configure notification behavior
Notifications.setNotificationHandler({
  handleNotification: async (notification) => {
    const category = notification.request.content.data?.category;

    return {
      shouldShowAlert: true,
      shouldPlaySound: category === 'emergency',
      shouldSetBadge: true,
      priority: category === 'emergency'
        ? Notifications.AndroidNotificationPriority.MAX
        : Notifications.AndroidNotificationPriority.DEFAULT,
    };
  },
});

// Register for push notifications
async function registerForPushNotifications() {
  if (!Device.isDevice) {
    throw new Error('Push notifications only work on physical devices');
  }

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') {
    throw new Error('Permission denied for push notifications');
  }

  const token = await Notifications.getExpoPushTokenAsync({
    projectId: Constants.expoConfig?.extra?.eas?.projectId,
  });

  // Send token to backend for storage
  await api.registerPushToken(token.data);

  return token;
}
```

#### Notification Actions

**Interactive Notifications:**

```typescript
await Notifications.setNotificationCategoryAsync('swap-request', [
  {
    identifier: 'approve',
    buttonTitle: 'Approve',
    options: {
      opensAppToForeground: false,
    },
  },
  {
    identifier: 'reject',
    buttonTitle: 'Reject',
    options: {
      opensAppToForeground: false,
      isDestructive: true,
    },
  },
  {
    identifier: 'view',
    buttonTitle: 'View Details',
    options: {
      opensAppToForeground: true,
    },
  },
]);
```

#### Backend Integration

**Push Endpoint** (backend sends to FCM):

```python
from firebase_admin import messaging

async def send_emergency_notification(user_ids: list[str], message: str):
    """Send critical notification to multiple users."""

    # Get FCM tokens from database
    tokens = await get_fcm_tokens(user_ids)

    notification = messaging.MulticastMessage(
        notification=messaging.Notification(
            title="EMERGENCY",
            body=message,
        ),
        data={
            "category": "emergency",
            "timestamp": datetime.utcnow().isoformat(),
        },
        android=messaging.AndroidConfig(
            priority="high",
            notification=messaging.AndroidNotification(
                sound="default",
                priority="max",
            ),
        ),
        apns=messaging.APNSConfig(
            headers={
                "apns-priority": "10",
            },
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    sound="default",
                    badge=1,
                ),
            ),
        ),
        tokens=tokens,
    )

    response = await messaging.send_multicast(notification)
    logger.info(f"Sent emergency notification: {response.success_count} successful")
```

#### Cost Analysis

| Service | Free Tier | Cost Beyond | Recommendation |
|---------|-----------|-------------|----------------|
| **Expo Push** | Unlimited | Free | ✅ Development |
| **FCM** | Unlimited | Free | ✅ Production |
| **OneSignal** | 10k subscribers | $9/month | ⚠️ If needed for analytics |
| **Airship** | No free tier | Enterprise pricing | ❌ Overkill |

**Verdict:** FCM for production (free, reliable, enterprise-grade)

---

## 4. Authentication & Security

### Healthcare Security Requirements

As a **HIPAA-compliant** application, we must implement:

1. **Strong Authentication**: Multi-factor preferred
2. **Secure Token Storage**: No plaintext credentials on device
3. **Biometric Support**: Face ID, Touch ID, fingerprint
4. **Session Management**: Automatic timeout, refresh tokens
5. **Audit Logging**: All authentication events logged server-side

### Biometric Authentication

#### Library: `expo-local-authentication`

**Why:**
- Cross-platform API (iOS Face ID/Touch ID, Android fingerprint/face)
- Hardware-backed security (Secure Enclave on iOS, KeyStore on Android)
- No biometric data ever exposed to app or uploaded
- Well-maintained by Expo team

#### Implementation

```typescript
import * as LocalAuthentication from 'expo-local-authentication';

class BiometricAuth {
  async isAvailable(): Promise<boolean> {
    const hasHardware = await LocalAuthentication.hasHardwareAsync();
    const isEnrolled = await LocalAuthentication.isEnrolledAsync();
    return hasHardware && isEnrolled;
  }

  async getSupportedTypes(): Promise<string[]> {
    const types = await LocalAuthentication.supportedAuthenticationTypesAsync();
    return types.map(type =>
      LocalAuthentication.AuthenticationType[type]
    );
  }

  async authenticate(reason: string): Promise<boolean> {
    const result = await LocalAuthentication.authenticateAsync({
      promptMessage: reason,
      fallbackLabel: 'Use passcode',
      disableDeviceFallback: false, // Allow PIN/password fallback
      cancelLabel: 'Cancel',
    });

    return result.success;
  }
}
```

### Secure Token Storage: `expo-secure-store`

**Critical:** Never store JWT tokens in AsyncStorage (not encrypted)

```typescript
import * as SecureStore from 'expo-secure-store';

class TokenManager {
  private readonly ACCESS_TOKEN_KEY = 'auth_access_token';
  private readonly REFRESH_TOKEN_KEY = 'auth_refresh_token';

  async saveTokens(accessToken: string, refreshToken: string) {
    await Promise.all([
      SecureStore.setItemAsync(this.ACCESS_TOKEN_KEY, accessToken, {
        keychainAccessible: SecureStore.WHEN_UNLOCKED,
      }),
      SecureStore.setItemAsync(this.REFRESH_TOKEN_KEY, refreshToken, {
        keychainAccessible: SecureStore.WHEN_UNLOCKED,
      }),
    ]);
  }

  async getAccessToken(): Promise<string | null> {
    return await SecureStore.getItemAsync(this.ACCESS_TOKEN_KEY);
  }

  async getRefreshToken(): Promise<string | null> {
    return await SecureStore.getItemAsync(this.REFRESH_TOKEN_KEY);
  }

  async clearTokens() {
    await Promise.all([
      SecureStore.deleteItemAsync(this.ACCESS_TOKEN_KEY),
      SecureStore.deleteItemAsync(this.REFRESH_TOKEN_KEY),
    ]);
  }
}
```

**Security Features:**

- **iOS**: Uses Keychain Services (hardware-backed Secure Enclave when available)
- **Android**: Uses EncryptedSharedPreferences backed by Keystore
- **Encryption**: AES-256 encryption at rest
- **Access Control**: Only unlocked device can access (configurable)

### Authentication Flow

```
┌─────────────────────────────────────────────────┐
│             Login Screen                         │
│  - Email + Password                              │
│  - Biometric option (if enrolled)                │
└─────────────────┬───────────────────────────────┘
                  │
    ┌─────────────▼──────────────┐
    │   Biometric Auth?          │
    └──┬──────────────────────┬──┘
       │ Yes                  │ No
       │                      │
┌──────▼─────────┐    ┌──────▼──────────┐
│ expo-local-    │    │ Password Auth   │
│ authentication │    │ (Server)        │
└──────┬─────────┘    └──────┬──────────┘
       │                     │
       │  ┌──────────────────┘
       │  │
       ▼  ▼
┌──────────────────────┐
│  Cryptographic Key   │
│  (stored in Keychain)│
└──────┬───────────────┘
       │
       │ Sign challenge
       │
       ▼
┌──────────────────────┐
│  Server Validates    │
│  Signature           │
└──────┬───────────────┘
       │
       │ Issues JWT
       │
       ▼
┌──────────────────────┐
│  expo-secure-store   │
│  Save tokens         │
└──────────────────────┘
```

### Best Practices Implementation

#### 1. Cryptographic Biometric Auth (Most Secure)

```typescript
import * as Crypto from 'expo-crypto';

// On enrollment, generate key pair
const keyPair = await Crypto.generateKeyPairAsync({
  algorithm: 'rsa',
  modulusLength: 2048,
});

// Store private key in secure hardware
await SecureStore.setItemAsync('biometric_private_key', keyPair.privateKey, {
  requireAuthentication: true, // Require biometric for access
  keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
});

// Send public key to server
await api.registerBiometricKey(keyPair.publicKey);

// On subsequent logins:
async function biometricLogin() {
  // Get challenge from server
  const { challenge } = await api.getBiometricChallenge();

  // Trigger biometric auth to access private key
  const authenticated = await LocalAuthentication.authenticateAsync({
    promptMessage: 'Authenticate to sign in',
  });

  if (!authenticated.success) throw new Error('Biometric auth failed');

  // Retrieve private key (only accessible after biometric auth)
  const privateKey = await SecureStore.getItemAsync('biometric_private_key');

  // Sign challenge
  const signature = await Crypto.digestStringAsync(
    Crypto.CryptoDigestAlgorithm.SHA256,
    challenge + privateKey
  );

  // Send signature to server for validation
  const { accessToken, refreshToken } = await api.verifyBiometricSignature(signature);

  await tokenManager.saveTokens(accessToken, refreshToken);
}
```

#### 2. Session Management

```typescript
class SessionManager {
  private readonly IDLE_TIMEOUT = 15 * 60 * 1000; // 15 minutes
  private lastActivity: number = Date.now();
  private timeoutId?: NodeJS.Timeout;

  constructor() {
    this.setupActivityTracking();
    this.startIdleTimer();
  }

  private setupActivityTracking() {
    // Track user interactions
    const events = ['touchstart', 'scroll', 'keydown'];
    events.forEach(event => {
      document.addEventListener(event, () => {
        this.updateActivity();
      });
    });
  }

  private updateActivity() {
    this.lastActivity = Date.now();
    this.resetIdleTimer();
  }

  private startIdleTimer() {
    this.timeoutId = setTimeout(() => {
      this.handleTimeout();
    }, this.IDLE_TIMEOUT);
  }

  private resetIdleTimer() {
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
    }
    this.startIdleTimer();
  }

  private async handleTimeout() {
    // Require re-authentication
    await this.lockSession();

    // Navigate to lock screen
    navigation.navigate('BiometricLock');
  }

  private async lockSession() {
    // Don't clear tokens, just require biometric re-auth
    await AsyncStorage.setItem('session_locked', 'true');
  }
}
```

#### 3. Security Checklist

- ✅ **Tokens in Secure Storage**: expo-secure-store (hardware-backed)
- ✅ **Biometric Fallback**: Always allow PIN/password
- ✅ **Session Timeout**: 15-minute idle timeout
- ✅ **Network Security**: Certificate pinning (for production)
- ✅ **Code Obfuscation**: Minification + Hermes bytecode
- ✅ **Root Detection**: Alert if device is jailbroken/rooted
- ✅ **No PHI Logging**: Sanitize all logs
- ✅ **TLS 1.3**: Enforce modern encryption

---

## 5. Architecture Patterns

### State Management: Zustand + TanStack Query

#### Why This Combination?

**TanStack Query (React Query)** for **server state**:
- Automatic caching, refetching, and synchronization
- Handles loading/error states
- Optimistic updates
- Request deduplication
- Offline support via persistence

**Zustand** for **local/UI state**:
- Lightweight (~1KB)
- No boilerplate
- No context providers needed
- Excellent performance (minimal re-renders)
- Simple API (literally 2 lines to get started)

#### Implementation Examples

**Server State (TanStack Query):**

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Fetch user's schedule
export function useSchedule(personId: string) {
  return useQuery({
    queryKey: ['schedule', personId],
    queryFn: () => api.getSchedule(personId),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes (formerly cacheTime)
    retry: 3,
    // Offline support
    networkMode: 'offlineFirst', // Try cache first, then network
  });
}

// Request swap
export function useSwapRequest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (swap: SwapRequest) => api.requestSwap(swap),
    // Optimistic update
    onMutate: async (newSwap) => {
      await queryClient.cancelQueries({ queryKey: ['swaps'] });

      const previousSwaps = queryClient.getQueryData(['swaps']);

      queryClient.setQueryData(['swaps'], (old: any) =>
        [...old, { ...newSwap, status: 'pending' }]
      );

      return { previousSwaps };
    },
    // Rollback on error
    onError: (err, newSwap, context) => {
      queryClient.setQueryData(['swaps'], context.previousSwaps);
    },
    // Refetch on success
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['swaps'] });
    },
  });
}
```

**Local State (Zustand):**

```typescript
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface AppState {
  // UI state
  selectedDate: Date;
  filterRole: string | null;
  notificationsEnabled: boolean;

  // Actions
  setSelectedDate: (date: Date) => void;
  setFilterRole: (role: string | null) => void;
  toggleNotifications: () => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      // Initial state
      selectedDate: new Date(),
      filterRole: null,
      notificationsEnabled: true,

      // Actions
      setSelectedDate: (date) => set({ selectedDate: date }),
      setFilterRole: (role) => set({ filterRole: role }),
      toggleNotifications: () =>
        set((state) => ({ notificationsEnabled: !state.notificationsEnabled })),
    }),
    {
      name: 'app-storage',
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);

// Usage in component (super simple!)
function ScheduleScreen() {
  const selectedDate = useAppStore((state) => state.selectedDate);
  const setSelectedDate = useAppStore((state) => state.setSelectedDate);

  return (
    <DatePicker value={selectedDate} onChange={setSelectedDate} />
  );
}
```

### Navigation: React Navigation v6

#### Structure

```typescript
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';

// Type-safe navigation
export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
  SwapDetails: { swapId: string };
  ScheduleView: { personId: string; date: string };
};

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator();

function MainTabs() {
  return (
    <Tab.Navigator>
      <Tab.Screen name="Schedule" component={ScheduleScreen} />
      <Tab.Screen name="Swaps" component={SwapsScreen} />
      <Tab.Screen name="Coverage" component={CoverageScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}

function RootNavigator() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {!isAuthenticated ? (
          <Stack.Screen name="Auth" component={AuthScreen} />
        ) : (
          <>
            <Stack.Screen name="Main" component={MainTabs} />
            <Stack.Screen
              name="SwapDetails"
              component={SwapDetailsScreen}
              options={{ presentation: 'modal' }}
            />
            <Stack.Screen
              name="ScheduleView"
              component={ScheduleViewScreen}
            />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
```

### Component Structure

**Atomic Design Pattern:**

```
src/
├── components/
│   ├── atoms/              # Basic building blocks
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Badge.tsx
│   │   └── Spinner.tsx
│   ├── molecules/          # Simple composites
│   │   ├── SwapCard.tsx
│   │   ├── ScheduleBlock.tsx
│   │   └── NotificationItem.tsx
│   ├── organisms/          # Complex composites
│   │   ├── SwapList.tsx
│   │   ├── ScheduleCalendar.tsx
│   │   └── CoverageDashboard.tsx
│   └── templates/          # Page layouts
│       ├── AuthTemplate.tsx
│       └── MainTemplate.tsx
├── screens/                # Full pages
│   ├── ScheduleScreen.tsx
│   ├── SwapsScreen.tsx
│   └── ProfileScreen.tsx
├── hooks/                  # Custom hooks
│   ├── useSchedule.ts
│   ├── useSwaps.ts
│   └── useAuth.ts
├── services/               # API clients
│   ├── api.ts
│   ├── sync.ts
│   └── notifications.ts
├── stores/                 # Zustand stores
│   ├── authStore.ts
│   └── appStore.ts
└── utils/                  # Helpers
    ├── date.ts
    ├── formatting.ts
    └── validation.ts
```

---

## 6. Development Considerations

### Development Workflow

#### Local Development Setup

```bash
# Install Expo CLI
npm install -g expo-cli eas-cli

# Create new project
npx create-expo-app residency-scheduler-mobile --template blank-typescript

# Install dependencies
cd residency-scheduler-mobile
npm install @tanstack/react-query zustand expo-local-authentication \
  expo-secure-store expo-notifications @react-navigation/native \
  @watermelondb/react-native

# Start development server
npx expo start

# Options:
# - Press 'i' for iOS simulator
# - Press 'a' for Android emulator
# - Scan QR code with Expo Go app on physical device
```

#### Hot Reload

Expo provides **Fast Refresh**:
- Edit code → See changes in <2 seconds
- Preserves component state during edits
- Works on device and simulator simultaneously

#### Environment Configuration

```typescript
// app.config.ts
export default {
  expo: {
    name: "Residency Scheduler",
    slug: "residency-scheduler",
    version: "1.0.0",
    orientation: "portrait",
    icon: "./assets/icon.png",
    userInterfaceStyle: "automatic",
    splash: {
      image: "./assets/splash.png",
      resizeMode: "contain",
      backgroundColor: "#ffffff"
    },
    assetBundlePatterns: ["**/*"],
    ios: {
      supportsTablet: true,
      bundleIdentifier: "com.hospital.residencyscheduler",
      infoPlist: {
        NSFaceIDUsageDescription: "Use Face ID to securely access your schedule"
      }
    },
    android: {
      adaptiveIcon: {
        foregroundImage: "./assets/adaptive-icon.png",
        backgroundColor: "#ffffff"
      },
      package: "com.hospital.residencyscheduler",
      permissions: [
        "USE_BIOMETRIC",
        "USE_FINGERPRINT",
        "RECEIVE_BOOT_COMPLETED"
      ]
    },
    extra: {
      apiUrl: process.env.API_URL || "https://api.residency-scheduler.com",
      eas: {
        projectId: "your-project-id"
      }
    },
    plugins: [
      "expo-secure-store",
      "expo-local-authentication",
      [
        "expo-notifications",
        {
          icon: "./assets/notification-icon.png",
          color: "#ffffff"
        }
      ]
    ]
  }
};
```

### Testing Strategy

#### Unit Tests (Jest + React Native Testing Library)

```typescript
import { render, screen, fireEvent } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SwapCard } from '../components/SwapCard';

describe('SwapCard', () => {
  it('displays swap details correctly', () => {
    const swap = {
      id: '123',
      requestorName: 'Dr. Smith',
      date: '2025-12-20',
      status: 'pending',
    };

    render(
      <QueryClientProvider client={new QueryClient()}>
        <SwapCard swap={swap} />
      </QueryClientProvider>
    );

    expect(screen.getByText('Dr. Smith')).toBeTruthy();
    expect(screen.getByText('pending')).toBeTruthy();
  });

  it('calls onApprove when approve button pressed', () => {
    const onApprove = jest.fn();
    const swap = { id: '123', status: 'pending' };

    render(<SwapCard swap={swap} onApprove={onApprove} />);

    fireEvent.press(screen.getByText('Approve'));

    expect(onApprove).toHaveBeenCalledWith('123');
  });
});
```

#### E2E Tests (Detox or Maestro)

**Maestro** (simpler, recommended):

```yaml
# .maestro/swap_flow.yaml
appId: com.hospital.residencyscheduler
---
- launchApp
- tapOn: "Swaps"
- assertVisible: "Swap Requests"
- tapOn: "Request Swap"
- inputText: "Select date"
  text: "2025-12-20"
- tapOn: "Submit"
- assertVisible: "Swap requested successfully"
```

Run tests:
```bash
maestro test .maestro/swap_flow.yaml
```

#### Test Coverage Goals

| Layer | Coverage Target | Priority |
|-------|----------------|----------|
| **Utils/Helpers** | 90%+ | High |
| **Hooks** | 80%+ | High |
| **Components** | 70%+ | Medium |
| **Screens** | 50%+ (E2E) | Medium |

### CI/CD with EAS Build

#### Setup

```bash
# Initialize EAS
eas init

# Configure build profiles
eas build:configure
```

**eas.json:**

```json
{
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "ios": {
        "resourceClass": "m-medium"
      }
    },
    "preview": {
      "distribution": "internal",
      "ios": {
        "simulator": true
      }
    },
    "production": {
      "autoIncrement": true,
      "env": {
        "API_URL": "https://api.residency-scheduler.com"
      }
    }
  },
  "submit": {
    "production": {
      "ios": {
        "appleId": "admin@hospital.com",
        "ascAppId": "1234567890",
        "appleTeamId": "ABCD123456"
      },
      "android": {
        "serviceAccountKeyPath": "./service-account-key.json",
        "track": "production"
      }
    }
  }
}
```

#### GitHub Actions Workflow

```yaml
# .github/workflows/eas-build.yml
name: EAS Build

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18
          cache: npm

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test -- --coverage

      - name: Type check
        run: npm run type-check

      - name: Lint
        run: npm run lint

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Setup Expo
        uses: expo/expo-github-action@v8
        with:
          expo-version: latest
          eas-version: latest
          token: ${{ secrets.EXPO_TOKEN }}

      - name: Install dependencies
        run: npm ci

      - name: Build iOS
        run: eas build --platform ios --non-interactive --no-wait

      - name: Build Android
        run: eas build --platform android --non-interactive --no-wait
```

#### OTA Updates (Expo Updates)

```bash
# Deploy update to production
eas update --branch production --message "Fix swap approval bug"

# Deploy to specific channel
eas update --channel preview --message "Test new feature"

# View update history
eas update:list
```

**Rollback capability:**

```bash
# Rollback to previous update
eas update:rollback --branch production
```

### Performance Optimization

#### Bundle Size

```bash
# Analyze bundle
npx expo-bundle-analyzer

# Techniques:
# - Use Hermes engine (enabled by default)
# - Import only needed components: import { Button } from 'package/Button'
# - Lazy load screens: const Screen = lazy(() => import('./Screen'))
```

#### Image Optimization

```typescript
import { Image } from 'expo-image';

// Use expo-image (faster, better caching)
<Image
  source={{ uri: avatarUrl }}
  placeholder={blurhash}
  contentFit="cover"
  transition={200}
  cachePolicy="memory-disk"
/>
```

#### List Performance

```typescript
import { FlashList } from '@shopify/flash-list';

// Use FlashList instead of FlatList (60 FPS even with 1000s of items)
<FlashList
  data={assignments}
  renderItem={({ item }) => <AssignmentRow assignment={item} />}
  estimatedItemSize={80}
  keyExtractor={(item) => item.id}
/>
```

---

## 7. Technology Stack Recommendation

### Final Technology Stack

| Category | Technology | Version | Rationale |
|----------|-----------|---------|-----------|
| **Framework** | Expo (Managed Workflow) | SDK 51+ | Fast development, easy maintenance, sufficient customization |
| **Language** | TypeScript | 5.0+ | Type safety, better developer experience |
| **UI Library** | React Native | 0.73+ | Industry standard, managed by Expo |
| **Local Database** | WatermelonDB | 0.27+ | High performance, reactive, offline-first |
| **Server State** | TanStack Query | 5.17+ | Best-in-class data fetching and caching |
| **Local State** | Zustand | 4.5+ | Lightweight, simple, performant |
| **Navigation** | React Navigation | 6.x | De facto standard, excellent TypeScript support |
| **Forms** | React Hook Form | 7.50+ | Performant, good validation support |
| **Validation** | Zod | 3.22+ | TypeScript-first schema validation |
| **Styling** | NativeWind (Tailwind) | 4.0+ | Utility-first, matches web frontend |
| **HTTP Client** | Axios | 1.6+ | Interceptors for auth, error handling |
| **Push Notifications** | Expo Notifications + FCM | Latest | Easy setup, enterprise-ready |
| **Biometrics** | expo-local-authentication | Latest | Cross-platform biometric support |
| **Secure Storage** | expo-secure-store | Latest | Hardware-backed encryption |
| **Background Tasks** | expo-background-fetch | Latest | Sync data while app backgrounded |
| **Testing (Unit)** | Jest + RNTL | Latest | Standard for React Native |
| **Testing (E2E)** | Maestro | Latest | Simpler than Detox, reliable |
| **CI/CD** | EAS Build + GitHub Actions | Latest | Expo-native, cloud builds |
| **Error Tracking** | Sentry | Latest | Best-in-class error monitoring |
| **Analytics** | Amplitude or Mixpanel | Latest | Product analytics for usage insights |

### Package.json (Core Dependencies)

```json
{
  "name": "residency-scheduler-mobile",
  "version": "1.0.0",
  "main": "expo/AppEntry.js",
  "scripts": {
    "start": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios",
    "web": "expo start --web",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "type-check": "tsc --noEmit",
    "lint": "eslint . --ext .ts,.tsx",
    "lint:fix": "eslint . --ext .ts,.tsx --fix"
  },
  "dependencies": {
    "expo": "~51.0.0",
    "expo-status-bar": "~1.12.0",
    "react": "18.2.0",
    "react-native": "0.74.0",

    "@tanstack/react-query": "^5.17.0",
    "zustand": "^4.5.0",

    "@react-navigation/native": "^6.1.9",
    "@react-navigation/native-stack": "^6.9.17",
    "@react-navigation/bottom-tabs": "^6.5.11",

    "@nozbe/watermelondb": "^0.27.0",
    "@nozbe/with-observables": "^1.6.0",

    "expo-local-authentication": "~14.0.0",
    "expo-secure-store": "~13.0.0",
    "expo-notifications": "~0.28.0",
    "expo-background-fetch": "~12.0.0",
    "expo-task-manager": "~11.8.0",
    "expo-image": "~1.12.0",

    "nativewind": "^4.0.0",
    "react-hook-form": "^7.50.0",
    "zod": "^3.22.0",
    "axios": "^1.6.0",
    "date-fns": "^3.0.0",

    "@shopify/flash-list": "^1.6.0"
  },
  "devDependencies": {
    "@babel/core": "^7.24.0",
    "@types/react": "~18.2.0",
    "@types/jest": "^29.5.0",
    "typescript": "~5.3.0",

    "jest": "^29.7.0",
    "jest-expo": "~51.0.0",
    "@testing-library/react-native": "^12.4.0",
    "@testing-library/jest-native": "^5.4.0",

    "eslint": "^8.57.0",
    "eslint-config-expo": "^7.0.0",
    "prettier": "^3.2.0"
  }
}
```

---

## 8. Implementation Timeline

### Phase 1: Foundation (Weeks 1-2)

**Goal:** Set up project infrastructure and core architecture

| Task | Effort | Dependencies |
|------|--------|--------------|
| Initialize Expo project | 1 day | - |
| Configure TypeScript, ESLint, Prettier | 0.5 day | - |
| Set up React Navigation structure | 1 day | - |
| Implement authentication flow (JWT) | 2 days | Backend API |
| Integrate expo-secure-store for tokens | 1 day | Auth flow |
| Set up TanStack Query and Zustand | 1 day | - |
| Configure EAS Build and GitHub Actions | 1 day | - |
| Basic UI components (atoms/molecules) | 3 days | - |

**Deliverable:** Working app skeleton with auth, navigation, and build pipeline

### Phase 2: Core Features (Weeks 3-5)

**Goal:** Implement primary user-facing features

| Task | Effort | Dependencies |
|------|--------|--------------|
| Schedule view screen | 3 days | Backend schedule API |
| WatermelonDB setup and schema | 2 days | - |
| Offline sync implementation | 4 days | WatermelonDB, backend sync API |
| Swap request flow | 3 days | Backend swap API |
| Swap approval/rejection | 2 days | Swap request flow |
| Coverage dashboard | 2 days | Backend coverage API |
| Profile and settings | 1 day | - |

**Deliverable:** Functional app with schedule viewing, swap management, offline support

### Phase 3: Advanced Features (Weeks 6-7)

**Goal:** Add security, notifications, and polish

| Task | Effort | Dependencies |
|------|--------|--------------|
| Biometric authentication | 2 days | Auth flow |
| Push notifications (FCM) | 3 days | Backend notification system |
| Background sync | 2 days | Offline sync |
| Notification handling (foreground/background) | 2 days | Push notifications |
| ACGME compliance indicators | 2 days | Backend compliance data |
| Emergency alerts | 1 day | Push notifications |

**Deliverable:** Production-ready app with all security and notification features

### Phase 4: Testing & Polish (Weeks 8-9)

**Goal:** Ensure quality and reliability

| Task | Effort | Dependencies |
|------|--------|--------------|
| Unit tests (80% coverage) | 4 days | All features |
| E2E tests (Maestro) | 3 days | All features |
| Performance optimization | 2 days | - |
| Accessibility audit (screen readers) | 2 days | - |
| Security audit | 1 day | - |
| Beta testing with users | 5 days | All features |

**Deliverable:** Tested, polished app ready for app store submission

### Phase 5: Deployment (Week 10)

**Goal:** Launch to app stores

| Task | Effort | Dependencies |
|------|--------|--------------|
| App Store submission (iOS) | 2 days | Testing complete |
| Google Play submission (Android) | 1 day | Testing complete |
| OTA update infrastructure | 1 day | EAS Updates |
| Documentation and training | 1 day | - |
| Monitoring setup (Sentry, analytics) | 1 day | - |

**Deliverable:** Live apps on App Store and Google Play

### Total Timeline: 10 Weeks (2.5 Months)

**Team Size Assumptions:**
- 2 mobile developers (full-time)
- 1 backend developer (part-time, for API support)
- 1 QA engineer (weeks 8-10)

**Risk Factors:**

| Risk | Mitigation |
|------|------------|
| Backend API delays | Start with mock data, swap in real API later |
| Biometric testing complexity | Test on multiple physical devices early |
| App store approval delays | Submit for review early, iterate quickly |
| Offline sync edge cases | Extensive testing, conservative conflict resolution |

### Milestones

- **Week 2:** Demo-able authentication and navigation
- **Week 5:** Beta release to internal testers
- **Week 7:** Feature-complete for external beta
- **Week 9:** Release candidate ready
- **Week 10:** Public launch

---

## 9. Additional Considerations

### Accessibility

**WCAG 2.1 AA Compliance:**

```typescript
// Use accessible components
<Button
  accessibilityLabel="Approve swap request from Dr. Smith"
  accessibilityRole="button"
  accessibilityState={{ disabled: isLoading }}
>
  Approve
</Button>

// Screen reader support
<View accessibilityRole="header">
  <Text>Schedule for December 20, 2025</Text>
</View>

// Minimum touch target sizes (48x48dp)
const styles = StyleSheet.create({
  button: {
    minWidth: 48,
    minHeight: 48,
  },
});
```

### Internationalization (Future)

```typescript
import { I18n } from 'i18n-js';
import * as Localization from 'expo-localization';

const i18n = new I18n({
  en: { welcome: 'Welcome to Residency Scheduler' },
  es: { welcome: 'Bienvenido a Residency Scheduler' },
});

i18n.locale = Localization.locale;
i18n.enableFallback = true;
```

### Analytics Events

```typescript
// Track key user actions
analytics.track('swap_requested', {
  swapId: swap.id,
  date: swap.date,
  userRole: user.role,
});

analytics.track('schedule_viewed', {
  date: selectedDate,
  filterApplied: filterRole !== null,
});

analytics.track('notification_opened', {
  category: notification.data.category,
  actionTaken: action,
});
```

### Error Monitoring (Sentry)

```typescript
import * as Sentry from '@sentry/react-native';

Sentry.init({
  dsn: 'https://your-sentry-dsn',
  enableAutoSessionTracking: true,
  sessionTrackingIntervalMillis: 10000,
  // Don't send PHI to Sentry
  beforeSend(event) {
    // Sanitize event data
    return sanitizePHI(event);
  },
});

// Capture errors with context
try {
  await api.requestSwap(swap);
} catch (error) {
  Sentry.captureException(error, {
    tags: {
      feature: 'swap-request',
      userId: user.id,
    },
    level: 'error',
  });
  throw error;
}
```

---

## 10. Sources & References

### Research Sources

**Technology Decisions:**
- [React Native + Expo vs Bare Workflow: Which Should You Choose?](https://dev.to/lucas_wade_0596/react-native-expo-vs-bare-workflow-which-should-you-choose-47lo)
- [Should I Use Expo for React Native in 2025?](https://scriptide.tech/blog/should-you-use-expo-for-react-native)
- [Expo vs React Native: Key Differences, Pros & Cons (2025 Guide)](https://www.utilities-online.info/blogs/expo-vs-react-native)

**Offline-First Architecture:**
- [Offline-first React Native Apps with Expo, WatermelonDB, and Supabase](https://supabase.com/blog/react-native-offline-first-watermelon-db)
- [Advanced React Native in 2025: Building Completely Offline-Ready Apps](https://medium.com/@theNewGenCoder/advanced-react-native-in-2025-building-completely-offline-ready-apps-with-seamless-sync-and-32b0569711d5)
- [GitHub - Nozbe/WatermelonDB](https://github.com/Nozbe/WatermelonDB)
- [React Native Local Database Options: A Comprehensive Summary](https://www.powersync.com/blog/react-native-local-database-options)

**Push Notifications:**
- [Expo vs Firebase FCM: Push Notification Provider Comparison [2025]](https://www.courier.com/integrations/compare/expo-vs-firebase-fcm)
- [Expo push notifications: Overview - Expo Documentation](https://docs.expo.dev/push-notifications/overview/)
- [Top 5 Push Notification Services for Expo/React Native in 2025](https://pushbase.dev/blog/top-5-push-notification-services-for-expo-react-native-in-2025)

**Authentication & Security:**
- [Biometric Authentication in React Native: Face ID, Touch ID, and Fingerprint Explained](https://medium.com/@rohandhalpe05/boost-app-security-and-ux-secure-face-id-and-fingerprint-implementation-secrets-4ff6b93dc683)
- [Best Practice: Implementing Biometric Authentication in React Native](https://medium.com/@christosdemetriou93/best-practice-implementing-biometric-authentication-in-react-native-0e4a746543e6)
- [A closer look at the security of React Native biometric libraries](https://blog.nviso.eu/2021/04/06/a-closer-look-at-the-security-of-react-native-biometric-libraries/)

**State Management:**
- [React State Management in 2025: What You Actually Need](https://www.developerway.com/posts/react-state-management-2025)
- [State Management in 2025: Redux, Zustand, or React Query](https://www.linkedin.com/pulse/state-management-2025-redux-zustand-react-query-sbtqc)
- [Redux Toolkit vs React Query vs Zustand: Which One Should You Use in 2025?](https://medium.com/@vishalthakur2463/redux-toolkit-vs-react-query-vs-zustand-which-one-should-you-use-in-2025-048c1d3915f4)

**CI/CD:**
- [EAS Workflows: React Native CI/CD built for your app](https://expo.dev/blog/expo-workflows-automate-your-release-process)
- [EAS Build - Expo Documentation](https://docs.expo.dev/build/introduction/)
- [Best CI/CD tools for React Native - LogRocket Blog](https://blog.logrocket.com/best-ci-cd-tools-react-native/)
- [How to Implement CI/CD in React Native: Complete Guide for 2025](https://www.creolestudios.com/implement-ci-cd-in-react-native/)

### Official Documentation

- [Expo Documentation](https://docs.expo.dev/)
- [React Native Documentation](https://reactnative.dev/)
- [TanStack Query Documentation](https://tanstack.com/query/latest)
- [Zustand Documentation](https://github.com/pmndrs/zustand)
- [React Navigation Documentation](https://reactnavigation.org/)
- [WatermelonDB Documentation](https://watermelondb.dev/)

---

## Conclusion

The recommended **Expo Managed Workflow** with **WatermelonDB** for offline-first capabilities, **TanStack Query + Zustand** for state management, and **FCM** for push notifications provides a robust, secure, and maintainable foundation for the Residency Scheduler mobile app.

This architecture balances:
- **Developer productivity** (Expo's managed workflow)
- **Performance** (WatermelonDB, FlashList, Hermes)
- **Security** (hardware-backed biometrics, secure storage, HIPAA compliance)
- **Offline reliability** (local-first data, background sync)
- **Future scalability** (can move to bare workflow if needed)

**Timeline:** 10 weeks to production launch with a 2-developer team.

**Next Steps:**
1. Set up Expo project and development environment
2. Implement authentication and secure storage
3. Build offline sync with WatermelonDB
4. Iterate with internal beta testers
5. Launch to app stores

---

**Document Version:** 1.0
**Last Updated:** 2025-12-19
**Author:** Terminal 6 - Mobile App Architecture Research
