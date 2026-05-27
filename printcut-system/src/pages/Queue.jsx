import { useState } from 'react';
import { GripVertical, Play, Trash2, ArrowUp, ArrowDown, Printer, Scissors } from 'lucide-react';
import Header from '../components/Header';
import { useApp } from '../context/AppContext';
import { statusMap, priorityMap, jobTypes } from '../data/initialData';

export default function Queue() {
  const { state, dispatch, notify } = useApp();

  const queuedJobs = state.jobs.filter(j => j.status === 'queued');
  const inProgressJobs = state.jobs.filter(j => j.status === 'in_progress');

  const moveUp = (index) => {
    if (index === 0) return;
    dispatch({ type: 'REORDER_QUEUE', payload: { dragIndex: index, hoverIndex: index - 1 } });
  };

  const moveDown = (index) => {
    if (index === queuedJobs.length - 1) return;
    dispatch({ type: 'REORDER_QUEUE', payload: { dragIndex: index, hoverIndex: index + 1 } });
  };

  const startJob = (id) => {
    dispatch({ type: 'UPDATE_JOB_STATUS', payload: { id, status: 'in_progress' } });
    notify('تم بدء تنفيذ المهمة');
  };

  const completeJob = (id) => {
    dispatch({ type: 'UPDATE_JOB_STATUS', payload: { id, status: 'completed' } });
    notify('تم إكمال المهمة بنجاح');
  };

  const removeFromQueue = (id) => {
    dispatch({ type: 'UPDATE_JOB_STATUS', payload: { id, status: 'cancelled' } });
    notify('تم إزالة المهمة من قائمة الانتظار', 'info');
  };

  const getTypeIcon = (type) => {
    if (type === 'cut') return Scissors;
    return Printer;
  };

  return (
    <div>
      <Header title="قائمة الانتظار" subtitle={`${queuedJobs.length} مهمة في الانتظار • ${inProgressJobs.length} قيد التنفيذ`} />

      <div className="p-6 space-y-6">
        {inProgressJobs.length > 0 && (
          <div>
            <h3 className="text-base font-bold text-gray-900 mb-3 flex items-center gap-2">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
              </span>
              قيد التنفيذ الآن
            </h3>
            <div className="space-y-3">
              {inProgressJobs.map(job => {
                const type = jobTypes.find(t => t.id === job.type);
                const TypeIcon = getTypeIcon(job.type);
                return (
                  <div
                    key={job.id}
                    className="bg-blue-50 border border-blue-200 rounded-2xl p-4 flex items-center justify-between"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
                        <TypeIcon className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-gray-900">{job.name}</h4>
                        <div className="flex items-center gap-3 mt-1">
                          <span className="text-xs text-gray-500">{job.client}</span>
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${type?.color}`}>
                            {type?.name}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-gray-900">{job.price} ر.س</span>
                      <button
                        onClick={() => completeJob(job.id)}
                        className="px-3 py-1.5 bg-accent-600 text-white rounded-lg text-xs font-medium hover:bg-accent-700 transition-colors"
                      >
                        إكمال
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div>
          <h3 className="text-base font-bold text-gray-900 mb-3">قائمة الانتظار</h3>
          {queuedJobs.length === 0 ? (
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Printer className="w-8 h-8 text-gray-300" />
              </div>
              <h4 className="text-lg font-semibold text-gray-400">لا توجد مهام في الانتظار</h4>
              <p className="text-sm text-gray-400 mt-1">أضف مهمة جديدة لتظهر هنا</p>
            </div>
          ) : (
            <div className="space-y-2">
              {queuedJobs.map((job, index) => {
                const priority = priorityMap[job.priority];
                const type = jobTypes.find(t => t.id === job.type);
                const TypeIcon = getTypeIcon(job.type);
                return (
                  <div
                    key={job.id}
                    className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 flex items-center gap-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex flex-col gap-1">
                      <button
                        onClick={() => moveUp(index)}
                        disabled={index === 0}
                        className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30 transition-colors"
                      >
                        <ArrowUp className="w-4 h-4" />
                      </button>
                      <div className="flex items-center justify-center w-6 h-6 bg-gray-100 rounded-full">
                        <span className="text-xs font-bold text-gray-500">{index + 1}</span>
                      </div>
                      <button
                        onClick={() => moveDown(index)}
                        disabled={index === queuedJobs.length - 1}
                        className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30 transition-colors"
                      >
                        <ArrowDown className="w-4 h-4" />
                      </button>
                    </div>

                    <div className="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center shrink-0">
                      <TypeIcon className="w-5 h-5 text-gray-500" />
                    </div>

                    <div className="flex-1">
                      <h4 className="text-sm font-bold text-gray-900">{job.name}</h4>
                      <div className="flex items-center gap-3 mt-1 flex-wrap">
                        <span className="text-xs text-gray-500">{job.client}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${type?.color}`}>
                          {type?.name}
                        </span>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${priority.color}`}>
                          {priority.name}
                        </span>
                        <span className="text-xs text-gray-400">
                          {job.width}×{job.height} {job.unit} • {job.copies} نسخة
                        </span>
                      </div>
                    </div>

                    <div className="text-left ml-4">
                      <p className="text-sm font-bold text-gray-900">{job.price} ر.س</p>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => startJob(job.id)}
                        className="p-2 bg-primary-50 text-primary-600 rounded-lg hover:bg-primary-100 transition-colors"
                        title="بدء التنفيذ"
                      >
                        <Play className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => removeFromQueue(job.id)}
                        className="p-2 bg-danger-50 text-danger-500 rounded-lg hover:bg-danger-100 transition-colors"
                        title="إزالة"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
