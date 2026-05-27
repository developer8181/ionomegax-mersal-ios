import { useStore } from '../store/useStore';
import { ShoppingBag, Users, Printer, Scissors, TrendingUp, Clock, AlertCircle } from 'lucide-react';
import { formatCurrency, formatDate, getStatusColor, getStatusLabel, getPriorityColor, getPriorityLabel } from '../utils/helpers';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Link } from 'react-router-dom';

const revenueData = [
  { month: 'يناير', revenue: 8500 },
  { month: 'فبراير', revenue: 12000 },
  { month: 'مارس', revenue: 9800 },
  { month: 'أبريل', revenue: 15600 },
  { month: 'مايو', revenue: 18200 },
];

const jobTypeData = [
  { name: 'طباعة وقص', value: 45, color: '#6366f1' },
  { name: 'طباعة فقط', value: 35, color: '#8b5cf6' },
  { name: 'قص فقط', value: 20, color: '#a78bfa' },
];

export default function Dashboard() {
  const { orders, customers, printQueue, cutQueue } = useStore();

  const stats = {
    total: orders.length,
    pending: orders.filter((o) => ['pending', 'designing'].includes(o.status)).length,
    inProgress: orders.filter((o) => ['printing', 'cutting'].includes(o.status)).length,
    completed: orders.filter((o) => o.status === 'completed').length,
    revenue: orders.filter((o) => o.status !== 'cancelled').reduce((s, o) => s + o.totalAmount, 0),
    pendingRevenue: orders.filter((o) => o.status !== 'cancelled' && o.status !== 'completed').reduce((s, o) => s + (o.totalAmount - o.depositAmount), 0),
    printing: printQueue.filter((j) => j.status === 'printing').length,
    queued: printQueue.filter((j) => j.status === 'queued').length,
    cutting: cutQueue.filter((j) => j.status === 'cutting').length,
    cutQueued: cutQueue.filter((j) => j.status === 'queued').length,
  };

  const recentOrders = [...orders].sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime()).slice(0, 5);
  const urgentOrders = orders.filter((o) => o.priority === 'urgent' && o.status !== 'completed');

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">لوحة التحكم</h1>
          <p className="text-sm text-gray-500 mt-1">مرحباً! هذا ملخص نشاط اليوم</p>
        </div>
        <div className="text-sm text-gray-500 bg-white px-4 py-2 rounded-lg border border-gray-200">
          {new Date().toLocaleDateString('ar-SA', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
        </div>
      </div>

      {/* Urgent alert */}
      {urgentOrders.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
          <AlertCircle className="text-red-500 shrink-0" size={20} />
          <div>
            <span className="font-semibold text-red-800">تنبيه: </span>
            <span className="text-red-700">لديك {urgentOrders.length} طلب عاجل بحاجة للاهتمام الفوري</span>
          </div>
          <Link to="/orders" className="mr-auto text-sm text-red-600 hover:text-red-800 font-medium underline">
            عرض الطلبات
          </Link>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="إجمالي الطلبات"
          value={stats.total}
          icon={<ShoppingBag size={20} />}
          color="indigo"
          sub={`${stats.pending} في الانتظار`}
        />
        <StatCard
          title="قيد التنفيذ"
          value={stats.inProgress}
          icon={<Clock size={20} />}
          color="yellow"
          sub={`${stats.completed} مكتمل`}
        />
        <StatCard
          title="إجمالي الإيرادات"
          value={formatCurrency(stats.revenue)}
          icon={<TrendingUp size={20} />}
          color="green"
          sub={`${formatCurrency(stats.pendingRevenue)} متبقي`}
        />
        <StatCard
          title="العملاء"
          value={customers.length}
          icon={<Users size={20} />}
          color="blue"
          sub="عميل نشط"
        />
      </div>

      {/* Queue Status */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 bg-purple-100 rounded-lg flex items-center justify-center">
              <Printer size={18} className="text-purple-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">طابور الطباعة</h3>
              <p className="text-xs text-gray-500">{printQueue.length} مهمة إجمالاً</p>
            </div>
          </div>
          <div className="flex gap-3">
            <div className="flex-1 bg-purple-50 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-purple-700">{stats.printing}</div>
              <div className="text-xs text-purple-600 mt-1">جارية الطباعة</div>
            </div>
            <div className="flex-1 bg-gray-50 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-gray-700">{stats.queued}</div>
              <div className="text-xs text-gray-600 mt-1">في الطابور</div>
            </div>
          </div>
          <Link to="/print-queue" className="mt-3 flex items-center justify-center text-sm text-purple-600 hover:text-purple-800 font-medium">
            إدارة الطابور ←
          </Link>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 bg-orange-100 rounded-lg flex items-center justify-center">
              <Scissors size={18} className="text-orange-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">طابور القص</h3>
              <p className="text-xs text-gray-500">{cutQueue.length} مهمة إجمالاً</p>
            </div>
          </div>
          <div className="flex gap-3">
            <div className="flex-1 bg-orange-50 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-orange-700">{stats.cutting}</div>
              <div className="text-xs text-orange-600 mt-1">جارية القص</div>
            </div>
            <div className="flex-1 bg-gray-50 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-gray-700">{stats.cutQueued}</div>
              <div className="text-xs text-gray-600 mt-1">في الطابور</div>
            </div>
          </div>
          <Link to="/cut-queue" className="mt-3 flex items-center justify-center text-sm text-orange-600 hover:text-orange-800 font-medium">
            إدارة الطابور ←
          </Link>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-3 gap-4">
        {/* Revenue Chart */}
        <div className="col-span-2 bg-white rounded-xl border border-gray-200 p-4">
          <h3 className="font-semibold text-gray-900 mb-4">الإيرادات الشهرية</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={revenueData}>
              <defs>
                <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v) => [formatCurrency(v as number), 'الإيرادات']} />
              <Area type="monotone" dataKey="revenue" stroke="#6366f1" fill="url(#colorRevenue)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Job Types Pie */}
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <h3 className="font-semibold text-gray-900 mb-4">أنواع المهام</h3>
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie data={jobTypeData} cx="50%" cy="50%" innerRadius={40} outerRadius={70} dataKey="value">
                {jobTypeData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-1 mt-2">
            {jobTypeData.map((item) => (
              <div key={item.name} className="flex items-center gap-2 text-xs">
                <span className="w-2 h-2 rounded-full shrink-0" style={{ background: item.color }} />
                <span className="text-gray-600">{item.name}</span>
                <span className="mr-auto font-medium">{item.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Orders */}
      <div className="bg-white rounded-xl border border-gray-200">
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <h3 className="font-semibold text-gray-900">آخر الطلبات</h3>
          <Link to="/orders" className="text-sm text-indigo-600 hover:text-indigo-800 font-medium">
            عرض الكل
          </Link>
        </div>
        <div className="divide-y divide-gray-50">
          {recentOrders.map((order) => (
            <div key={order.id} className="flex items-center gap-4 px-4 py-3 hover:bg-gray-50 transition-colors">
              <div className="w-9 h-9 bg-indigo-100 rounded-lg flex items-center justify-center text-indigo-700 font-bold text-xs shrink-0">
                {order.orderNumber.split('-')[2]}
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-medium text-gray-900 text-sm">{order.customerName}</div>
                <div className="text-xs text-gray-500">{order.orderNumber} · {formatDate(order.createdAt)}</div>
              </div>
              <span className={`text-xs px-2 py-1 rounded-full font-medium ${getStatusColor(order.status)}`}>
                {getStatusLabel(order.status)}
              </span>
              <span className={`text-xs px-2 py-1 rounded-full font-medium ${getPriorityColor(order.priority)}`}>
                {getPriorityLabel(order.priority)}
              </span>
              <div className="text-sm font-semibold text-gray-900">{formatCurrency(order.totalAmount)}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon, color, sub }: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  sub: string;
}) {
  const colors: Record<string, string> = {
    indigo: 'bg-indigo-100 text-indigo-600',
    yellow: 'bg-yellow-100 text-yellow-600',
    green: 'bg-green-100 text-green-600',
    blue: 'bg-blue-100 text-blue-600',
  };
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <div className="flex items-start justify-between mb-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colors[color]}`}>
          {icon}
        </div>
      </div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      <div className="text-sm text-gray-600 mt-0.5">{title}</div>
      <div className="text-xs text-gray-400 mt-1">{sub}</div>
    </div>
  );
}
