import { useState } from 'react';
import { Play, CheckCircle, XCircle, Clock, Scissors, MoreVertical, Settings } from 'lucide-react';
import { useStore } from '../store/useStore';
import type { CutJob } from '../types';
import { formatDateTime, getPriorityColor, getPriorityLabel } from '../utils/helpers';
import PageHeader from '../components/PageHeader';
import Modal from '../components/Modal';

const statusConfig = {
  queued: { label: 'في الطابور', color: 'bg-gray-100 text-gray-700', icon: Clock },
  cutting: { label: 'جارية القص', color: 'bg-orange-100 text-orange-700', icon: Scissors },
  done: { label: 'مكتملة', color: 'bg-green-100 text-green-700', icon: CheckCircle },
  failed: { label: 'فشلت', color: 'bg-red-100 text-red-700', icon: XCircle },
};

export default function CutQueue() {
  const { cutQueue, updateCutJob, removeCutJob } = useStore();
  const [activeTab, setActiveTab] = useState<'cutting' | 'queued' | 'done' | 'failed'>('cutting');
  const [settingsJob, setSettingsJob] = useState<CutJob | null>(null);

  const byStatus = {
    queued: cutQueue.filter((j) => j.status === 'queued'),
    cutting: cutQueue.filter((j) => j.status === 'cutting'),
    done: cutQueue.filter((j) => j.status === 'done'),
    failed: cutQueue.filter((j) => j.status === 'failed'),
  };

  const startJob = (id: string) =>
    updateCutJob(id, { status: 'cutting', startedAt: new Date() });
  const completeJob = (id: string) =>
    updateCutJob(id, { status: 'done', completedAt: new Date() });
  const failJob = (id: string) =>
    updateCutJob(id, { status: 'failed' });
  const requeueJob = (id: string) =>
    updateCutJob(id, { status: 'queued', startedAt: undefined, completedAt: undefined });

  const tabs = (['cutting', 'queued', 'done', 'failed'] as const);

  return (
    <div>
      <PageHeader
        title="طابور القص"
        subtitle={`${cutQueue.length} مهمة إجمالاً`}
        actions={
          <div className="flex items-center gap-2 text-sm">
            <div className="flex items-center gap-1.5 text-orange-700 bg-orange-50 border border-orange-200 px-3 py-1.5 rounded-lg">
              <Scissors size={14} />
              <span>{byStatus.cutting.length} جارية الآن</span>
            </div>
          </div>
        }
      />

      {/* Machine Status Bar */}
      <div className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex items-center gap-6 text-sm">
          <MachineStatus name="Graphtec CE7000" status={byStatus.cutting.length > 0 ? 'cutting' : 'idle'} speed={byStatus.cutting[0]?.cuttingSpeed} pressure={byStatus.cutting[0]?.pressure} />
          <MachineStatus name="Roland GS-24" status="idle" />
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200 px-6">
        <div className="flex gap-0">
          {tabs.map((tab) => {
            const cfg = statusConfig[tab];
            const Icon = cfg.icon;
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <Icon size={14} />
                {cfg.label}
                <span className={`text-xs px-1.5 py-0.5 rounded-full ${byStatus[tab].length > 0 ? cfg.color : 'bg-gray-100 text-gray-500'}`}>
                  {byStatus[tab].length}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="p-6">
        {/* Active cutting jobs */}
        {activeTab === 'cutting' && byStatus.cutting.length > 0 && (
          <div className="mb-6 space-y-3">
            {byStatus.cutting.map((job) => (
              <ActiveCutCard key={job.id} job={job} onComplete={() => completeJob(job.id)} onFail={() => failJob(job.id)} />
            ))}
          </div>
        )}

        <div className="grid grid-cols-1 gap-3">
          {byStatus[activeTab].map((job, idx) => (
            <CutJobCard
              key={job.id}
              job={job}
              index={idx}
              onStart={() => startJob(job.id)}
              onComplete={() => completeJob(job.id)}
              onFail={() => failJob(job.id)}
              onRequeue={() => requeueJob(job.id)}
              onRemove={() => removeCutJob(job.id)}
              onSettings={() => setSettingsJob(job)}
            />
          ))}
          {byStatus[activeTab].length === 0 && (
            <div className="text-center py-16 text-gray-400 bg-white rounded-xl border border-gray-200">
              <Scissors size={32} className="mx-auto mb-3 opacity-50" />
              <p>لا توجد مهام في هذا القسم</p>
            </div>
          )}
        </div>
      </div>

      {/* Settings Modal */}
      {settingsJob && (
        <Modal isOpen={!!settingsJob} onClose={() => setSettingsJob(null)} title="إعدادات القص" size="sm">
          <CutSettings
            job={settingsJob}
            onSave={(data) => { updateCutJob(settingsJob.id, data); setSettingsJob(null); }}
          />
        </Modal>
      )}
    </div>
  );
}

function MachineStatus({ name, status, speed, pressure }: {
  name: string;
  status: 'cutting' | 'idle';
  speed?: number;
  pressure?: number;
}) {
  return (
    <div className="flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full ${status === 'cutting' ? 'bg-orange-500 animate-pulse' : 'bg-gray-300'}`} />
      <span className="font-medium text-gray-700">{name}</span>
      <span className={`text-xs px-2 py-0.5 rounded-full ${status === 'cutting' ? 'bg-orange-100 text-orange-700' : 'bg-gray-100 text-gray-500'}`}>
        {status === 'cutting' ? 'يعمل' : 'خامل'}
      </span>
      {speed && <span className="text-xs text-gray-400">السرعة: {speed}</span>}
      {pressure && <span className="text-xs text-gray-400">الضغط: {pressure}g</span>}
    </div>
  );
}

function ActiveCutCard({ job, onComplete, onFail }: {
  job: CutJob;
  onComplete: () => void;
  onFail: () => void;
}) {
  const progress = Math.floor(Math.random() * 60) + 20;
  return (
    <div className="bg-orange-50 border border-orange-200 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-orange-500 animate-pulse" />
          <div>
            <span className="font-semibold text-orange-900">{job.itemName}</span>
            <span className="text-sm text-orange-700 mr-2">— {job.customerName}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={onComplete} className="flex items-center gap-1 text-xs text-green-700 bg-green-100 hover:bg-green-200 px-3 py-1.5 rounded-lg font-medium">
            <CheckCircle size={12} /> اكتمل
          </button>
          <button onClick={onFail} className="flex items-center gap-1 text-xs text-red-700 bg-red-100 hover:bg-red-200 px-3 py-1.5 rounded-lg font-medium">
            <XCircle size={12} /> فشل
          </button>
        </div>
      </div>
      <div className="mb-2 flex items-center justify-between text-xs text-orange-700">
        <span>التقدم: {progress}%</span>
        <span>{job.cutter || 'الجهاز الافتراضي'} · سرعة: {job.cuttingSpeed ?? 40} · ضغط: {job.pressure ?? 80}g</span>
      </div>
      <div className="w-full bg-orange-200 rounded-full h-2">
        <div className="bg-orange-500 h-2 rounded-full transition-all" style={{ width: `${progress}%` }} />
      </div>
      <div className="mt-2 text-xs text-orange-600">
        {job.orderNumber} · {job.quantity} قطعة · {job.width}×{job.height} سم · {job.materialName}
      </div>
    </div>
  );
}

function CutJobCard({ job, index, onStart, onComplete, onRequeue, onRemove, onSettings }: {
  job: CutJob;
  index: number;
  onStart: () => void;
  onComplete: () => void;
  onFail?: () => void;
  onRequeue: () => void;
  onRemove: () => void;
  onSettings: () => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-sm transition-shadow">
      <div className="flex items-start gap-4">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold shrink-0 ${
          job.priority === 'urgent' ? 'bg-red-100 text-red-700' :
          job.priority === 'high' ? 'bg-orange-100 text-orange-700' :
          'bg-gray-100 text-gray-700'
        }`}>
          {index + 1}
        </div>

        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <div>
              <span className="font-semibold text-gray-900">{job.itemName}</span>
              <span className="text-sm text-gray-500 mr-2">· {job.customerName}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${getPriorityColor(job.priority)}`}>
                {getPriorityLabel(job.priority)}
              </span>
              <button onClick={onSettings} title="إعدادات القص" className="p-1 text-gray-400 hover:text-orange-600 rounded">
                <Settings size={14} />
              </button>
              <div className="relative">
                <button onClick={() => setMenuOpen(!menuOpen)} className="p-1 text-gray-400 hover:text-gray-600 rounded">
                  <MoreVertical size={14} />
                </button>
                {menuOpen && (
                  <>
                    <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
                    <div className="absolute top-full left-0 z-20 bg-white rounded-lg shadow-lg border border-gray-200 py-1 min-w-32">
                      {job.status === 'queued' && <MenuItem label="بدء القص" onClick={() => { onStart(); setMenuOpen(false); }} />}
                      {job.status === 'cutting' && <MenuItem label="تم الاكتمال" onClick={() => { onComplete(); setMenuOpen(false); }} />}
                      {(job.status === 'done' || job.status === 'failed') && <MenuItem label="إعادة الإضافة" onClick={() => { onRequeue(); setMenuOpen(false); }} />}
                      <MenuItem label="إزالة" onClick={() => { onRemove(); setMenuOpen(false); }} danger />
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-3 text-xs text-gray-500">
            <span className="bg-gray-50 px-2 py-1 rounded"># {job.orderNumber}</span>
            <span className="bg-gray-50 px-2 py-1 rounded">الكمية: {job.quantity}</span>
            <span className="bg-gray-50 px-2 py-1 rounded">الحجم: {job.width}×{job.height} سم</span>
            <span className="bg-gray-50 px-2 py-1 rounded">المادة: {job.materialName}</span>
            {job.cutter && <span className="bg-orange-50 text-orange-700 px-2 py-1 rounded">الجهاز: {job.cutter}</span>}
            {job.cuttingSpeed && <span className="bg-blue-50 text-blue-700 px-2 py-1 rounded">سرعة: {job.cuttingSpeed}</span>}
            {job.pressure && <span className="bg-green-50 text-green-700 px-2 py-1 rounded">ضغط: {job.pressure}g</span>}
          </div>

          <div className="mt-2 text-xs text-gray-400">
            أُضيف: {formatDateTime(job.createdAt)}
            {job.completedAt && ` · اكتمل: ${formatDateTime(job.completedAt)}`}
          </div>
        </div>

        {job.status === 'queued' && (
          <button onClick={onStart} className="flex items-center gap-1.5 text-xs text-white bg-orange-500 hover:bg-orange-600 px-3 py-2 rounded-lg font-medium shrink-0">
            <Play size={12} /> بدء
          </button>
        )}
      </div>
    </div>
  );
}

function CutSettings({ job, onSave }: { job: CutJob; onSave: (data: Partial<CutJob>) => void }) {
  const [speed, setSpeed] = useState(job.cuttingSpeed ?? 40);
  const [pressure, setPressure] = useState(job.pressure ?? 80);
  const [cutter, setCutter] = useState(job.cutter ?? 'Graphtec CE7000');

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">جهاز القص</label>
        <select value={cutter} onChange={(e) => setCutter(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
          <option>Graphtec CE7000</option>
          <option>Roland GS-24</option>
          <option>Mimaki CJV150</option>
          <option>Silhouette Cameo</option>
        </select>
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">سرعة القص: {speed}</label>
        <input type="range" min="1" max="100" value={speed} onChange={(e) => setSpeed(+e.target.value)} className="w-full" />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">ضغط النصل (g): {pressure}</label>
        <input type="range" min="10" max="350" value={pressure} onChange={(e) => setPressure(+e.target.value)} className="w-full" />
      </div>
      <div className="grid grid-cols-3 gap-2 text-xs">
        {[
          { label: 'فينيل رقيق', speed: 30, pressure: 70 },
          { label: 'فينيل عادي', speed: 40, pressure: 100 },
          { label: 'فينيل سميك', speed: 20, pressure: 180 },
        ].map((preset) => (
          <button key={preset.label} onClick={() => { setSpeed(preset.speed); setPressure(preset.pressure); }}
            className="border border-gray-200 rounded-lg p-2 hover:bg-gray-50 text-center">
            <div className="font-medium text-gray-700">{preset.label}</div>
            <div className="text-gray-500">س:{preset.speed} ض:{preset.pressure}</div>
          </button>
        ))}
      </div>
      <div className="flex gap-2 justify-end">
        <button onClick={() => onSave({ cutter, cuttingSpeed: speed, pressure })}
          className="px-4 py-2 text-sm text-white bg-orange-500 hover:bg-orange-600 rounded-lg font-medium">
          حفظ الإعدادات
        </button>
      </div>
    </div>
  );
}

function MenuItem({ label, onClick, danger = false }: { label: string; onClick: () => void; danger?: boolean }) {
  return (
    <button onClick={onClick} className={`w-full text-right px-3 py-1.5 text-sm hover:bg-gray-50 ${danger ? 'text-red-600' : 'text-gray-700'}`}>
      {label}
    </button>
  );
}
