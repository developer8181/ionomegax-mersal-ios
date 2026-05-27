export type OrderStatus = 'pending' | 'designing' | 'printing' | 'cutting' | 'completed' | 'cancelled';
export type Priority = 'low' | 'normal' | 'high' | 'urgent';
export type MaterialType = 'vinyl' | 'paper' | 'canvas' | 'fabric' | 'pvc' | 'other';
export type JobType = 'print' | 'cut' | 'print_cut';

export interface Customer {
  id: string;
  name: string;
  phone: string;
  email?: string;
  address?: string;
  notes?: string;
  createdAt: Date;
  totalOrders: number;
}

export interface Material {
  id: string;
  name: string;
  type: MaterialType;
  width: number;
  height: number;
  unit: 'cm' | 'mm' | 'inch';
  color: string;
  stock: number;
  stockUnit: string;
  pricePerUnit: number;
  notes?: string;
}

export interface OrderItem {
  id: string;
  name: string;
  quantity: number;
  width: number;
  height: number;
  materialId: string;
  materialName: string;
  jobType: JobType;
  designUrl?: string;
  notes?: string;
  unitPrice: number;
}

export interface Order {
  id: string;
  orderNumber: string;
  customerId: string;
  customerName: string;
  status: OrderStatus;
  priority: Priority;
  items: OrderItem[];
  totalAmount: number;
  depositAmount: number;
  createdAt: Date;
  updatedAt: Date;
  dueDate?: Date;
  notes?: string;
  assignedTo?: string;
}

export interface PrintJob {
  id: string;
  orderId: string;
  orderNumber: string;
  customerName: string;
  itemName: string;
  width: number;
  height: number;
  quantity: number;
  materialName: string;
  status: 'queued' | 'printing' | 'done' | 'failed';
  priority: Priority;
  createdAt: Date;
  startedAt?: Date;
  completedAt?: Date;
  printer?: string;
  notes?: string;
}

export interface CutJob {
  id: string;
  orderId: string;
  orderNumber: string;
  customerName: string;
  itemName: string;
  width: number;
  height: number;
  quantity: number;
  materialName: string;
  status: 'queued' | 'cutting' | 'done' | 'failed';
  priority: Priority;
  createdAt: Date;
  startedAt?: Date;
  completedAt?: Date;
  cutter?: string;
  cuttingSpeed?: number;
  pressure?: number;
  notes?: string;
}

export interface DashboardStats {
  totalOrders: number;
  pendingOrders: number;
  inProgressOrders: number;
  completedOrders: number;
  totalRevenue: number;
  pendingRevenue: number;
  printQueueCount: number;
  cutQueueCount: number;
}
