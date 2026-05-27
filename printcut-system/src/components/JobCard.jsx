import { statusMap, priorityMap, jobTypes } from '../data/initialData';
import { Clock, FileText, MoreVertical, Play, CheckCircle, XCircle, Trash2 } from 'lucide-react';
import { useState } from 'react';
import { useApp } from '../context/AppContext';

export default function JobCard({ job, compact = false }) {
  const { dispatch, notify } = useApp();
  const [menuOpen, setMenuOpen] = useState(false);

  const status = statusMap[job.status];
  const priority = priorityMap[job.priority];
  const type = jobTypes.find(t => t.id === job.type);

  const handleStatusChange = (newStatus) => {
    dispatch({ type: 'UPDATE_JOB_STATUS', payload: { id: job.id, status: newStatus } });
    const statusName = statusMap[newStatus].name;
    notify(`تم تحديث حالة المهمة إلى: ${statusName}`);
    setMenuOpen(false);
  };

  const handleDelete = () => {
    dispatch({ type: 'DELETE_JOB', payload: job.id });
    notify('تم حذف المهمة بنجاح', 'error');
    setMenuOpen(false);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('ar-SA', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (compact) {
    return (
      <div className="flex items-center justify-between p-3 bg-white rounded-xl border border-gray-100 hover:shadow-sm transition-shadow">
        <div className="flex items-center gap-3">
          <div className={`w-2 h-2 rounded-full ${status.dot}`} />
          <div>
            <p className="text-sm font-semibold text-gray-900">{job.name}</p>
            <p className="text-xs text-gray-500">{job.client}</p>
          </div>
        </div>
        <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${status.color}`}>
          {status.name}
        </span>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden animate-fade-in">
      <div className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${type?.color}`}>
                {type?.name}
              </span>
              <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${priority.color}`}>
                {priority.name}
              </span>
            </div>
            <h3 className="text-base font-bold text-gray-900 mt-2">{job.name}</h3>
            <p className="text-sm text-gray-500">{job.client}</p>
          </div>

          <div className="relative">
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <MoreVertical className="w-4 h-4" />
            </button>
            {menuOpen && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
                <div className="absolute left-0 top-8 bg-white rounded-xl shadow-xl border border-gray-100 py-1 z-20 w-44 animate-fade-in">
                  {job.status !== 'in_progress' && job.status !== 'completed' && (
                    <button
                      onClick={() => handleStatusChange('in_progress')}
                      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
                    >
                      <Play className="w-4 h-4 text-blue-500" />
                      بدء التنفيذ
                    </button>
                  )}
                  {job.status !== 'completed' && (
                    <button
                      onClick={() => handleStatusChange('completed')}
                      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
                    >
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      إكمال المهمة
                    </button>
                  )}
                  {job.status !== 'cancelled' && job.status !== 'completed' && (
                    <button
                      onClick={() => handleStatusChange('cancelled')}
                      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
                    >
                      <XCircle className="w-4 h-4 text-orange-500" />
                      إلغاء المهمة
                    </button>
                  )}
                  <hr className="my-1 border-gray-100" />
                  <button
                    onClick={handleDelete}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-danger-600 hover:bg-danger-50"
                  >
                    <Trash2 className="w-4 h-4" />
                    حذف المهمة
                  </button>
                </div>
              </>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 mt-4">
          <div className="bg-gray-50 rounded-lg p-2.5">
            <p className="text-xs text-gray-500">المادة</p>
            <p className="text-sm font-semibold text-gray-800">{job.material}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-2.5">
            <p className="text-xs text-gray-500">الأبعاد</p>
            <p className="text-sm font-semibold text-gray-800">{job.width}×{job.height} {job.unit}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-2.5">
            <p className="text-xs text-gray-500">النسخ</p>
            <p className="text-sm font-semibold text-gray-800">{job.copies}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-2.5">
            <p className="text-xs text-gray-500">السعر</p>
            <p className="text-sm font-semibold text-gray-800">{job.price} ر.س</p>
          </div>
        </div>

        {job.notes && (
          <p className="text-xs text-gray-500 mt-3 bg-gray-50 rounded-lg p-2.5">
            {job.notes}
          </p>
        )}
      </div>

      <div className="flex items-center justify-between px-5 py-3 bg-gray-50 border-t border-gray-100">
        <div className="flex items-center gap-2">
          <span className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-medium ${status.color}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${status.dot}`} />
            {status.name}
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-gray-400">
          <Clock className="w-3.5 h-3.5" />
          {formatDate(job.createdAt)}
        </div>
      </div>
    </div>
  );
}
