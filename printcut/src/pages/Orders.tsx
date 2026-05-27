import { useState } from 'react';
import { Plus, Search, Eye, Trash2, ChevronDown } from 'lucide-react';
import { useStore } from '../store/useStore';
import type { Order, OrderStatus, Priority } from '../types';
import { formatCurrency, formatDate, getStatusColor, getStatusLabel, getPriorityColor, getPriorityLabel, getJobTypeLabel, generateId } from '../utils/helpers';
import PageHeader from '../components/PageHeader';
import Badge from '../components/Badge';
import Modal from '../components/Modal';

const statusOptions: { value: OrderStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'جميع الحالات' },
  { value: 'pending', label: 'انتظار' },
  { value: 'designing', label: 'تصميم' },
  { value: 'printing', label: 'طباعة' },
  { value: 'cutting', label: 'قص' },
  { value: 'completed', label: 'مكتمل' },
  { value: 'cancelled', label: 'ملغي' },
];

const priorityOptions: { value: Priority | 'all'; label: string }[] = [
  { value: 'all', label: 'جميع الأولويات' },
  { value: 'urgent', label: 'عاجل' },
  { value: 'high', label: 'عالي' },
  { value: 'normal', label: 'عادي' },
  { value: 'low', label: 'منخفض' },
];

export default function Orders() {
  const { orders, customers, materials, addOrder, updateOrderStatus, deleteOrder } = useStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<OrderStatus | 'all'>('all');
  const [priorityFilter, setPriorityFilter] = useState<Priority | 'all'>('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [viewOrder, setViewOrder] = useState<Order | null>(null);

  const filtered = orders.filter((o) => {
    const matchSearch = !searchQuery ||
      o.orderNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
      o.customerName.includes(searchQuery);
    const matchStatus = statusFilter === 'all' || o.status === statusFilter;
    const matchPriority = priorityFilter === 'all' || o.priority === priorityFilter;
    return matchSearch && matchStatus && matchPriority;
  }).sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());

  return (
    <div>
      <PageHeader
        title="الطلبات"
        subtitle={`${orders.length} طلب إجمالاً`}
        actions={
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 text-sm font-medium"
          >
            <Plus size={16} /> طلب جديد
          </button>
        }
      />

      {/* Filters */}
      <div className="bg-white border-b border-gray-200 px-6 py-3 flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-48">
          <Search size={15} className="absolute top-1/2 -translate-y-1/2 right-3 text-gray-400" />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="بحث بالاسم أو رقم الطلب..."
            className="w-full border border-gray-300 rounded-lg pr-9 pl-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as OrderStatus | 'all')}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          {statusOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value as Priority | 'all')}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          {priorityOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <div className="text-sm text-gray-500">{filtered.length} نتيجة</div>
      </div>

      {/* Table */}
      <div className="p-6">
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600 text-xs uppercase">
              <tr>
                <th className="text-right px-4 py-3 font-medium">رقم الطلب</th>
                <th className="text-right px-4 py-3 font-medium">العميل</th>
                <th className="text-right px-4 py-3 font-medium">الحالة</th>
                <th className="text-right px-4 py-3 font-medium">الأولوية</th>
                <th className="text-right px-4 py-3 font-medium">تاريخ الإنشاء</th>
                <th className="text-right px-4 py-3 font-medium">تاريخ التسليم</th>
                <th className="text-right px-4 py-3 font-medium">المبلغ</th>
                <th className="text-right px-4 py-3 font-medium">إجراءات</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((order) => (
                <tr key={order.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-mono font-medium text-indigo-700">{order.orderNumber}</td>
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">{order.customerName}</div>
                    <div className="text-xs text-gray-500">{order.items.length} عنصر</div>
                  </td>
                  <td className="px-4 py-3">
                    <StatusDropdown
                      orderId={order.id}
                      status={order.status}
                      onChange={updateOrderStatus}
                    />
                  </td>
                  <td className="px-4 py-3">
                    <Badge className={getPriorityColor(order.priority)}>
                      {getPriorityLabel(order.priority)}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{formatDate(order.createdAt)}</td>
                  <td className="px-4 py-3">
                    {order.dueDate ? (
                      <span className={`text-sm ${new Date() > order.dueDate && order.status !== 'completed' ? 'text-red-600 font-medium' : 'text-gray-600'}`}>
                        {formatDate(order.dueDate)}
                      </span>
                    ) : <span className="text-gray-400">—</span>}
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-semibold text-gray-900">{formatCurrency(order.totalAmount)}</div>
                    {order.depositAmount < order.totalAmount && (
                      <div className="text-xs text-orange-600">متبقي: {formatCurrency(order.totalAmount - order.depositAmount)}</div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1">
                      <button onClick={() => setViewOrder(order)} className="p-1.5 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded" title="عرض">
                        <Eye size={14} />
                      </button>
                      <button onClick={() => deleteOrder(order.id)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded" title="حذف">
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={8} className="text-center py-12 text-gray-400">
                    لا توجد طلبات مطابقة للبحث
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Order Modal */}
      <AddOrderModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        customers={customers}
        materials={materials}
        onAdd={(data) => { addOrder(data); setShowAddModal(false); }}
      />

      {/* View Order Modal */}
      {viewOrder && (
        <Modal isOpen={!!viewOrder} onClose={() => setViewOrder(null)} title={`تفاصيل الطلب - ${viewOrder.orderNumber}`} size="lg">
          <OrderDetails order={viewOrder} />
        </Modal>
      )}
    </div>
  );
}

function StatusDropdown({ orderId, status, onChange }: {
  orderId: string;
  status: OrderStatus;
  onChange: (id: string, status: OrderStatus) => void;
}) {
  const [open, setOpen] = useState(false);
  const statuses: OrderStatus[] = ['pending', 'designing', 'printing', 'cutting', 'completed', 'cancelled'];

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className={`flex items-center gap-1 text-xs px-2.5 py-1 rounded-full font-medium ${getStatusColor(status)}`}
      >
        {getStatusLabel(status)} <ChevronDown size={10} />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute top-full mt-1 right-0 z-20 bg-white rounded-lg shadow-lg border border-gray-200 py-1 min-w-32">
            {statuses.map((s) => (
              <button
                key={s}
                onClick={() => { onChange(orderId, s); setOpen(false); }}
                className={`w-full text-right px-3 py-1.5 text-xs hover:bg-gray-50 flex items-center gap-2 ${s === status ? 'font-bold' : ''}`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${getStatusColor(s).split(' ')[0]}`} />
                {getStatusLabel(s)}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function OrderDetails({ order }: { order: Order }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <InfoField label="رقم الطلب" value={order.orderNumber} />
        <InfoField label="العميل" value={order.customerName} />
        <InfoField label="الحالة" value={getStatusLabel(order.status)} />
        <InfoField label="الأولوية" value={getPriorityLabel(order.priority)} />
        <InfoField label="تاريخ الإنشاء" value={formatDate(order.createdAt)} />
        <InfoField label="تاريخ التسليم" value={order.dueDate ? formatDate(order.dueDate) : '—'} />
        <InfoField label="إجمالي المبلغ" value={formatCurrency(order.totalAmount)} />
        <InfoField label="المبلغ المدفوع" value={formatCurrency(order.depositAmount)} />
      </div>

      <div>
        <h4 className="font-semibold text-gray-900 mb-3">العناصر المطلوبة</h4>
        <div className="space-y-2">
          {order.items.map((item) => (
            <div key={item.id} className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-gray-900">{item.name}</span>
                <span className="text-sm text-gray-600">× {item.quantity}</span>
              </div>
              <div className="text-xs text-gray-500 flex flex-wrap gap-2">
                <span>المادة: {item.materialName}</span>
                <span>الأبعاد: {item.width}×{item.height} سم</span>
                <span>النوع: {getJobTypeLabel(item.jobType)}</span>
                <span>السعر: {formatCurrency(item.unitPrice)}/قطعة</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {order.notes && (
        <div className="bg-blue-50 rounded-lg p-3">
          <div className="text-xs font-medium text-blue-700 mb-1">ملاحظات</div>
          <div className="text-sm text-blue-900">{order.notes}</div>
        </div>
      )}
    </div>
  );
}

function InfoField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs text-gray-500 mb-0.5">{label}</div>
      <div className="text-sm font-medium text-gray-900">{value}</div>
    </div>
  );
}

function AddOrderModal({ isOpen, onClose, customers, materials, onAdd }: {
  isOpen: boolean;
  onClose: () => void;
  customers: Array<{ id: string; name: string }>;
  materials: Array<{ id: string; name: string }>;
  onAdd: (data: any) => void;
}) {
  const [form, setForm] = useState({
    customerId: '',
    priority: 'normal' as Priority,
    status: 'pending' as OrderStatus,
    dueDate: '',
    notes: '',
    depositAmount: 0,
    itemName: '',
    itemQty: 1,
    itemWidth: 10,
    itemHeight: 10,
    itemMaterialId: '',
    itemJobType: 'print_cut',
    itemUnitPrice: 10,
  });

  const customerName = customers.find((c) => c.id === form.customerId)?.name ?? '';
  const materialName = materials.find((m) => m.id === form.itemMaterialId)?.name ?? '';
  const totalAmount = form.itemQty * form.itemUnitPrice;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.customerId || !form.itemName || !form.itemMaterialId) return;
    onAdd({
      customerId: form.customerId,
      customerName,
      priority: form.priority,
      status: form.status,
      dueDate: form.dueDate ? new Date(form.dueDate) : undefined,
      notes: form.notes,
      depositAmount: form.depositAmount,
      totalAmount,
      items: [{
        id: generateId(),
        name: form.itemName,
        quantity: form.itemQty,
        width: form.itemWidth,
        height: form.itemHeight,
        materialId: form.itemMaterialId,
        materialName,
        jobType: form.itemJobType as any,
        unitPrice: form.itemUnitPrice,
      }],
    });
  };

  const field = (label: string, el: React.ReactNode) => (
    <div>
      <label className="block text-xs font-medium text-gray-700 mb-1">{label}</label>
      {el}
    </div>
  );

  const inputClass = "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500";

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="إضافة طلب جديد" size="lg">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          {field('العميل *', (
            <select value={form.customerId} onChange={(e) => setForm({ ...form, customerId: e.target.value })} className={inputClass} required>
              <option value="">اختر العميل</option>
              {customers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          ))}
          {field('الأولوية', (
            <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value as Priority })} className={inputClass}>
              <option value="low">منخفض</option>
              <option value="normal">عادي</option>
              <option value="high">عالي</option>
              <option value="urgent">عاجل</option>
            </select>
          ))}
          {field('تاريخ التسليم', (
            <input type="date" value={form.dueDate} onChange={(e) => setForm({ ...form, dueDate: e.target.value })} className={inputClass} />
          ))}
          {field('المبلغ المدفوع (ريال)', (
            <input type="number" min="0" value={form.depositAmount} onChange={(e) => setForm({ ...form, depositAmount: +e.target.value })} className={inputClass} />
          ))}
        </div>

        <div className="border-t pt-4">
          <h4 className="font-medium text-gray-900 mb-3 text-sm">تفاصيل العنصر</h4>
          <div className="grid grid-cols-2 gap-3">
            {field('اسم العنصر *', (
              <input value={form.itemName} onChange={(e) => setForm({ ...form, itemName: e.target.value })} placeholder="مثال: ملصقات لوجو" className={inputClass} required />
            ))}
            {field('المادة *', (
              <select value={form.itemMaterialId} onChange={(e) => setForm({ ...form, itemMaterialId: e.target.value })} className={inputClass} required>
                <option value="">اختر المادة</option>
                {materials.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
              </select>
            ))}
            {field('نوع المهمة', (
              <select value={form.itemJobType} onChange={(e) => setForm({ ...form, itemJobType: e.target.value })} className={inputClass}>
                <option value="print_cut">طباعة وقص</option>
                <option value="print">طباعة فقط</option>
                <option value="cut">قص فقط</option>
              </select>
            ))}
            {field('الكمية', (
              <input type="number" min="1" value={form.itemQty} onChange={(e) => setForm({ ...form, itemQty: +e.target.value })} className={inputClass} />
            ))}
            {field('العرض (سم)', (
              <input type="number" min="1" value={form.itemWidth} onChange={(e) => setForm({ ...form, itemWidth: +e.target.value })} className={inputClass} />
            ))}
            {field('الارتفاع (سم)', (
              <input type="number" min="1" value={form.itemHeight} onChange={(e) => setForm({ ...form, itemHeight: +e.target.value })} className={inputClass} />
            ))}
            {field('سعر الوحدة (ريال)', (
              <input type="number" min="0" step="0.5" value={form.itemUnitPrice} onChange={(e) => setForm({ ...form, itemUnitPrice: +e.target.value })} className={inputClass} />
            ))}
          </div>
        </div>

        {field('ملاحظات', (
          <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} rows={2} placeholder="أي ملاحظات إضافية..." className={inputClass} />
        ))}

        <div className="bg-indigo-50 rounded-lg p-3 flex justify-between items-center">
          <span className="text-sm text-indigo-700">إجمالي الطلب:</span>
          <span className="text-lg font-bold text-indigo-800">{formatCurrency(totalAmount)}</span>
        </div>

        <div className="flex gap-2 justify-end">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium">
            إلغاء
          </button>
          <button type="submit" className="px-4 py-2 text-sm text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium">
            إضافة الطلب
          </button>
        </div>
      </form>
    </Modal>
  );
}
