import { useStore } from '../store/useStore';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend
} from 'recharts';
import { formatCurrency } from '../utils/helpers';
import { TrendingUp, Printer, Scissors, CheckCircle } from 'lucide-react';
import PageHeader from '../components/PageHeader';

const COLORS = ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd', '#818cf8', '#4f46e5'];

const monthlyData = [
  { month: 'يناير', orders: 12, revenue: 8500, completed: 10 },
  { month: 'فبراير', orders: 18, revenue: 12000, completed: 15 },
  { month: 'مارس', orders: 14, revenue: 9800, completed: 12 },
  { month: 'أبريل', orders: 22, revenue: 15600, completed: 20 },
  { month: 'مايو', orders: 28, revenue: 18200, completed: 24 },
];

export default function Reports() {
  const { orders, customers, materials, printQueue, cutQueue } = useStore();

  const completed = orders.filter((o) => o.status === 'completed').length;
  const totalRevenue = orders.filter((o) => o.status !== 'cancelled').reduce((s, o) => s + o.totalAmount, 0);
  const collected = orders.filter((o) => o.status !== 'cancelled').reduce((s, o) => s + o.depositAmount, 0);
  const pending = totalRevenue - collected;

  const statusDistribution = [
    { name: 'انتظار', value: orders.filter((o) => o.status === 'pending').length },
    { name: 'تصميم', value: orders.filter((o) => o.status === 'designing').length },
    { name: 'طباعة', value: orders.filter((o) => o.status === 'printing').length },
    { name: 'قص', value: orders.filter((o) => o.status === 'cutting').length },
    { name: 'مكتمل', value: orders.filter((o) => o.status === 'completed').length },
    { name: 'ملغي', value: orders.filter((o) => o.status === 'cancelled').length },
  ].filter((s) => s.value > 0);

  const jobTypeData = [
    { name: 'طباعة وقص', value: orders.filter((o) => o.items.some((i) => i.jobType === 'print_cut')).length },
    { name: 'طباعة فقط', value: orders.filter((o) => o.items.some((i) => i.jobType === 'print')).length },
    { name: 'قص فقط', value: orders.filter((o) => o.items.some((i) => i.jobType === 'cut')).length },
  ];

  const topCustomers = customers.map((c) => ({
    name: c.name,
    orders: orders.filter((o) => o.customerId === c.id).length,
    revenue: orders.filter((o) => o.customerId === c.id && o.status !== 'cancelled').reduce((s, o) => s + o.totalAmount, 0),
  })).sort((a, b) => b.revenue - a.revenue).slice(0, 5);

  const materialUsage = materials.map((m) => ({
    name: m.name.substring(0, 15),
    used: orders.flatMap((o) => o.items).filter((i) => i.materialId === m.id).reduce((s, i) => s + i.quantity, 0),
  })).filter((m) => m.used > 0).sort((a, b) => b.used - a.used).slice(0, 6);

  return (
    <div>
      <PageHeader title="التقارير والإحصائيات" subtitle="تحليل شامل لأداء العمل" />

      <div className="p-6 space-y-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard
            title="إجمالي الإيرادات"
            value={formatCurrency(totalRevenue)}
            icon={<TrendingUp size={18} />}
            color="text-green-600 bg-green-100"
            sub={`${formatCurrency(pending)} متبقي`}
          />
          <KpiCard
            title="الطلبات المكتملة"
            value={`${completed} / ${orders.length}`}
            icon={<CheckCircle size={18} />}
            color="text-indigo-600 bg-indigo-100"
            sub={`${Math.round((completed / orders.length) * 100)}% معدل الإنجاز`}
          />
          <KpiCard
            title="مهام الطباعة"
            value={printQueue.filter((j) => j.status === 'done').length}
            icon={<Printer size={18} />}
            color="text-purple-600 bg-purple-100"
            sub={`${printQueue.filter((j) => j.status === 'queued').length} في الطابور`}
          />
          <KpiCard
            title="مهام القص"
            value={cutQueue.filter((j) => j.status === 'done').length}
            icon={<Scissors size={18} />}
            color="text-orange-600 bg-orange-100"
            sub={`${cutQueue.filter((j) => j.status === 'queued').length} في الطابور`}
          />
        </div>

        {/* Monthly Performance */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="font-semibold text-gray-900 mb-4">الأداء الشهري</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis yAxisId="left" tick={{ fontSize: 12 }} />
              <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="orders" name="الطلبات" stroke="#6366f1" strokeWidth={2} dot={{ r: 4 }} />
              <Line yAxisId="left" type="monotone" dataKey="completed" name="المكتملة" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* Revenue Bar Chart */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-4">الإيرادات الشهرية</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => [formatCurrency(v as number), 'الإيرادات']} />
                <Bar dataKey="revenue" name="الإيرادات" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Status Distribution */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-4">توزيع حالات الطلبات</h3>
            <div className="flex items-center gap-4">
              <ResponsiveContainer width="50%" height={160}>
                <PieChart>
                  <Pie data={statusDistribution} cx="50%" cy="50%" outerRadius={70} dataKey="value">
                    {statusDistribution.map((_, index) => (
                      <Cell key={index} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex-1 space-y-1.5">
                {statusDistribution.map((item, index) => (
                  <div key={item.name} className="flex items-center gap-2 text-xs">
                    <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: COLORS[index % COLORS.length] }} />
                    <span className="text-gray-600 flex-1">{item.name}</span>
                    <span className="font-semibold text-gray-900">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* Top Customers */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-4">أفضل العملاء</h3>
            <div className="space-y-3">
              {topCustomers.map((c, i) => (
                <div key={c.name} className="flex items-center gap-3">
                  <span className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold shrink-0">
                    {i + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-900 truncate">{c.name}</span>
                      <span className="text-sm font-bold text-gray-900 mr-2">{formatCurrency(c.revenue)}</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-1.5">
                      <div
                        className="bg-indigo-500 h-1.5 rounded-full"
                        style={{ width: `${(c.revenue / topCustomers[0].revenue) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Material Usage */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-4">استهلاك المواد</h3>
            {materialUsage.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={materialUsage} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 10 }} width={100} />
                  <Tooltip />
                  <Bar dataKey="used" name="الاستخدام" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center py-8 text-gray-400 text-sm">
                لا توجد بيانات استهلاك
              </div>
            )}
          </div>
        </div>

        {/* Job Types */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="font-semibold text-gray-900 mb-4">توزيع أنواع المهام</h3>
          <div className="grid grid-cols-3 gap-4">
            {jobTypeData.map((item, i) => (
              <div key={item.name} className="text-center p-4 bg-gray-50 rounded-xl">
                <div className="text-3xl font-bold mb-1" style={{ color: COLORS[i] }}>{item.value}</div>
                <div className="text-sm text-gray-600">{item.name}</div>
                <div className="text-xs text-gray-400 mt-1">
                  {orders.length > 0 ? Math.round((item.value / orders.length) * 100) : 0}%
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function KpiCard({ title, value, icon, color, sub }: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  sub: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${color}`}>
        {icon}
      </div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      <div className="text-sm text-gray-600 mt-0.5">{title}</div>
      <div className="text-xs text-gray-400 mt-1">{sub}</div>
    </div>
  );
}
