import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, Image, X } from 'lucide-react';
import Header from '../components/Header';
import { useApp } from '../context/AppContext';
import { materials, jobTypes } from '../data/initialData';

const resolutions = [
  { value: 360, label: '360 DPI - اقتصادي' },
  { value: 720, label: '720 DPI - قياسي' },
  { value: 1440, label: '1440 DPI - عالي الجودة' },
  { value: 2880, label: '2880 DPI - فائق الجودة' },
];

export default function NewJob() {
  const { state, dispatch, notify } = useApp();
  const navigate = useNavigate();
  const [dragActive, setDragActive] = useState(false);

  const [form, setForm] = useState({
    name: '',
    client: '',
    type: 'print',
    priority: 'medium',
    material: 'vinyl',
    width: '',
    height: '',
    unit: 'cm',
    copies: 1,
    colorMode: 'cmyk',
    resolution: 720,
    notes: '',
    price: '',
    file: null,
    fileName: '',
    fileSize: '',
    cutSpeed: 50,
    cutPressure: 50,
    bleed: 0,
    mirror: false,
    laminate: false,
  });

  const handleChange = (field, value) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const handleFileDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer?.files?.[0] || e.target?.files?.[0];
    if (file) {
      handleChange('file', file);
      handleChange('fileName', file.name);
      handleChange('fileSize', (file.size / (1024 * 1024)).toFixed(1) + ' MB');
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.name || !form.client || !form.width || !form.height) {
      notify('يرجى ملء جميع الحقول المطلوبة', 'error');
      return;
    }

    dispatch({
      type: 'ADD_JOB',
      payload: {
        ...form,
        status: 'queued',
        completedAt: null,
        width: Number(form.width),
        height: Number(form.height),
        copies: Number(form.copies),
        price: Number(form.price) || 0,
        file: form.fileName,
      },
    });

    notify('تم إنشاء المهمة بنجاح');
    navigate('/jobs');
  };

  const showCutSettings = form.type === 'cut' || form.type === 'print_cut';
  const showPrintSettings = form.type === 'print' || form.type === 'print_cut';

  return (
    <div>
      <Header title="مهمة جديدة" subtitle="إنشاء مهمة طباعة أو قص جديدة" />

      <form onSubmit={handleSubmit} className="p-6 max-w-5xl">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main info */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
              <h3 className="text-base font-bold text-gray-900 mb-4">المعلومات الأساسية</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">اسم المهمة *</label>
                  <input
                    type="text"
                    value={form.name}
                    onChange={(e) => handleChange('name', e.target.value)}
                    placeholder="مثال: لوحة إعلانية - شركة النور"
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">العميل *</label>
                  <select
                    value={form.client}
                    onChange={(e) => handleChange('client', e.target.value)}
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
                    required
                  >
                    <option value="">اختر العميل</option>
                    {state.clients.map(c => (
                      <option key={c.id} value={c.name}>{c.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">نوع المهمة</label>
                  <select
                    value={form.type}
                    onChange={(e) => handleChange('type', e.target.value)}
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
                  >
                    {jobTypes.map(t => (
                      <option key={t.id} value={t.id}>{t.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">الأولوية</label>
                  <select
                    value={form.priority}
                    onChange={(e) => handleChange('priority', e.target.value)}
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
                  >
                    <option value="low">منخفض</option>
                    <option value="medium">متوسط</option>
                    <option value="high">عالي</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">المادة</label>
                  <select
                    value={form.material}
                    onChange={(e) => handleChange('material', e.target.value)}
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
                  >
                    {materials.map(m => (
                      <option key={m.id} value={m.id}>{m.name} ({m.nameEn})</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
              <h3 className="text-base font-bold text-gray-900 mb-4">الأبعاد والنسخ</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">العرض *</label>
                  <input
                    type="number"
                    value={form.width}
                    onChange={(e) => handleChange('width', e.target.value)}
                    placeholder="0"
                    min="0"
                    step="0.1"
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">الارتفاع *</label>
                  <input
                    type="number"
                    value={form.height}
                    onChange={(e) => handleChange('height', e.target.value)}
                    placeholder="0"
                    min="0"
                    step="0.1"
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">الوحدة</label>
                  <select
                    value={form.unit}
                    onChange={(e) => handleChange('unit', e.target.value)}
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
                  >
                    <option value="cm">سنتيمتر (cm)</option>
                    <option value="mm">مليمتر (mm)</option>
                    <option value="m">متر (m)</option>
                    <option value="in">إنش (in)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">عدد النسخ</label>
                  <input
                    type="number"
                    value={form.copies}
                    onChange={(e) => handleChange('copies', e.target.value)}
                    min="1"
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              </div>
            </div>

            {showPrintSettings && (
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 animate-fade-in">
                <h3 className="text-base font-bold text-gray-900 mb-4">إعدادات الطباعة</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">نظام الألوان</label>
                    <select
                      value={form.colorMode}
                      onChange={(e) => handleChange('colorMode', e.target.value)}
                      className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
                    >
                      <option value="cmyk">CMYK</option>
                      <option value="rgb">RGB</option>
                      <option value="grayscale">تدرج رمادي</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">الدقة</label>
                    <select
                      value={form.resolution}
                      onChange={(e) => handleChange('resolution', Number(e.target.value))}
                      className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
                    >
                      {resolutions.map(r => (
                        <option key={r.value} value={r.value}>{r.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">هامش النزيف (Bleed) - مم</label>
                    <input
                      type="number"
                      value={form.bleed}
                      onChange={(e) => handleChange('bleed', e.target.value)}
                      min="0"
                      max="20"
                      className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                  </div>
                  <div className="flex items-center gap-6 pt-6">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={form.mirror}
                        onChange={(e) => handleChange('mirror', e.target.checked)}
                        className="w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                      />
                      <span className="text-sm text-gray-700">انعكاس (Mirror)</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={form.laminate}
                        onChange={(e) => handleChange('laminate', e.target.checked)}
                        className="w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                      />
                      <span className="text-sm text-gray-700">تغليف (Laminate)</span>
                    </label>
                  </div>
                </div>
              </div>
            )}

            {showCutSettings && (
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 animate-fade-in">
                <h3 className="text-base font-bold text-gray-900 mb-4">إعدادات القص</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                      سرعة القص: {form.cutSpeed}%
                    </label>
                    <input
                      type="range"
                      value={form.cutSpeed}
                      onChange={(e) => handleChange('cutSpeed', Number(e.target.value))}
                      min="1"
                      max="100"
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
                    />
                    <div className="flex justify-between text-xs text-gray-400 mt-1">
                      <span>بطيء</span>
                      <span>سريع</span>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                      ضغط القص: {form.cutPressure}%
                    </label>
                    <input
                      type="range"
                      value={form.cutPressure}
                      onChange={(e) => handleChange('cutPressure', Number(e.target.value))}
                      min="1"
                      max="100"
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
                    />
                    <div className="flex justify-between text-xs text-gray-400 mt-1">
                      <span>خفيف</span>
                      <span>قوي</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
              <h3 className="text-base font-bold text-gray-900 mb-4">ملاحظات</h3>
              <textarea
                value={form.notes}
                onChange={(e) => handleChange('notes', e.target.value)}
                placeholder="أضف أي ملاحظات خاصة بالمهمة..."
                rows={3}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
              />
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
              <h3 className="text-base font-bold text-gray-900 mb-4">رفع الملف</h3>
              <div
                className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors cursor-pointer ${
                  dragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-200 hover:border-gray-300'
                }`}
                onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
                onDragLeave={() => setDragActive(false)}
                onDrop={handleFileDrop}
                onClick={() => document.getElementById('file-input').click()}
              >
                <input
                  id="file-input"
                  type="file"
                  className="hidden"
                  accept=".pdf,.ai,.eps,.svg,.png,.jpg,.jpeg,.tiff,.psd"
                  onChange={handleFileDrop}
                />
                {form.fileName ? (
                  <div className="animate-fade-in">
                    <FileText className="w-10 h-10 text-primary-500 mx-auto mb-2" />
                    <p className="text-sm font-semibold text-gray-900">{form.fileName}</p>
                    <p className="text-xs text-gray-500 mt-1">{form.fileSize}</p>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleChange('file', null);
                        handleChange('fileName', '');
                        handleChange('fileSize', '');
                      }}
                      className="mt-2 text-xs text-danger-500 hover:text-danger-700"
                    >
                      إزالة الملف
                    </button>
                  </div>
                ) : (
                  <>
                    <Upload className="w-10 h-10 text-gray-300 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">اسحب الملف هنا أو انقر للرفع</p>
                    <p className="text-xs text-gray-400 mt-1">PDF, AI, EPS, SVG, PNG, JPG, TIFF, PSD</p>
                  </>
                )}
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
              <h3 className="text-base font-bold text-gray-900 mb-4">التسعير</h3>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">السعر (ر.س)</label>
                <input
                  type="number"
                  value={form.price}
                  onChange={(e) => handleChange('price', e.target.value)}
                  placeholder="0.00"
                  min="0"
                  step="0.01"
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              {form.width && form.height && form.copies && (
                <div className="mt-4 bg-gray-50 rounded-xl p-3 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">المساحة</span>
                    <span className="font-medium text-gray-800">
                      {(Number(form.width) * Number(form.height)).toFixed(1)} {form.unit}²
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">إجمالي المساحة</span>
                    <span className="font-medium text-gray-800">
                      {(Number(form.width) * Number(form.height) * Number(form.copies)).toFixed(1)} {form.unit}²
                    </span>
                  </div>
                  {form.price && (
                    <div className="flex justify-between text-sm pt-2 border-t border-gray-200">
                      <span className="text-gray-500">سعر النسخة</span>
                      <span className="font-bold text-gray-900">
                        {(Number(form.price) / Number(form.copies)).toFixed(2)} ر.س
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                className="flex-1 px-4 py-3 bg-primary-600 text-white rounded-xl text-sm font-semibold hover:bg-primary-700 transition-colors shadow-sm"
              >
                إنشاء المهمة
              </button>
              <button
                type="button"
                onClick={() => navigate('/jobs')}
                className="px-4 py-3 bg-gray-100 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-200 transition-colors"
              >
                إلغاء
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
