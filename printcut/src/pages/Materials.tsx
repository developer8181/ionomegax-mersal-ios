import { useState } from 'react';
import { Plus, Search, Edit, Trash2, Package, AlertTriangle } from 'lucide-react';
import { useStore } from '../store/useStore';
import type { Material, MaterialType } from '../types';
import { formatCurrency, getMaterialTypeLabel } from '../utils/helpers';
import PageHeader from '../components/PageHeader';
import Modal from '../components/Modal';

const materialTypeColors: Record<MaterialType, string> = {
  vinyl: 'bg-indigo-100 text-indigo-700',
  paper: 'bg-blue-100 text-blue-700',
  canvas: 'bg-yellow-100 text-yellow-700',
  fabric: 'bg-pink-100 text-pink-700',
  pvc: 'bg-green-100 text-green-700',
  other: 'bg-gray-100 text-gray-700',
};

export default function Materials() {
  const { materials, addMaterial, updateMaterial, deleteMaterial } = useStore();
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<MaterialType | 'all'>('all');
  const [showAdd, setShowAdd] = useState(false);
  const [editMaterial, setEditMaterial] = useState<Material | null>(null);

  const filtered = materials.filter((m) => {
    const matchSearch = !search || m.name.includes(search);
    const matchType = typeFilter === 'all' || m.type === typeFilter;
    return matchSearch && matchType;
  });

  const lowStock = materials.filter((m) => m.stock < 10).length;

  return (
    <div>
      <PageHeader
        title="المواد والخامات"
        subtitle={`${materials.length} مادة مسجلة`}
        actions={
          <div className="flex items-center gap-2">
            {lowStock > 0 && (
              <div className="flex items-center gap-1.5 text-orange-700 bg-orange-50 border border-orange-200 px-3 py-2 rounded-lg text-sm">
                <AlertTriangle size={14} />
                <span>{lowStock} مادة منخفضة المخزون</span>
              </div>
            )}
            <button
              onClick={() => setShowAdd(true)}
              className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 text-sm font-medium"
            >
              <Plus size={16} /> مادة جديدة
            </button>
          </div>
        }
      />

      {/* Filters */}
      <div className="bg-white border-b border-gray-200 px-6 py-3 flex gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search size={15} className="absolute top-1/2 -translate-y-1/2 right-3 text-gray-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="بحث عن مادة..."
            className="w-full border border-gray-300 rounded-lg pr-9 pl-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div className="flex gap-2">
          {(['all', 'vinyl', 'paper', 'canvas', 'fabric', 'pvc', 'other'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTypeFilter(t)}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                typeFilter === t
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {t === 'all' ? 'الكل' : getMaterialTypeLabel(t)}
            </button>
          ))}
        </div>
      </div>

      <div className="p-6">
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600 text-xs">
              <tr>
                <th className="text-right px-4 py-3 font-medium">المادة</th>
                <th className="text-right px-4 py-3 font-medium">النوع</th>
                <th className="text-right px-4 py-3 font-medium">العرض</th>
                <th className="text-right px-4 py-3 font-medium">اللون</th>
                <th className="text-right px-4 py-3 font-medium">المخزون</th>
                <th className="text-right px-4 py-3 font-medium">السعر/وحدة</th>
                <th className="text-right px-4 py-3 font-medium">إجراءات</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((material) => (
                <tr key={material.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-5 h-5 rounded border border-gray-300"
                        style={{ backgroundColor: material.color === 'transparent' ? 'transparent' : material.color, background: material.color === 'transparent' ? 'repeating-conic-gradient(#ccc 0% 25%, white 0% 50%) 0 0 / 8px 8px' : material.color }}
                      />
                      <span className="font-medium text-gray-900">{material.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${materialTypeColors[material.type]}`}>
                      {getMaterialTypeLabel(material.type)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{material.width} {material.unit}</td>
                  <td className="px-4 py-3 text-gray-600">{material.color}</td>
                  <td className="px-4 py-3">
                    <span className={`font-medium ${material.stock < 10 ? 'text-red-600' : material.stock < 20 ? 'text-orange-500' : 'text-gray-900'}`}>
                      {material.stock} {material.stockUnit}
                    </span>
                    {material.stock < 10 && (
                      <span className="mr-1 text-xs text-red-500">⚠️ منخفض</span>
                    )}
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-900">{formatCurrency(material.pricePerUnit)}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      <button onClick={() => setEditMaterial(material)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded">
                        <Edit size={13} />
                      </button>
                      <button onClick={() => deleteMaterial(material.id)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded">
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className="text-center py-12">
                    <Package size={28} className="mx-auto mb-2 text-gray-300" />
                    <p className="text-gray-400">لا توجد مواد مطابقة</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Stock Summary */}
        <div className="mt-4 grid grid-cols-3 gap-3">
          {(['vinyl', 'paper', 'canvas'] as MaterialType[]).map((type) => {
            const typeMatls = materials.filter((m) => m.type === type);
            const totalStock = typeMatls.reduce((s, m) => s + m.stock, 0);
            return (
              <div key={type} className={`rounded-xl p-4 ${materialTypeColors[type].replace('text-', 'bg-').split(' ')[0]} bg-opacity-20`}>
                <div className="text-sm font-semibold text-gray-900">{getMaterialTypeLabel(type)}</div>
                <div className="text-2xl font-bold text-gray-900 mt-1">{totalStock}</div>
                <div className="text-xs text-gray-500">{typeMatls.length} نوع مختلف</div>
              </div>
            );
          })}
        </div>
      </div>

      <MaterialFormModal
        isOpen={showAdd || !!editMaterial}
        onClose={() => { setShowAdd(false); setEditMaterial(null); }}
        material={editMaterial}
        onSave={(data) => {
          if (editMaterial) {
            updateMaterial(editMaterial.id, data);
          } else {
            addMaterial(data as any);
          }
          setShowAdd(false);
          setEditMaterial(null);
        }}
      />
    </div>
  );
}

function MaterialFormModal({ isOpen, onClose, material, onSave }: {
  isOpen: boolean;
  onClose: () => void;
  material: Material | null;
  onSave: (data: Partial<Material>) => void;
}) {
  const [form, setForm] = useState<Partial<Material>>(material ?? {
    name: '',
    type: 'vinyl',
    width: 120,
    height: 0,
    unit: 'cm',
    color: '#FFFFFF',
    stock: 10,
    stockUnit: 'متر',
    pricePerUnit: 25,
    notes: '',
  });

  const inputClass = "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500";

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name) return;
    onSave(form);
  };

  const field = (label: string, el: React.ReactNode, required = false) => (
    <div>
      <label className="block text-xs font-medium text-gray-700 mb-1">{label}{required && ' *'}</label>
      {el}
    </div>
  );

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={material ? 'تعديل المادة' : 'إضافة مادة جديدة'} size="md">
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          {field('اسم المادة', <input value={form.name ?? ''} onChange={(e) => setForm({ ...form, name: e.target.value })} className={inputClass} placeholder="مثال: فينيل أبيض لامع" required />, true)}
          {field('النوع', (
            <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value as MaterialType })} className={inputClass}>
              {(['vinyl', 'paper', 'canvas', 'fabric', 'pvc', 'other'] as MaterialType[]).map((t) => (
                <option key={t} value={t}>{getMaterialTypeLabel(t)}</option>
              ))}
            </select>
          ))}
          {field('العرض', <input type="number" value={form.width ?? ''} onChange={(e) => setForm({ ...form, width: +e.target.value })} className={inputClass} placeholder="120" />)}
          {field('الوحدة', (
            <select value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value as any })} className={inputClass}>
              <option value="cm">سم</option>
              <option value="mm">مم</option>
              <option value="inch">بوصة</option>
            </select>
          ))}
          {field('اللون', (
            <div className="flex gap-2">
              <input type="color" value={form.color === 'transparent' ? '#FFFFFF' : (form.color ?? '#FFFFFF')} onChange={(e) => setForm({ ...form, color: e.target.value })} className="w-10 h-9 rounded border border-gray-300 cursor-pointer" />
              <input value={form.color ?? ''} onChange={(e) => setForm({ ...form, color: e.target.value })} className={`flex-1 ${inputClass}`} placeholder="#FFFFFF" />
            </div>
          ))}
          {field('المخزون الحالي', <input type="number" value={form.stock ?? ''} onChange={(e) => setForm({ ...form, stock: +e.target.value })} className={inputClass} />)}
          {field('وحدة المخزون', <input value={form.stockUnit ?? ''} onChange={(e) => setForm({ ...form, stockUnit: e.target.value })} className={inputClass} placeholder="متر / لفة / قطعة" />)}
          {field('السعر/وحدة (ريال)', <input type="number" step="0.5" value={form.pricePerUnit ?? ''} onChange={(e) => setForm({ ...form, pricePerUnit: +e.target.value })} className={inputClass} />)}
        </div>
        {field('ملاحظات', <textarea value={form.notes ?? ''} onChange={(e) => setForm({ ...form, notes: e.target.value })} className={inputClass} rows={2} />)}

        <div className="flex gap-2 justify-end pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium">
            إلغاء
          </button>
          <button type="submit" className="px-4 py-2 text-sm text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium">
            {material ? 'حفظ' : 'إضافة'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
