import { useEffect, useMemo, useRef } from 'react';
import { X, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

export interface NotificationItem {
  id: string;
  type: 'pending' | 'received' | 'reminder';
  title: string;
  message: string;
  timestamp: string;
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
  const scheme = url.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${scheme}//${url.host}`;
}

export function NotificationDrawer({ isOpen, onClose, notifications, onNotificationsChange, onUnreadCountChange }: NotificationDrawerProps) {
  const wsRef = useRef<WebSocket | null>(null);
  const notificationsRef = useRef<NotificationItem[]>(notifications);

  useEffect(() => {
    notificationsRef.current = notifications;
  }, [notifications]);

  const unreadCount = useMemo(() => notifications.filter((n) => n.type === 'pending').length, [notifications]);

  useEffect(() => {
    onUnreadCountChange?.(unreadCount);
  }, [unreadCount, onUnreadCountChange]);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    const base = import.meta.env.VITE_NOTIFICATION_WS_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const wsBase = toWsUrl(base);
    const ws = new WebSocket(`${wsBase}/ws/notifications/?token=${encodeURIComponent(token)}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload?.event === 'transaction.created' || payload?.event === 'notification.push' || payload?.event === 'notification.pending') {
          const row = payload.notification || {};
          const item: NotificationItem = {
            id: String(row.id || crypto.randomUUID()),
            type: payload?.event === 'transaction.created' ? 'pending' : row.type === 'due_reminder' ? 'reminder' : 'received',
            title: row.payload?.title || payload?.event || 'Notification',
            message: row.payload?.body || JSON.stringify(row.payload || {}),
            timestamp: row.created_at || new Date().toISOString(),
          };
          onNotificationsChange?.([item, ...notificationsRef.current]);
        }
      } catch {
        return;
      }
    };

    return () => {
      ws.close();
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
              {notifications.map((notification) => (
                <div key={notification.id} className={`p-4 bg-white border-l-4 ${getBorderColor(notification.type)} rounded-lg shadow-sm`}>
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
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
