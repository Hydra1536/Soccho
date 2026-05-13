import { X, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { Button } from './Button';

interface Notification {
  id: string;
  type: 'pending' | 'received' | 'reminder';
  title: string;
  message: string;
  timestamp: string;
}

interface NotificationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  notifications: Notification[];
}

export function NotificationDrawer({ isOpen, onClose, notifications }: NotificationDrawerProps) {
  const handleAgree = (id: string) => {
    console.log('Agreed to:', id);
  };

  const handleDisagree = (id: string) => {
    console.log('Disagreed to:', id);
  };

  const getIcon = (type: Notification['type']) => {
    switch (type) {
      case 'pending':
        return <Clock size={20} className="text-[#F59E0B]" />;
      case 'received':
        return <CheckCircle size={20} className="text-[#9CA3AF]" />;
      case 'reminder':
        return <AlertCircle size={20} className="text-[#EF4444]" />;
    }
  };

  const getBorderColor = (type: Notification['type']) => {
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
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/40 z-40"
            onClick={onClose}
          />

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
              <button
                onClick={onClose}
                className="p-2 hover:bg-[#F3F4F6] rounded-lg transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            <div className="p-4 space-y-3">
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 bg-white border-l-4 ${getBorderColor(notification.type)} rounded-lg shadow-sm`}
                >
                  <div className="flex items-start gap-3">
                    {getIcon(notification.type)}
                    <div className="flex-1">
                      <h3 className="font-medium text-sm text-[#111827] mb-1">
                        {notification.title}
                      </h3>
                      <p className="text-sm text-[#6B7280] mb-2">
                        {notification.message}
                      </p>
                      <p className="text-xs text-[#9CA3AF]">{notification.timestamp}</p>

                      {notification.type === 'pending' && (
                        <div className="flex gap-2 mt-3">
                          <button
                            onClick={() => handleAgree(notification.id)}
                            className="px-3 py-1.5 bg-[#10B981] text-white text-sm rounded-lg hover:bg-[#059669] transition-colors"
                          >
                            Agree
                          </button>
                          <button
                            onClick={() => handleDisagree(notification.id)}
                            className="px-3 py-1.5 bg-[#EF4444] text-white text-sm rounded-lg hover:bg-[#DC2626] transition-colors"
                          >
                            Disagree
                          </button>
                        </div>
                      )}

                      {notification.type === 'reminder' && (
                        <div className="mt-2 flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-[#EF4444] animate-pulse" />
                          <span className="text-xs text-[#EF4444] font-medium">Due soon</span>
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
