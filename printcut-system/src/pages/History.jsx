import { useState } from 'react';
import { Calendar, Download, Filter, Search, FileText, BarChart3 } from 'lucide-react';
import Header from '../components/Header';
import { useApp } from '../context/AppContext';
import { statusMap, jobTypes, priorityMap } from '../data/initialData';

export default function History() {
  const { state } = useApp();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [dateRange, setDateRange] = useState('all');

  const completedStatuses = ['completed', 'failed', 'cancelled'];

  const historyJobs = state.jobs
    .filter(j => {
      if (filterStatus === 'all') return completedStatuses.includes(j.status);
      return j.status === filterStatus;
    })
    .filter(j => {
      if (!searchQuery) return true;
      const q = searchQuery.toLowerCase();
      return j.name.toLowerCase().includes(q) || j.client.toLowerCase().includes(q);
    })
    .sort((a, b) => {
      const dateA = new Date(a.completedAt || a.createdAt);
      const dateB = new Date(b.completedAt || b.createdAt);
      return dateB - dateA;
    });

  const stats = {
    completed: state.jobs.filter(j => j.status === 'completed').length,
    failed: state.jobs.filter(j => j.status === 'failed').length,
    cancelled: state.jobs.filter(j => j.status === 'cancelled').length,
    totalRevenue: state.jobs.filter(j => j.status === 'completed').reduce((s, j) => s + j.price, 0),
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('ar-SA', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div>
      <Header title="السجل" subtitle="سجل جميع المهام المكتملة والملغاة" />

      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div className="bg-accent-50 rounded-2xl p-4 border border-accent-100">
            <p className="text-sm text-accent-700">مكتملة</p>
            <p className="text-2xl font-bold text-accent-800">{stats.completed}</p>
          </div>
          <div className="bg-danger-50 rounded-2xl p-4 border border-danger-100">
            <p className="text-sm text-danger-600">فاشلة</p>
            <p className="text-2xl font-bold text-danger-700">{stats.failed}</p>
          </div>
          <div className="bg-gray-50 rounded-2xl p-4 border border-gray-200">
            <p className="text-sm text-gray-600">ملغاة</p>
            <p className="text-2xl font-bold text-gray-800">{stats.cancelled}</p>
          </div>
          <div className="bg-primary-50 rounded-2xl p-4 border border-primary-100">
            <p className="text-sm text-primary-700">إجمالي الإيرادات</p>
            <p className="text-2xl font-bold text-primary-800">{stats.totalRevenue.toLocaleString('ar-SA')} ر.س</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="w-4 h-4 absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="بحث في السجل..."
              className="w-full pr-10 pl-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
          >
            <option value="all">جميع الحالات</option>
            <option value="completed">مكتملة</option>
            <option value="failed">فاشلة</option>
            <option value="cancelled">ملغاة</option>
          </select>
        </div>

        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          {historyJobs.length === 0 ? (
            <div className="p-12 text-center">
              <BarChart3 className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <h4 className="text-lg font-semibold text-gray-400">لا توجد سجلات</h4>
              <p className="text-sm text-gray-400 mt-1">سيظهر هنا سجل المهام المكتملة</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-100">
                    <th className="text-right px-5 py-3 font-semibold text-gray-600">المهمة</th>
                    <th className="text-right px-5 py-3 font-semibold text-gray-600">العميل</th>
                    <th className="text-right px-5 py-3 font-semibold text-gray-600">النوع</th>
                    <th className="text-right px-5 py-3 font-semibold text-gray-600">الحالة</th>
                    <th className="text-right px-5 py-3 font-semibold text-gray-600">الأبعاد</th>
                    <th className="text-right px-5 py-3 font-semibold text-gray-600">السعر</th>
                    <th className="text-right px-5 py-3 font-semibold text-gray-600">التاريخ</th>
                  </tr>
                </thead>
                <tbody>
                  {historyJobs.map(job => {
                    const status = statusMap[job.status];
                    const type = jobTypes.find(t => t.id === job.type);
                    return (
                      <tr key={job.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                        <td className="px-5 py-3.5">
                          <div className="flex items-center gap-2">
                            <FileText className="w-4 h-4 text-gray-400" />
                            <span className="font-medium text-gray-900">{job.name}</span>
                          </div>
                        </td>
                        <td className="px-5 py-3.5 text-gray-600">{job.client}</td>
                        <td className="px-5 py-3.5">
                          <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${type?.color}`}>
                            {type?.name}
                          </span>
                        </td>
                        <td className="px-5 py-3.5">
                          <span className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-medium w-fit ${status.color}`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${status.dot}`} />
                            {status.name}
                          </span>
                        </td>
                        <td className="px-5 py-3.5 text-gray-600">
                          {job.width}×{job.height} {job.unit}
                        </td>
                        <td className="px-5 py-3.5 font-semibold text-gray-900">
                          {job.price} ر.س
                        </td>
                        <td className="px-5 py-3.5 text-gray-500 text-xs">
                          {formatDate(job.completedAt || job.createdAt)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
