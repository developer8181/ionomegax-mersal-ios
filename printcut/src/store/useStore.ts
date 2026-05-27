import { create } from 'zustand';
import type { Customer, Order, Material, PrintJob, CutJob, OrderStatus } from '../types';
import { generateId, generateOrderNumber } from '../utils/helpers';

interface AppStore {
  customers: Customer[];
  orders: Order[];
  materials: Material[];
  printQueue: PrintJob[];
  cutQueue: CutJob[];

  // Customer actions
  addCustomer: (customer: Omit<Customer, 'id' | 'createdAt' | 'totalOrders'>) => void;
  updateCustomer: (id: string, data: Partial<Customer>) => void;
  deleteCustomer: (id: string) => void;

  // Order actions
  addOrder: (order: Omit<Order, 'id' | 'orderNumber' | 'createdAt' | 'updatedAt'>) => void;
  updateOrder: (id: string, data: Partial<Order>) => void;
  updateOrderStatus: (id: string, status: OrderStatus) => void;
  deleteOrder: (id: string) => void;

  // Material actions
  addMaterial: (material: Omit<Material, 'id'>) => void;
  updateMaterial: (id: string, data: Partial<Material>) => void;
  deleteMaterial: (id: string) => void;

  // Print queue actions
  addToPrintQueue: (job: Omit<PrintJob, 'id' | 'createdAt'>) => void;
  updatePrintJob: (id: string, data: Partial<PrintJob>) => void;
  removePrintJob: (id: string) => void;

  // Cut queue actions
  addToCutQueue: (job: Omit<CutJob, 'id' | 'createdAt'>) => void;
  updateCutJob: (id: string, data: Partial<CutJob>) => void;
  removeCutJob: (id: string) => void;
}

const sampleCustomers: Customer[] = [
  { id: '1', name: 'محمد العلي', phone: '0501234567', email: 'mohammed@email.com', address: 'الرياض - حي النزهة', createdAt: new Date('2024-01-15'), totalOrders: 8 },
  { id: '2', name: 'سارة المطيري', phone: '0557891234', email: 'sara@email.com', address: 'جدة - حي الحمراء', createdAt: new Date('2024-02-20'), totalOrders: 5 },
  { id: '3', name: 'شركة النور للدعاية', phone: '0112345678', email: 'info@alnoor.com', address: 'الرياض - طريق الملك عبدالله', createdAt: new Date('2024-01-05'), totalOrders: 15 },
  { id: '4', name: 'أحمد الزهراني', phone: '0559876543', address: 'مكة المكرمة', createdAt: new Date('2024-03-10'), totalOrders: 3 },
  { id: '5', name: 'فاطمة القحطاني', phone: '0501112233', email: 'fatima@email.com', address: 'الدمام - حي الشاطئ', createdAt: new Date('2024-03-22'), totalOrders: 2 },
];

const sampleMaterials: Material[] = [
  { id: '1', name: 'فينيل أبيض لامع', type: 'vinyl', width: 120, height: 0, unit: 'cm', color: '#FFFFFF', stock: 50, stockUnit: 'متر', pricePerUnit: 25 },
  { id: '2', name: 'فينيل أسود مطفأ', type: 'vinyl', width: 120, height: 0, unit: 'cm', color: '#000000', stock: 30, stockUnit: 'متر', pricePerUnit: 25 },
  { id: '3', name: 'ورق طباعة لامع', type: 'paper', width: 91, height: 0, unit: 'cm', color: '#FFFFFF', stock: 100, stockUnit: 'متر', pricePerUnit: 15 },
  { id: '4', name: 'فينيل شفاف', type: 'vinyl', width: 120, height: 0, unit: 'cm', color: 'transparent', stock: 20, stockUnit: 'متر', pricePerUnit: 35 },
  { id: '5', name: 'كانفاس طباعة', type: 'canvas', width: 150, height: 0, unit: 'cm', color: '#F5F5DC', stock: 25, stockUnit: 'متر', pricePerUnit: 45 },
  { id: '6', name: 'PVC شفاف', type: 'pvc', width: 100, height: 0, unit: 'cm', color: 'transparent', stock: 15, stockUnit: 'متر', pricePerUnit: 30 },
];

const sampleOrders: Order[] = [
  {
    id: '1', orderNumber: 'ORD-2024-001', customerId: '3', customerName: 'شركة النور للدعاية',
    status: 'printing', priority: 'high',
    items: [
      { id: '1', name: 'ملصقات لوجو', quantity: 500, width: 10, height: 10, materialId: '1', materialName: 'فينيل أبيض لامع', jobType: 'print_cut', unitPrice: 2 }
    ],
    totalAmount: 1000, depositAmount: 500,
    createdAt: new Date('2024-05-20'), updatedAt: new Date('2024-05-22'),
    dueDate: new Date('2024-05-28'),
  },
  {
    id: '2', orderNumber: 'ORD-2024-002', customerId: '1', customerName: 'محمد العلي',
    status: 'cutting', priority: 'normal',
    items: [
      { id: '2', name: 'لافتة بنر', quantity: 2, width: 100, height: 200, materialId: '3', materialName: 'ورق طباعة لامع', jobType: 'print', unitPrice: 150 }
    ],
    totalAmount: 300, depositAmount: 300,
    createdAt: new Date('2024-05-21'), updatedAt: new Date('2024-05-23'),
    dueDate: new Date('2024-05-25'),
  },
  {
    id: '3', orderNumber: 'ORD-2024-003', customerId: '2', customerName: 'سارة المطيري',
    status: 'pending', priority: 'normal',
    items: [
      { id: '3', name: 'ملصقات شخصية', quantity: 100, width: 5, height: 5, materialId: '2', materialName: 'فينيل أسود مطفأ', jobType: 'print_cut', unitPrice: 3 }
    ],
    totalAmount: 300, depositAmount: 150,
    createdAt: new Date('2024-05-23'), updatedAt: new Date('2024-05-23'),
    dueDate: new Date('2024-05-30'),
  },
  {
    id: '4', orderNumber: 'ORD-2024-004', customerId: '3', customerName: 'شركة النور للدعاية',
    status: 'designing', priority: 'urgent',
    items: [
      { id: '4', name: 'بنرات معرض', quantity: 10, width: 80, height: 160, materialId: '3', materialName: 'ورق طباعة لامع', jobType: 'print', unitPrice: 120 }
    ],
    totalAmount: 1200, depositAmount: 600,
    createdAt: new Date('2024-05-24'), updatedAt: new Date('2024-05-24'),
    dueDate: new Date('2024-05-27'),
  },
  {
    id: '5', orderNumber: 'ORD-2024-005', customerId: '4', customerName: 'أحمد الزهراني',
    status: 'completed', priority: 'low',
    items: [
      { id: '5', name: 'لاصق سيارة', quantity: 1, width: 30, height: 15, materialId: '4', materialName: 'فينيل شفاف', jobType: 'print_cut', unitPrice: 80 }
    ],
    totalAmount: 80, depositAmount: 80,
    createdAt: new Date('2024-05-18'), updatedAt: new Date('2024-05-20'),
    dueDate: new Date('2024-05-22'),
  },
];

const samplePrintQueue: PrintJob[] = [
  { id: '1', orderId: '1', orderNumber: 'ORD-2024-001', customerName: 'شركة النور للدعاية', itemName: 'ملصقات لوجو', width: 10, height: 10, quantity: 500, materialName: 'فينيل أبيض لامع', status: 'printing', priority: 'high', createdAt: new Date('2024-05-22'), startedAt: new Date(), printer: 'رولاند VS-640' },
  { id: '2', orderId: '4', orderNumber: 'ORD-2024-004', customerName: 'شركة النور للدعاية', itemName: 'بنرات معرض', width: 80, height: 160, quantity: 10, materialName: 'ورق طباعة لامع', status: 'queued', priority: 'urgent', createdAt: new Date('2024-05-24'), printer: 'إبسون SC-T7200' },
  { id: '3', orderId: '3', orderNumber: 'ORD-2024-003', customerName: 'سارة المطيري', itemName: 'ملصقات شخصية', width: 5, height: 5, quantity: 100, materialName: 'فينيل أسود مطفأ', status: 'queued', priority: 'normal', createdAt: new Date('2024-05-23') },
];

const sampleCutQueue: CutJob[] = [
  { id: '1', orderId: '2', orderNumber: 'ORD-2024-002', customerName: 'محمد العلي', itemName: 'لافتة بنر', width: 100, height: 200, quantity: 2, materialName: 'ورق طباعة لامع', status: 'cutting', priority: 'normal', createdAt: new Date('2024-05-23'), startedAt: new Date(), cutter: 'Graphtec CE7000', cuttingSpeed: 40, pressure: 80 },
  { id: '2', orderId: '1', orderNumber: 'ORD-2024-001', customerName: 'شركة النور للدعاية', itemName: 'ملصقات لوجو', width: 10, height: 10, quantity: 500, materialName: 'فينيل أبيض لامع', status: 'queued', priority: 'high', createdAt: new Date('2024-05-22'), cutter: 'Graphtec CE7000' },
];

export const useStore = create<AppStore>((set) => ({
  customers: sampleCustomers,
  orders: sampleOrders,
  materials: sampleMaterials,
  printQueue: samplePrintQueue,
  cutQueue: sampleCutQueue,

  addCustomer: (customer) => set((state) => ({
    customers: [...state.customers, { ...customer, id: generateId(), createdAt: new Date(), totalOrders: 0 }]
  })),

  updateCustomer: (id, data) => set((state) => ({
    customers: state.customers.map((c) => c.id === id ? { ...c, ...data } : c)
  })),

  deleteCustomer: (id) => set((state) => ({
    customers: state.customers.filter((c) => c.id !== id)
  })),

  addOrder: (order) => set((state) => ({
    orders: [...state.orders, {
      ...order, id: generateId(), orderNumber: generateOrderNumber(),
      createdAt: new Date(), updatedAt: new Date()
    }],
    customers: state.customers.map((c) =>
      c.id === order.customerId ? { ...c, totalOrders: c.totalOrders + 1 } : c
    )
  })),

  updateOrder: (id, data) => set((state) => ({
    orders: state.orders.map((o) => o.id === id ? { ...o, ...data, updatedAt: new Date() } : o)
  })),

  updateOrderStatus: (id, status) => set((state) => ({
    orders: state.orders.map((o) => o.id === id ? { ...o, status, updatedAt: new Date() } : o)
  })),

  deleteOrder: (id) => set((state) => ({
    orders: state.orders.filter((o) => o.id !== id)
  })),

  addMaterial: (material) => set((state) => ({
    materials: [...state.materials, { ...material, id: generateId() }]
  })),

  updateMaterial: (id, data) => set((state) => ({
    materials: state.materials.map((m) => m.id === id ? { ...m, ...data } : m)
  })),

  deleteMaterial: (id) => set((state) => ({
    materials: state.materials.filter((m) => m.id !== id)
  })),

  addToPrintQueue: (job) => set((state) => ({
    printQueue: [...state.printQueue, { ...job, id: generateId(), createdAt: new Date() }]
  })),

  updatePrintJob: (id, data) => set((state) => ({
    printQueue: state.printQueue.map((j) => j.id === id ? { ...j, ...data } : j)
  })),

  removePrintJob: (id) => set((state) => ({
    printQueue: state.printQueue.filter((j) => j.id !== id)
  })),

  addToCutQueue: (job) => set((state) => ({
    cutQueue: [...state.cutQueue, { ...job, id: generateId(), createdAt: new Date() }]
  })),

  updateCutJob: (id, data) => set((state) => ({
    cutQueue: state.cutQueue.map((j) => j.id === id ? { ...j, ...data } : j)
  })),

  removeCutJob: (id) => set((state) => ({
    cutQueue: state.cutQueue.filter((j) => j.id !== id)
  })),
}));
