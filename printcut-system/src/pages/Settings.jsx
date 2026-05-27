import { useState } from 'react';
import { Save, Printer, Scissors, Palette, Globe, Building2, CreditCard } from 'lucide-react';
import Header from '../components/Header';
import { useApp } from '../context/AppContext';

export default function Settings() {
  const { notify } = useApp();

  const [settings, setSettings] = useState({
    companyName: 'PrintCut Pro',
    companyPhone: '0501234567',
    companyEmail: 'info@printcut.sa',
    companyAddress: 'الرياض، المملكة العربية السعودية',
    currency: 'SAR',
    taxRate: 15,
    defaultResolution: 720,
    defaultColorMode: 'cmyk',
    defaultMaterial: 'vinyl',
    printerName: 'Roland VG2-640',
    cutterName: 'Roland GS-24',
    printerWidth: 160,
    cutterWidth: 60,
    defaultCutSpeed: 50,
    defaultCutPressure: 50,
    autoQueue: true,
    notifications: true,
    darkMode: false,
    language: 'ar',
  });

  const handleChange = (field, value) => {
    setSettings(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    notify('تم حفظ الإعدادات بنجاح');
  };

  return (
    <div>
      <Header title="الإعدادات" subtitle="إعدادات النظام والأجهزة" />

      <div className="p-6 max-w-4xl space-y-6">
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-primary-50 flex items-center justify-center">
              <Building2 className="w-5 h-5 text-primary-600" />
            </div>
            <h3 className="text-base font-bold text-gray-900">معلومات الشركة</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">اسم الشركة</label>
              <input
                type="text"
                value={settings.companyName}
                onChange={(e) => handleChange('companyName', e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">رقم الهاتف</label>
              <input
                type="tel"
                value={settings.companyPhone}
                onChange={(e) => handleChange('companyPhone', e.target.value)}
                dir="ltr"
                className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 text-left"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">البريد الإلكتروني</label>
              <input
                type="email"
                value={settings.companyEmail}
                onChange={(e) => handleChange('companyEmail', e.target.value)}
                dir="ltr"
                className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 text-left"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">العنوان</label>
              <input
                type="text"
                value={settings.companyAddress}
                onChange={(e) => handleChange('companyAddress', e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-accent-50 flex items-center justify-center">
              <Printer className="w-5 h-5 text-accent-600" />
            </div>
            <h3 className="text-base font-bold text-gray-900">إعدادات الطابعة</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">اسم الطابعة</label>
              <input
                type="text"
                value={settings.printerName}
                onChange={(e) => handleChange('printerName', e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">عرض الطابعة (سم)</label>
              <input
                type="number"
                value={settings.printerWidth}
                onChange={(e) => handleChange('printerWidth', Number(e.target.value))}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">الدقة الافتراضية</label>
              <select
                value={settings.defaultResolution}
                onChange={(e) => handleChange('defaultResolution', Number(e.target.value))}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
              >
                <option value={360}>360 DPI</option>
                <option value={720}>720 DPI</option>
                <option value={1440}>1440 DPI</option>
                <option value={2880}>2880 DPI</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">نظام الألوان</label>
              <select
                value={settings.defaultColorMode}
                onChange={(e) => handleChange('defaultColorMode', e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
              >
                <option value="cmyk">CMYK</option>
                <option value="rgb">RGB</option>
              </select>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-purple-50 flex items-center justify-center">
              <Scissors className="w-5 h-5 text-purple-600" />
            </div>
            <h3 className="text-base font-bold text-gray-900">إعدادات القاطع</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">اسم القاطع</label>
              <input
                type="text"
                value={settings.cutterName}
                onChange={(e) => handleChange('cutterName', e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">عرض القاطع (سم)</label>
              <input
                type="number"
                value={settings.cutterWidth}
                onChange={(e) => handleChange('cutterWidth', Number(e.target.value))}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                سرعة القص الافتراضية: {settings.defaultCutSpeed}%
              </label>
              <input
                type="range"
                value={settings.defaultCutSpeed}
                onChange={(e) => handleChange('defaultCutSpeed', Number(e.target.value))}
                min="1"
                max="100"
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                ضغط القص الافتراضي: {settings.defaultCutPressure}%
              </label>
              <input
                type="range"
                value={settings.defaultCutPressure}
                onChange={(e) => handleChange('defaultCutPressure', Number(e.target.value))}
                min="1"
                max="100"
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
              />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-warning-50 flex items-center justify-center">
              <CreditCard className="w-5 h-5 text-warning-500" />
            </div>
            <h3 className="text-base font-bold text-gray-900">الفوترة والضرائب</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">العملة</label>
              <select
                value={settings.currency}
                onChange={(e) => handleChange('currency', e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
              >
                <option value="SAR">ريال سعودي (SAR)</option>
                <option value="AED">درهم إماراتي (AED)</option>
                <option value="KWD">دينار كويتي (KWD)</option>
                <option value="USD">دولار أمريكي (USD)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">نسبة الضريبة (%)</label>
              <input
                type="number"
                value={settings.taxRate}
                onChange={(e) => handleChange('taxRate', Number(e.target.value))}
                min="0"
                max="100"
                className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center">
              <Globe className="w-5 h-5 text-gray-600" />
            </div>
            <h3 className="text-base font-bold text-gray-900">إعدادات عامة</h3>
          </div>
          <div className="space-y-4">
            <label className="flex items-center justify-between p-3 bg-gray-50 rounded-xl cursor-pointer">
              <div>
                <p className="text-sm font-medium text-gray-700">إضافة تلقائية للانتظار</p>
                <p className="text-xs text-gray-500">إضافة المهام الجديدة تلقائياً لقائمة الانتظار</p>
              </div>
              <input
                type="checkbox"
                checked={settings.autoQueue}
                onChange={(e) => handleChange('autoQueue', e.target.checked)}
                className="w-5 h-5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
            </label>
            <label className="flex items-center justify-between p-3 bg-gray-50 rounded-xl cursor-pointer">
              <div>
                <p className="text-sm font-medium text-gray-700">الإشعارات</p>
                <p className="text-xs text-gray-500">تفعيل إشعارات حالة المهام</p>
              </div>
              <input
                type="checkbox"
                checked={settings.notifications}
                onChange={(e) => handleChange('notifications', e.target.checked)}
                className="w-5 h-5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
            </label>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">اللغة</label>
              <select
                value={settings.language}
                onChange={(e) => handleChange('language', e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
              >
                <option value="ar">العربية</option>
                <option value="en">English</option>
              </select>
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            onClick={handleSave}
            className="flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-xl text-sm font-semibold hover:bg-primary-700 transition-colors shadow-sm"
          >
            <Save className="w-4 h-4" />
            حفظ الإعدادات
          </button>
        </div>
      </div>
    </div>
  );
}
