import { useState } from 'react';
import { Play, CheckCircle, XCircle, Clock, Printer, MoreVertical } from 'lucide-react';
import { useStore } from '../store/useStore';
import type { PrintJob } from '../types';
import { formatDateTime, getPriorityColor, getPriorityLabel } from '../utils/helpers';
import PageHeader from '../components/PageHeader';

const statusConfig = {
  queued: { label: 'في الطابور', color: 'bg-gray-100 text-gray-700', icon: Clock },
  printing: { label: 'جارية الطباعة', color: 'bg-purple-100 text-purple-700', icon: Printer },
  done: { label: 'مكتملة', color: 'bg-green-100 text-green-700', icon: CheckCircle },
  failed: { label: 'فشلت', color: 'bg-red-100 text-red-700', icon: XCircle },
};

export default function PrintQueue() {
  const { printQueue, updatePrintJob, removePrintJob } = useStore();
  const [activeTab, setActiveTab] = useState<'queued' | 'printing' | 'done' | 'failed'>('printing');

  const byStatus = {
    queued: printQueue.filter((j) => j.status === 'queued'),
    printing: printQueue.filter((j) => j.status === 'printing'),
    done: printQueue.filter((j) => j.status === 'done'),
    failed: printQueue.filter((j) => j.status === 'failed'),
  };

  const startJob = (id: string) =>
    updatePrintJob(id, { status: 'printing', startedAt: new Date() });

  const completeJob = (id: string) =>
    updatePrintJob(id, { status: 'done', completedAt: new Date() });

  const failJob = (id: string) =>
    updatePrintJob(id, { status: 'failed' });

  const requeueJob = (id: string) =>
    updatePrintJob(id, { status: 'queued', startedAt: undefined, completedAt: undefined });

  const tabs = (['printing', 'queued', 'done', 'failed'] as const);

  return (
    <div>
      <PageHeader
        title="طابور الطباعة"
        subtitle={`${printQueue.length} مهمة إجمالاً`}
        actions={
          <div className="flex items-center gap-3 text-sm">
            <div className="flex items-center gap-1.5 text-purple-700 bg-purple-50 border border-purple-200 px-3 py-1.5 rounded-lg">
              <Printer size={14} />
              <span>{byStatus.printing.length} جارية الآن</span>
            </div>
          </div>
        }
      />

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
        {/* Active printing jobs with progress */}
        {activeTab === 'printing' && byStatus.printing.length > 0 && (
          <div className="mb-6 space-y-3">
            {byStatus.printing.map((job) => (
              <ActiveJobCard key={job.id} job={job} onComplete={() => completeJob(job.id)} onFail={() => failJob(job.id)} />
            ))}
          </div>
        )}

        {/* Jobs Grid */}
        <div className="grid grid-cols-1 gap-3">
          {byStatus[activeTab].map((job, idx) => (
            <JobCard
              key={job.id}
              job={job}
              index={idx}
              onStart={() => startJob(job.id)}
              onComplete={() => completeJob(job.id)}
              onRequeue={() => requeueJob(job.id)}
              onRemove={() => removePrintJob(job.id)}
            />
          ))}
          {byStatus[activeTab].length === 0 && (
            <div className="text-center py-16 text-gray-400 bg-white rounded-xl border border-gray-200">
              <Printer size={32} className="mx-auto mb-3 opacity-50" />
              <p>لا توجد مهام في هذا القسم</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ActiveJobCard({ job, onComplete, onFail }: {
  job: PrintJob;
  onComplete: () => void;
  onFail: () => void;
}) {
  const [progress] = useState(Math.floor(Math.random() * 70) + 15);

  return (
    <div className="bg-purple-50 border border-purple-200 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-purple-500 animate-pulse" />
          <div>
            <span className="font-semibold text-purple-900">{job.itemName}</span>
            <span className="text-sm text-purple-700 mr-2">— {job.customerName}</span>
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
      <div className="mb-2 flex items-center justify-between text-xs text-purple-700">
        <span>التقدم: {progress}%</span>
        <span>{job.printer || 'الطابعة الافتراضية'}</span>
      </div>
      <div className="w-full bg-purple-200 rounded-full h-2">
        <div className="bg-purple-600 h-2 rounded-full transition-all" style={{ width: `${progress}%` }} />
      </div>
      <div className="mt-2 text-xs text-purple-600">
        {job.orderNumber} · {job.quantity} قطعة · {job.width}×{job.height} سم · {job.materialName}
      </div>
    </div>
  );
}

function JobCard({ job, index, onStart, onComplete, onRequeue, onRemove }: {
  job: PrintJob;
  index: number;
  onStart: () => void;
  onComplete: () => void;
  onFail?: () => void;
  onRequeue: () => void;
  onRemove: () => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-sm transition-shadow">
      <div className="flex items-start gap-4">
        {/* Order indicator */}
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
              <div className="relative">
                <button onClick={() => setMenuOpen(!menuOpen)} className="p-1 text-gray-400 hover:text-gray-600 rounded">
                  <MoreVertical size={14} />
                </button>
                {menuOpen && (
                  <>
                    <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
                    <div className="absolute top-full left-0 z-20 bg-white rounded-lg shadow-lg border border-gray-200 py-1 min-w-32">
                      {job.status === 'queued' && <MenuItem label="بدء الطباعة" onClick={() => { onStart(); setMenuOpen(false); }} />}
                      {job.status === 'printing' && <MenuItem label="تم الاكتمال" onClick={() => { onComplete(); setMenuOpen(false); }} />}
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
            {job.printer && <span className="bg-purple-50 text-purple-700 px-2 py-1 rounded">الطابعة: {job.printer}</span>}
          </div>

          <div className="mt-2 text-xs text-gray-400">
            أُضيف: {formatDateTime(job.createdAt)}
            {job.completedAt && ` · اكتمل: ${formatDateTime(job.completedAt)}`}
          </div>
        </div>

        {/* Actions */}
        {job.status === 'queued' && (
          <button onClick={onStart} className="flex items-center gap-1.5 text-xs text-white bg-purple-600 hover:bg-purple-700 px-3 py-2 rounded-lg font-medium shrink-0">
            <Play size={12} /> بدء
          </button>
        )}
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
