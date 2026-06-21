const SHELL_CACHE = "soccho-shell-v5";
const DATA_CACHE = "soccho-data-v5";
const TTL_MS = 5 * 60 * 1000;
const DB_NAME = "soccho-offline";
const STORE = "tx-queue";
const APP_SHELL = ["/", "/index.html", "/manifest.webmanifest"];

self.addEventListener("install", (event) => {
	event.waitUntil(
		(async () => {
			const cache = await caches.open(SHELL_CACHE);
			await cache.addAll(APP_SHELL);
		})(),
	);
	self.skipWaiting();
});

self.addEventListener("activate", (event) => {
	event.waitUntil(
		(async () => {
			const names = await caches.keys();
			await Promise.all(
				names
					.filter((name) => ![SHELL_CACHE, DATA_CACHE].includes(name))
					.map((name) => caches.delete(name)),
			);
			await self.clients.claim();
		})(),
	);
});

function openDb() {
	return new Promise((resolve, reject) => {
		const req = indexedDB.open(DB_NAME, 1);
		req.onupgradeneeded = () => {
			const db = req.result;
			if (!db.objectStoreNames.contains(STORE)) {
				db.createObjectStore(STORE, { keyPath: "id", autoIncrement: true });
			}
		};
		req.onsuccess = () => resolve(req.result);
		req.onerror = () => reject(req.error);
	});
}

async function enqueueTransaction(item) {
	const db = await openDb();
	const tx = db.transaction(STORE, "readwrite");
	tx.objectStore(STORE).add({ ...item, createdAt: Date.now() });
	return new Promise((resolve, reject) => {
		tx.oncomplete = () => resolve(true);
		tx.onerror = () => reject(tx.error);
	});
}

async function readQueued() {
	const db = await openDb();
	const tx = db.transaction(STORE, "readonly");
	const req = tx.objectStore(STORE).getAll();
	return new Promise((resolve, reject) => {
		req.onsuccess = () => resolve(req.result || []);
		req.onerror = () => reject(req.error);
	});
}

async function clearQueued(ids) {
	const db = await openDb();
	const tx = db.transaction(STORE, "readwrite");
	const store = tx.objectStore(STORE);
	ids.forEach((id) => store.delete(id));
	return new Promise((resolve, reject) => {
		tx.oncomplete = () => resolve(true);
		tx.onerror = () => reject(tx.error);
	});
}

async function putDataCache(request, response) {
	const cache = await caches.open(DATA_CACHE);
	const headers = new Headers(response.headers);
	headers.set("x-cached-at", String(Date.now()));
	const wrapped = new Response(await response.clone().blob(), {
		status: response.status,
		statusText: response.statusText,
		headers,
	});
	await cache.put(request, wrapped);
}

async function getFreshCache(request) {
	const cache = await caches.open(DATA_CACHE);
	const cached = await cache.match(request);
	if (!cached) {
		return null;
	}
	const createdAt = Number(cached.headers.get("x-cached-at") || "0");
	if (!createdAt || Date.now() - createdAt > TTL_MS) {
		return null;
	}
	return cached;
}

function isNavigationRequest(request, url) {
	return (
		request.mode === "navigate" &&
		url.origin === self.location.origin &&
		!/\.[a-zA-Z0-9]+$/.test(url.pathname)
	);
}

function isStaticAsset(url) {
	return (
		url.origin === self.location.origin &&
		(url.pathname.startsWith("/assets/") ||
			url.pathname.endsWith(".css") ||
			url.pathname.endsWith(".js") ||
			url.pathname.endsWith(".woff2"))
	);
}

function isOfflineDataRequest(request, url) {
	if (request.method !== "GET") {
		return false;
	}
	return (
		url.pathname.includes("/api/auth/me/") ||
		url.pathname.includes("/api/social/list/") ||
		url.pathname.includes("/api/social/requests/") ||
		url.pathname.includes("/api/notification/list/") ||
		url.pathname.includes("/api/transactions/loyalty-score/")
	);
}

function shouldCacheGraphql(payload) {
	const operationName = String(payload?.operationName || "");
	const query = String(payload?.query || "");
	return (
		operationName === "GetFriends" ||
		operationName === "FriendLedger" ||
		operationName === "DashboardSummary" ||
		query.includes("friendLedger") ||
		query.includes("dashboardSummary")
	);
}

function graphqlCacheKey(url, payload) {
	return new Request(
		`${url.origin}/__graphql_cache__?op=${encodeURIComponent(String(payload?.operationName || "anonymous"))}&vars=${encodeURIComponent(JSON.stringify(payload?.variables || {}))}`,
	);
}

self.addEventListener("fetch", (event) => {
	const request = event.request;
	const url = new URL(request.url);

	if (isNavigationRequest(request, url)) {
		event.respondWith(
			(async () => {
				const cache = await caches.open(SHELL_CACHE);
				const cached = await cache.match("/index.html");
				try {
					const network = await fetch(request);
					if (network.ok) {
						return network;
					}
				} catch {
					if (cached) {
						return cached;
					}
				}
				return cached || fetch("/index.html");
			})(),
		);
		return;
	}

	if (isStaticAsset(url)) {
		event.respondWith(
			(async () => {
				const cache = await caches.open(SHELL_CACHE);
				const cached = await cache.match(request);
				if (cached) {
					return cached;
				}
				const network = await fetch(request);
				if (network.ok) {
					await cache.put(request, network.clone());
				}
				return network;
			})(),
		);
		return;
	}

	if (isOfflineDataRequest(request, url)) {
		event.respondWith(
			(async () => {
				const cached = await getFreshCache(request);
				const networkPromise = fetch(request)
					.then(async (response) => {
						if (response.ok) {
							await putDataCache(request, response.clone());
						}
						return response;
					})
					.catch(() => null);

				if (cached) {
					event.waitUntil(networkPromise);
					return cached;
				}

				const network = await networkPromise;
				if (network) {
					return network;
				}
				return new Response(JSON.stringify({ results: [], offline: true }), {
					status: 503,
					headers: { "Content-Type": "application/json" },
				});
			})(),
		);
		return;
	}

	if (request.method === "POST" && url.pathname.startsWith("/graphql/")) {
		event.respondWith(
			(async () => {
				let payload = null;
				try {
					payload = await request.clone().json();
				} catch {
					return fetch(request.clone());
				}

				if (!shouldCacheGraphql(payload)) {
					return fetch(request.clone());
				}

				const cacheKey = graphqlCacheKey(url, payload);
				try {
					const network = await fetch(request.clone());
					if (network.ok) {
						await putDataCache(cacheKey, network.clone());
					}
					return network;
				} catch {
					const cached = await getFreshCache(cacheKey);
					if (cached) {
						return cached;
					}
					return new Response(JSON.stringify({ error: "offline" }), {
						status: 503,
						headers: { "Content-Type": "application/json" },
					});
				}
			})(),
		);
		return;
	}

	if (
		request.method === "POST" &&
		url.pathname.startsWith("/api/transactions/")
	) {
		event.respondWith(
			(async () => {
				try {
					return await fetch(request.clone());
				} catch {
					const payload = await request.clone().json();
					await enqueueTransaction({
						url: request.url,
						payload,
						authorization: request.headers.get("Authorization") || "",
					});
					if ("sync" in self.registration) {
						await self.registration.sync.register("sync-transactions");
					}
					return new Response(JSON.stringify({ queued: true, offline: true }), {
						status: 202,
						headers: { "Content-Type": "application/json" },
					});
				}
			})(),
		);
	}
});

self.addEventListener("sync", (event) => {
	if (event.tag !== "sync-transactions") {
		return;
	}
	event.waitUntil(
		(async () => {
			const queued = await readQueued();
			const completed = [];
			for (const item of queued) {
				try {
					const headers = { "Content-Type": "application/json" };
					if (item.authorization) {
						headers.Authorization = item.authorization;
					}
					const response = await fetch(item.url, {
						method: "POST",
						headers,
						body: JSON.stringify(item.payload),
					});
					if (response.ok) {
						completed.push(item.id);
					}
				} catch {}
			}
			if (completed.length > 0) {
				await clearQueued(completed);
			}
		})(),
	);
});
