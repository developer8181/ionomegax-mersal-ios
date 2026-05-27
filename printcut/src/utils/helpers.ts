export const generateId = (): string => Math.random().toString(36).slice(2, 11);

let orderCounter = 6;
export const generateOrderNumber = (): string => {
  const num = String(orderCounter++).padStart(3, '0');
  return `ORD-2024-${num}`;
};

export const formatCurrency = (amount: number): string =>
  new Intl.NumberFormat('ar-SA', { style: 'currency', currency: 'SAR' }).format(amount);

export const formatDate = (date: Date): string =>
  new Intl.DateTimeFormat('ar-SA', { day: 'numeric', month: 'short', year: 'numeric' }).format(date);

export const formatDateTime = (date: Date): string =>
  new Intl.DateTimeFormat('ar-SA', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }).format(date);

export const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    pending: 'انتظار',
    designing: 'تصميم',
    printing: 'طباعة',
    cutting: 'قص',
    completed: 'مكتمل',
    cancelled: 'ملغي',
    queued: 'في الطابور',
    done: 'منتهي',
    failed: 'فشل',
  };
  return labels[status] ?? status;
};

export const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    designing: 'bg-blue-100 text-blue-800',
    printing: 'bg-purple-100 text-purple-800',
    cutting: 'bg-orange-100 text-orange-800',
    completed: 'bg-green-100 text-green-800',
    cancelled: 'bg-red-100 text-red-800',
    queued: 'bg-gray-100 text-gray-800',
    done: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };
  return colors[status] ?? 'bg-gray-100 text-gray-800';
};

export const getPriorityLabel = (priority: string): string => {
  const labels: Record<string, string> = {
    low: 'منخفض',
    normal: 'عادي',
    high: 'عالي',
    urgent: 'عاجل',
  };
  return labels[priority] ?? priority;
};

export const getPriorityColor = (priority: string): string => {
  const colors: Record<string, string> = {
    low: 'bg-gray-100 text-gray-600',
    normal: 'bg-blue-100 text-blue-700',
    high: 'bg-orange-100 text-orange-700',
    urgent: 'bg-red-100 text-red-700',
  };
  return colors[priority] ?? 'bg-gray-100 text-gray-600';
};

export const getMaterialTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    vinyl: 'فينيل',
    paper: 'ورق',
    canvas: 'كانفاس',
    fabric: 'قماش',
    pvc: 'PVC',
    other: 'أخرى',
  };
  return labels[type] ?? type;
};

export const getJobTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    print: 'طباعة فقط',
    cut: 'قص فقط',
    print_cut: 'طباعة وقص',
  };
  return labels[type] ?? type;
};
