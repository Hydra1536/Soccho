const CACHE_NAME = 'soccho-shell-v1';
const API_CACHE = 'soccho-api-v1';
const TTL_MS = 5 * 60 * 1000;
const DB_NAME = 'soccho-offline';
const STORE = 'tx-queue';

self.addEventListener('install', (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE_NAME);
      try {
        const appShell = await fetch('/', { cache: 'no-cache' });
        if (!appShell.ok) {
          return;
        }
        await cache.put('/', appShell.clone());
        await cache.put('/home', appShell.clone());
      } catch {
        // Do not fail the service worker install when the shell cannot be prefetched.
      }
    })()
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

function openDb() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: 'id', autoIncrement: true });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function enqueueTransaction(item) {
  const db = await openDb();
  const tx = db.transaction(STORE, 'readwrite');
  tx.objectStore(STORE).add({ ...item, createdAt: Date.now() });
  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve(true);
    tx.onerror = () => reject(tx.error);
  });
}

async function readQueued() {
  const db = await openDb();
  const tx = db.transaction(STORE, 'readonly');
  const req = tx.objectStore(STORE).getAll();
  return new Promise((resolve, reject) => {
    req.onsuccess = () => resolve(req.result || []);
    req.onerror = () => reject(req.error);
  });
}

async function clearQueued(ids) {
  const db = await openDb();
  const tx = db.transaction(STORE, 'readwrite');
  const store = tx.objectStore(STORE);
  ids.forEach((id) => store.delete(id));
  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve(true);
    tx.onerror = () => reject(tx.error);
  });
}

async function cacheWithTtl(request, response) {
  const cache = await caches.open(API_CACHE);
  const headers = new Headers(response.headers);
  headers.set('x-cached-at', String(Date.now()));
  const wrapped = new Response(await response.clone().blob(), {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
  await cache.put(request, wrapped);
}

async function getFreshCached(request) {
  const cache = await caches.open(API_CACHE);
  const cached = await cache.match(request);
  if (!cached) return null;
  const created = Number(cached.headers.get('x-cached-at') || '0');
  if (!created || Date.now() - created > TTL_MS) {
    await cache.delete(request);
    return null;
  }
  return cached;
}

function shouldCacheGraphqlPayload(payload) {
  const operationName = String(payload?.operationName || '');
  const query = String(payload?.query || '');
  if (operationName === 'GetFriends' || operationName === 'FriendLedger') {
    return true;
  }
  return query.includes('friendList') || query.includes('friendLedger');
}

function graphqlCacheKey(url, payload) {
  const operationName = encodeURIComponent(String(payload?.operationName || 'anonymous'));
  const variables = encodeURIComponent(JSON.stringify(payload?.variables || {}));
  return new Request(`${url.origin}/__graphql_cache__?op=${operationName}&vars=${variables}`);
}

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  if (req.method === 'GET' && url.pathname === '/home') {
    event.respondWith(
      (async () => {
        try {
          const network = await fetch(req);
          if (network.ok) await cacheWithTtl(req, network.clone());
          return network;
        } catch {
          const cached = await getFreshCached(req);
          if (cached) return cached;
          throw new Error('offline');
        }
      })()
    );
    return;
  }

  if (req.method === 'POST' && url.pathname.startsWith('/graphql/')) {
    event.respondWith(
      (async () => {
        let payload = null;
        try {
          payload = await req.clone().json();
        } catch {
          return fetch(req.clone());
        }

        if (!shouldCacheGraphqlPayload(payload)) {
          return fetch(req.clone());
        }

        const cacheKey = graphqlCacheKey(url, payload);

        try {
          const network = await fetch(req.clone());
          if (network.ok) await cacheWithTtl(cacheKey, network.clone());
          return network;
        } catch {
          const cached = await getFreshCached(cacheKey);
          if (cached) return cached;
          return new Response(JSON.stringify({ error: 'offline' }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' },
          });
        }
      })()
    );
    return;
  }

  if (req.method === 'POST' && url.pathname.startsWith('/api/transactions/')) {
    event.respondWith(
      (async () => {
        try {
          return await fetch(req.clone());
        } catch {
          const body = await req.clone().json();
          const authHeader = req.headers.get('Authorization');
          await enqueueTransaction({
            url: req.url,
            payload: body,
            authorization: authHeader || '',
          });
          if ('sync' in self.registration) {
            await self.registration.sync.register('sync-transactions');
          }
          return new Response(JSON.stringify({ queued: true }), {
            status: 202,
            headers: { 'Content-Type': 'application/json' },
          });
        }
      })()
    );
  }
});

self.addEventListener('sync', (event) => {
  if (event.tag !== 'sync-transactions') return;
  event.waitUntil(
    (async () => {
      const queued = await readQueued();
      const completed = [];
      for (const item of queued) {
        try {
          const headers = { 'Content-Type': 'application/json' };
          if (item.authorization) {
            headers.Authorization = item.authorization;
          }
          const res = await fetch(item.url || '/api/transactions/', {
            method: 'POST',
            headers,
            body: JSON.stringify(item.payload),
          });
          if (res.ok) completed.push(item.id);
        } catch {
          // keep for retry
        }
      }
      if (completed.length > 0) await clearQueued(completed);
    })()
  );
});
