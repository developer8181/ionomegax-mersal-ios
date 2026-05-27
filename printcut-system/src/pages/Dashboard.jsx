import {
  Printer,
  Scissors,
  CheckCircle,
  Clock,
  TrendingUp,
  DollarSign,
  AlertTriangle,
  ArrowUpLeft,
} from 'lucide-react';
import Header from '../components/Header';
import StatCard from '../components/StatCard';
import JobCard from '../components/JobCard';
import { useApp } from '../context/AppContext';
import { statusMap } from '../data/initialData';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const { state } = useApp();
  const { jobs } = state;

  const stats = {
    total: jobs.length,
    queued: jobs.filter(j => j.status === 'queued').length,
    inProgress: jobs.filter(j => j.status === 'in_progress').length,
    completed: jobs.filter(j => j.status === 'completed').length,
    failed: jobs.filter(j => j.status === 'failed').length,
    totalRevenue: jobs.filter(j => j.status === 'completed').reduce((sum, j) => sum + j.price, 0),
    pendingRevenue: jobs.filter(j => ['queued', 'in_progress'].includes(j.status)).reduce((sum, j) => sum + j.price, 0),
  };

  const recentJobs = [...jobs]
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    .slice(0, 5);

  const activeJobs = jobs.filter(j => j.status === 'in_progress');

  return (
    <div>
      <Header title="لوحة التحكم" subtitle="نظرة عامة على حالة النظام" />

      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            icon={Printer}
            label="إجمالي المهام"
            value={stats.total}
            change={12}
            color="text-primary-600"
            bgColor="bg-primary-50"
          />
          <StatCard
            icon={Clock}
            label="في الانتظار"
            value={stats.queued}
            color="text-warning-500"
            bgColor="bg-warning-50"
          />
          <StatCard
            icon={TrendingUp}
            label="قيد التنفيذ"
            value={stats.inProgress}
            color="text-blue-600"
            bgColor="bg-blue-50"
          />
          <StatCard
            icon={CheckCircle}
            label="مكتملة"
            value={stats.completed}
            change={8}
            color="text-accent-600"
            bgColor="bg-accent-50"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="bg-gradient-to-br from-primary-600 to-primary-800 rounded-2xl p-6 text-white">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold">الإيرادات المحققة</h3>
              <DollarSign className="w-6 h-6 opacity-80" />
            </div>
            <p className="text-3xl font-bold">{stats.totalRevenue.toLocaleString('ar-SA')} ر.س</p>
            <p className="text-sm opacity-80 mt-2">من {stats.completed} مهمة مكتملة</p>
          </div>

          <div className="bg-gradient-to-br from-accent-600 to-accent-800 rounded-2xl p-6 text-white">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold">إيرادات معلقة</h3>
              <ArrowUpLeft className="w-6 h-6 opacity-80" />
            </div>
            <p className="text-3xl font-bold">{stats.pendingRevenue.toLocaleString('ar-SA')} ر.س</p>
            <p className="text-sm opacity-80 mt-2">من {stats.queued + stats.inProgress} مهمة</p>
          </div>

          <div className="bg-gradient-to-br from-orange-500 to-red-600 rounded-2xl p-6 text-white">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold">تحتاج انتباه</h3>
              <AlertTriangle className="w-6 h-6 opacity-80" />
            </div>
            <p className="text-3xl font-bold">{stats.failed}</p>
            <p className="text-sm opacity-80 mt-2">مهام فاشلة تحتاج مراجعة</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm">
            <div className="flex items-center justify-between p-5 border-b border-gray-100">
              <h3 className="text-base font-bold text-gray-900">المهام النشطة</h3>
              <Link to="/jobs" className="text-sm text-primary-600 hover:text-primary-700 font-medium">
                عرض الكل
              </Link>
            </div>
            <div className="p-4 space-y-3">
              {activeJobs.length > 0 ? (
                activeJobs.map(job => <JobCard key={job.id} job={job} compact />)
              ) : (
                <p className="text-sm text-gray-400 text-center py-8">لا توجد مهام نشطة حالياً</p>
              )}
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm">
            <div className="flex items-center justify-between p-5 border-b border-gray-100">
              <h3 className="text-base font-bold text-gray-900">آخر المهام</h3>
              <Link to="/history" className="text-sm text-primary-600 hover:text-primary-700 font-medium">
                عرض السجل
              </Link>
            </div>
            <div className="p-4 space-y-3">
              {recentJobs.map(job => <JobCard key={job.id} job={job} compact />)}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
          <h3 className="text-base font-bold text-gray-900 mb-4">توزيع الحالات</h3>
          <div className="flex gap-3 flex-wrap">
            {Object.entries(statusMap).map(([key, val]) => {
              const count = jobs.filter(j => j.status === key).length;
              const pct = jobs.length > 0 ? Math.round((count / jobs.length) * 100) : 0;
              return (
                <div key={key} className="flex-1 min-w-[120px]">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">{val.name}</span>
                    <span className="text-sm font-bold text-gray-900">{count}</span>
                  </div>
                  <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${val.dot}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-400 mt-1">{pct}%</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
