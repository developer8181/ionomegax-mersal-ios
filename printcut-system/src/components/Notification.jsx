import { CheckCircle, AlertCircle, Info, X } from 'lucide-react';
import { useApp } from '../context/AppContext';

const icons = {
  success: CheckCircle,
  error: AlertCircle,
  info: Info,
};

const styles = {
  success: 'bg-accent-50 border-accent-500 text-accent-800',
  error: 'bg-danger-50 border-danger-500 text-danger-800',
  info: 'bg-primary-50 border-primary-500 text-primary-800',
};

export default function Notification() {
  const { state, dispatch } = useApp();
  if (!state.notification) return null;

  const { message, type } = state.notification;
  const Icon = icons[type] || Info;

  return (
    <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 animate-slide-in">
      <div className={`flex items-center gap-3 px-5 py-3 rounded-xl border-r-4 shadow-lg ${styles[type]}`}>
        <Icon className="w-5 h-5 shrink-0" />
        <span className="text-sm font-medium">{message}</span>
        <button
          onClick={() => dispatch({ type: 'CLEAR_NOTIFICATION' })}
          className="p-1 hover:bg-black/5 rounded-full transition-colors mr-2"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
