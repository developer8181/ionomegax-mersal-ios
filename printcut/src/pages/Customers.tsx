import { useState } from 'react';
import { Plus, Search, Phone, Mail, MapPin, Edit, Trash2, User } from 'lucide-react';
import { useStore } from '../store/useStore';
import type { Customer } from '../types';
import { formatDate, formatCurrency } from '../utils/helpers';
import PageHeader from '../components/PageHeader';
import Modal from '../components/Modal';

export default function Customers() {
  const { customers, orders, addCustomer, updateCustomer, deleteCustomer } = useStore();
  const [search, setSearch] = useState('');
  const [showAdd, setShowAdd] = useState(false);
  const [editCustomer, setEditCustomer] = useState<Customer | null>(null);
  const [viewCustomer, setViewCustomer] = useState<Customer | null>(null);

  const filtered = customers.filter((c) =>
    !search || c.name.includes(search) || c.phone.includes(search) || c.email?.includes(search)
  );

  const getCustomerOrders = (customerId: string) =>
    orders.filter((o) => o.customerId === customerId);

  const getCustomerRevenue = (customerId: string) =>
    orders.filter((o) => o.customerId === customerId && o.status !== 'cancelled')
      .reduce((s, o) => s + o.totalAmount, 0);

  return (
    <div>
      <PageHeader
        title="العملاء"
        subtitle={`${customers.length} عميل مسجل`}
        actions={
          <button
            onClick={() => setShowAdd(true)}
            className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 text-sm font-medium"
          >
            <Plus size={16} /> عميل جديد
          </button>
        }
      />

      {/* Search */}
      <div className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="relative max-w-sm">
          <Search size={15} className="absolute top-1/2 -translate-y-1/2 right-3 text-gray-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="بحث بالاسم أو الهاتف..."
            className="w-full border border-gray-300 rounded-lg pr-9 pl-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((customer) => {
            const customerOrders = getCustomerOrders(customer.id);
            const revenue = getCustomerRevenue(customer.id);
            return (
              <div key={customer.id} className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-700 font-bold text-lg">
                      {customer.name[0]}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{customer.name}</h3>
                      <p className="text-xs text-gray-500">منذ {formatDate(customer.createdAt)}</p>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <button onClick={() => setEditCustomer(customer)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded">
                      <Edit size={13} />
                    </button>
                    <button onClick={() => deleteCustomer(customer.id)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded">
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>

                <div className="space-y-1.5 mb-3">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Phone size={13} className="text-gray-400 shrink-0" />
                    <span dir="ltr">{customer.phone}</span>
                  </div>
                  {customer.email && (
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Mail size={13} className="text-gray-400 shrink-0" />
                      <span className="truncate">{customer.email}</span>
                    </div>
                  )}
                  {customer.address && (
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <MapPin size={13} className="text-gray-400 shrink-0" />
                      <span className="truncate">{customer.address}</span>
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-2 pt-3 border-t border-gray-100">
                  <div className="text-center">
                    <div className="text-lg font-bold text-gray-900">{customerOrders.length}</div>
                    <div className="text-xs text-gray-500">طلبات</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm font-bold text-green-700">{formatCurrency(revenue)}</div>
                    <div className="text-xs text-gray-500">إجمالي</div>
                  </div>
                </div>

                <button
                  onClick={() => setViewCustomer(customer)}
                  className="w-full mt-3 text-sm text-indigo-600 hover:text-indigo-800 font-medium py-1.5 border border-indigo-200 rounded-lg hover:bg-indigo-50 transition-colors"
                >
                  عرض التفاصيل
                </button>
              </div>
            );
          })}

          {filtered.length === 0 && (
            <div className="col-span-3 text-center py-16 text-gray-400">
              <User size={32} className="mx-auto mb-3 opacity-50" />
              <p>لا يوجد عملاء مطابقون</p>
            </div>
          )}
        </div>
      </div>

      {/* Add/Edit Modal */}
      <CustomerFormModal
        isOpen={showAdd || !!editCustomer}
        onClose={() => { setShowAdd(false); setEditCustomer(null); }}
        customer={editCustomer}
        onSave={(data) => {
          if (editCustomer) {
            updateCustomer(editCustomer.id, data);
          } else {
            addCustomer(data as any);
          }
          setShowAdd(false);
          setEditCustomer(null);
        }}
      />

      {/* View Modal */}
      {viewCustomer && (
        <Modal isOpen={!!viewCustomer} onClose={() => setViewCustomer(null)} title={`ملف العميل — ${viewCustomer.name}`} size="lg">
          <CustomerProfile customer={viewCustomer} orders={getCustomerOrders(viewCustomer.id)} revenue={getCustomerRevenue(viewCustomer.id)} />
        </Modal>
      )}
    </div>
  );
}

function CustomerProfile({ customer, orders: custOrders, revenue }: {
  customer: Customer;
  orders: any[];
  revenue: number;
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4 bg-indigo-50 rounded-xl p-4">
        <div className="w-16 h-16 bg-indigo-600 rounded-full flex items-center justify-center text-white font-bold text-2xl">
          {customer.name[0]}
        </div>
        <div>
          <h3 className="text-xl font-bold text-gray-900">{customer.name}</h3>
          <p className="text-sm text-gray-500">{customer.address}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {customer.phone && <InfoCard label="الهاتف" value={customer.phone} icon={<Phone size={14} />} />}
        {customer.email && <InfoCard label="البريد الإلكتروني" value={customer.email} icon={<Mail size={14} />} />}
      </div>

      <div className="grid grid-cols-3 gap-3">
        <StatCard label="إجمالي الطلبات" value={custOrders.length} color="bg-blue-50 text-blue-700" />
        <StatCard label="إجمالي الإيرادات" value={formatCurrency(revenue)} color="bg-green-50 text-green-700" />
        <StatCard label="عضو منذ" value={formatDate(customer.createdAt)} color="bg-purple-50 text-purple-700" />
      </div>

      {custOrders.length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-900 mb-2">آخر الطلبات</h4>
          <div className="space-y-2">
            {custOrders.slice(0, 3).map((order: any) => (
              <div key={order.id} className="flex items-center justify-between text-sm bg-gray-50 rounded-lg px-3 py-2">
                <span className="font-mono text-indigo-600">{order.orderNumber}</span>
                <span className="text-gray-600">{formatDate(order.createdAt)}</span>
                <span className="font-semibold">{formatCurrency(order.totalAmount)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {customer.notes && (
        <div className="bg-yellow-50 rounded-lg p-3 text-sm text-yellow-900">
          <span className="font-medium">ملاحظات: </span>{customer.notes}
        </div>
      )}
    </div>
  );
}

function InfoCard({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) {
  return (
    <div className="bg-gray-50 rounded-lg p-3 flex items-center gap-2">
      <span className="text-gray-400">{icon}</span>
      <div>
        <div className="text-xs text-gray-500">{label}</div>
        <div className="text-sm font-medium text-gray-900">{value}</div>
      </div>
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className={`rounded-lg p-3 text-center ${color}`}>
      <div className="text-lg font-bold">{value}</div>
      <div className="text-xs opacity-80">{label}</div>
    </div>
  );
}

function CustomerFormModal({ isOpen, onClose, customer, onSave }: {
  isOpen: boolean;
  onClose: () => void;
  customer: Customer | null;
  onSave: (data: Partial<Customer>) => void;
}) {
  const [form, setForm] = useState({
    name: customer?.name ?? '',
    phone: customer?.phone ?? '',
    email: customer?.email ?? '',
    address: customer?.address ?? '',
    notes: customer?.notes ?? '',
  });

  const inputClass = "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500";

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name || !form.phone) return;
    onSave(form);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={customer ? 'تعديل العميل' : 'إضافة عميل جديد'} size="md">
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">الاسم *</label>
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className={inputClass} required placeholder="الاسم الكامل" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">رقم الهاتف *</label>
          <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className={inputClass} required placeholder="05xxxxxxxx" dir="ltr" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">البريد الإلكتروني</label>
          <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className={inputClass} placeholder="example@email.com" dir="ltr" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">العنوان</label>
          <input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} className={inputClass} placeholder="المدينة - الحي" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">ملاحظات</label>
          <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className={inputClass} rows={2} placeholder="أي معلومات إضافية..." />
        </div>
        <div className="flex gap-2 justify-end pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium">
            إلغاء
          </button>
          <button type="submit" className="px-4 py-2 text-sm text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium">
            {customer ? 'حفظ التعديلات' : 'إضافة العميل'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
