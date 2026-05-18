import { useEffect, useMemo, useRef, useState } from 'react';
import { X, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { useNavigate } from 'react-router';
import api, { getValidAccessToken } from '../../lib/api';

export interface NotificationItem {
  id: string;
  type: 'pending' | 'received' | 'reminder';
  title: string;
  message: string;
  timestamp: string;
  route?: string;
}

interface NotificationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  notifications: NotificationItem[];
  onNotificationsChange?: (items: NotificationItem[]) => void;
  onUnreadCountChange?: (count: number) => void;
}

function toWsUrl(httpUrl: string): string {
  const url = new URL(httpUrl);
  if (url.protocol === 'ws:' || url.protocol === 'wss:') {
    return `${url.protocol}//${url.host}`;
  }
  const scheme = url.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${scheme}//${url.host}`;
}

type ApiNotificationRow = {
  id: string | number;
  type: string;
  payload?: {
    title?: string;
    body?: string;
  };
  created_at?: string;
};

type NotificationListResponse = {
  next: string | null;
  previous: string | null;
  results: ApiNotificationRow[];
};

export function NotificationDrawer({ isOpen, onClose, notifications, onNotificationsChange, onUnreadCountChange }: NotificationDrawerProps) {
  const navigate = useNavigate();
  const wsRef = useRef<WebSocket | null>(null);
  const notificationsRef = useRef<NotificationItem[]>(notifications);
  const reconnectTimerRef = useRef<number | null>(null);
  const reconnectAttemptRef = useRef(0);
  const listRef = useRef<HTMLDivElement | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loadingInitial, setLoadingInitial] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [showMoreButton, setShowMoreButton] = useState(false);
  const [seenAt, setSeenAt] = useState<number>(Date.now());

  useEffect(() => {
    notificationsRef.current = notifications;
  }, [notifications]);

  const unreadCount = useMemo(() => {
    if (isOpen) {
      return 0;
    }
    return notifications.filter((notification) => {
      const ts = Date.parse(notification.timestamp || '');
      if (Number.isNaN(ts)) {
        return false;
      }
      return ts > seenAt;
    }).length;
  }, [isOpen, notifications, seenAt]);

  useEffect(() => {
    onUnreadCountChange?.(unreadCount);
  }, [unreadCount, onUnreadCountChange]);

  const dedupeById = (items: NotificationItem[]) => {
    const seen = new Set<string>();
    return items.filter((item) => {
      if (seen.has(item.id)) {
        return false;
      }
      seen.add(item.id);
      return true;
    });
  };

  const toNotificationItem = (row: ApiNotificationRow): NotificationItem => {
    const isFriendRequest = row.type === 'friend_request';
    const mappedType: NotificationItem['type'] =
      row.type === 'lend_confirmation' ? 'pending' : row.type === 'due_reminder' ? 'reminder' : 'received';
    return {
      id: String(row.id || crypto.randomUUID()),
      type: mappedType,
      title: row.payload?.title || (isFriendRequest ? 'New friend request' : 'Notification'),
      message: row.payload?.body || 'You have a new notification.',
      timestamp: row.created_at || new Date().toISOString(),
      route: isFriendRequest ? '/friends' : undefined,
    };
  };

  const extractCursor = (nextUrl: string | null): string | null => {
    if (!nextUrl) {
      return null;
    }
    try {
      const parsed = nextUrl.startsWith('http') ? new URL(nextUrl) : new URL(nextUrl, window.location.origin);
      return parsed.searchParams.get('cursor');
    } catch {
      return null;
    }
  };

  const fetchNotificationPage = async (cursor: string | null, append: boolean) => {
    if (append) {
      setLoadingMore(true);
    } else {
      setLoadingInitial(true);
    }

    try {
      const params = cursor ? { cursor } : {};
      const { data } = await api.get<NotificationListResponse>('/api/notification/list/', { params });
      const mapped = (data?.results || []).map(toNotificationItem);
      const nextItems = append
        ? dedupeById([...notificationsRef.current, ...mapped])
        : dedupeById(mapped);
      onNotificationsChange?.(nextItems);
      setNextCursor(extractCursor(data?.next || null));
      setShowMoreButton(false);
    } catch {
      if (!append) {
        onNotificationsChange?.([]);
      }
      setNextCursor(null);
    } finally {
      if (append) {
        setLoadingMore(false);
      } else {
        setLoadingInitial(false);
      }
    }
  };

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    setSeenAt(Date.now());
    void fetchNotificationPage(null, false);
  }, [isOpen]);

  useEffect(() => {
    if (isOpen) {
      setSeenAt(Date.now());
    }
  }, [isOpen, notifications.length]);

  useEffect(() => {
    let cancelled = false;

    const clearReconnectTimer = () => {
      if (reconnectTimerRef.current !== null) {
        window.clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
    };

    const scheduleReconnect = () => {
      if (cancelled) {
        return;
      }

      const delay = Math.min(2000 * (reconnectAttemptRef.current + 1), 15000);
      reconnectAttemptRef.current += 1;
      clearReconnectTimer();
      reconnectTimerRef.current = window.setTimeout(() => {
        void connect();
      }, delay);
    };

    const connect = async () => {
      const token = await getValidAccessToken();
      if (!token || cancelled) {
        scheduleReconnect();
        return;
      }

      const base = import.meta.env.VITE_NOTIFICATION_WS_URL || 'https://soccho-notification.onrender.com';
      const wsBase = toWsUrl(base);
      const ws = new WebSocket(`${wsBase}/ws/notifications/?token=${encodeURIComponent(token)}`);
      wsRef.current = ws;

      ws.onopen = () => {
        reconnectAttemptRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (
            payload?.event === 'transaction.created'
            || payload?.event === 'notification.push'
            || payload?.event === 'notification.pending'
            || payload?.event === 'friend.request'
          ) {
            const row = payload.notification || {};
            const item: NotificationItem = {
              id: String(row.id || crypto.randomUUID()),
              type: payload?.event === 'transaction.created' ? 'pending' : row.type === 'due_reminder' ? 'reminder' : 'received',
              title: row.payload?.title || payload?.event || 'Notification',
              message: row.payload?.body || 'You have a new notification.',
              timestamp: row.created_at || new Date().toISOString(),
              route: payload?.event === 'friend.request' || row.type === 'friend_request' ? '/friends' : undefined,
            };
            onNotificationsChange?.(dedupeById([item, ...notificationsRef.current]));
          }
        } catch {
          return;
        }
      };

      ws.onerror = () => {
        console.warn('Notification websocket error');
        scheduleReconnect();
      };

      ws.onclose = (event) => {
        console.warn('Notification websocket closed', { code: event.code, reason: event.reason });
        if (wsRef.current === ws) {
          wsRef.current = null;
        }
        scheduleReconnect();
      };
    };

    void connect();

    return () => {
      cancelled = true;
      clearReconnectTimer();
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [onNotificationsChange]);

  const handleAction = (id: string, action: 'agree' | 'disagree') => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ action, notification_id: id }));

    if (action === 'agree') {
      onNotificationsChange?.(notificationsRef.current.filter((n) => n.id !== id));
    }
  };

  const getIcon = (type: NotificationItem['type']) => {
    switch (type) {
      case 'pending':
        return <Clock size={20} className="text-[#F59E0B]" />;
      case 'received':
        return <CheckCircle size={20} className="text-[#9CA3AF]" />;
      case 'reminder':
        return <AlertCircle size={20} className="text-[#EF4444]" />;
    }
  };

  const getBorderColor = (type: NotificationItem['type']) => {
    switch (type) {
      case 'pending':
        return 'border-l-[#F59E0B]';
      case 'received':
        return 'border-l-[#9CA3AF]';
      case 'reminder':
        return 'border-l-[#EF4444]';
    }
  };

  const handleNotificationClick = (notification: NotificationItem) => {
    if (!notification.route) {
      return;
    }
    onClose();
    navigate(notification.route);
  };

  const handleListScroll = () => {
    const el = listRef.current;
    if (!el) {
      return;
    }
    const nearBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 80;
    setShowMoreButton(nearBottom && !!nextCursor);
  };

  const handleShowMore = async () => {
    if (!nextCursor || loadingMore) {
      return;
    }
    await fetchNotificationPage(nextCursor, true);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }} className="fixed inset-0 bg-black/40 z-40" onClick={onClose} />

          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            className="fixed left-0 top-0 bottom-0 w-[70%] bg-white z-50 shadow-2xl rounded-r-2xl overflow-y-auto"
            ref={listRef}
            onScroll={handleListScroll}
          >
            <div className="p-4 border-b border-[#E5E7EB] flex items-center justify-between sticky top-0 bg-white">
              <h2 className="font-bold text-lg" style={{ fontFamily: 'var(--font-display)' }}>
                Notifications
              </h2>
              <button onClick={onClose} className="p-2 hover:bg-[#F3F4F6] rounded-lg transition-colors">
                <X size={20} />
              </button>
            </div>

            <div className="p-4 space-y-3">
              {loadingInitial && (
                <p className="text-sm text-[#6B7280]">Loading notifications...</p>
              )}
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 bg-white border-l-4 ${getBorderColor(notification.type)} rounded-lg shadow-sm ${notification.route ? 'cursor-pointer hover:bg-[#F9FAFB]' : ''}`}
                  onClick={() => handleNotificationClick(notification)}
                  role={notification.route ? 'button' : undefined}
                  tabIndex={notification.route ? 0 : undefined}
                  onKeyDown={(event) => {
                    if (!notification.route) {
                      return;
                    }
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault();
                      handleNotificationClick(notification);
                    }
                  }}
                >
                  <div className="flex items-start gap-3">
                    {getIcon(notification.type)}
                    <div className="flex-1">
                      <h3 className="font-medium text-sm text-[#111827] mb-1">{notification.title}</h3>
                      <p className="text-sm text-[#6B7280] mb-2">{notification.message}</p>
                      <p className="text-xs text-[#9CA3AF]">{notification.timestamp}</p>

                      {notification.type === 'pending' && (
                        <div className="flex gap-2 mt-3">
                          <button onClick={() => handleAction(notification.id, 'agree')} className="px-3 py-1.5 bg-[#10B981] text-white text-sm rounded-lg hover:bg-[#059669] transition-colors">
                            Agree
                          </button>
                          <button onClick={() => handleAction(notification.id, 'disagree')} className="px-3 py-1.5 bg-[#EF4444] text-white text-sm rounded-lg hover:bg-[#DC2626] transition-colors">
                            Disagree
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {notifications.length === 0 && (
                <div className="text-center py-12 text-[#6B7280]">
                  <p>No notifications</p>
                </div>
              )}

              {showMoreButton && !!nextCursor && (
                <div className="pt-2">
                  <button
                    onClick={() => void handleShowMore()}
                    disabled={loadingMore}
                    className={`w-full px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      loadingMore ? 'bg-[#E5E7EB] text-[#6B7280]' : 'bg-[#111827] text-white hover:bg-black'
                    }`}
                  >
                    {loadingMore ? 'Loading...' : 'Show more'}
                  </button>
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
