export interface OrderItem {
  id: string;
  product_id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
}

export interface Order {
  id: string;
  customer_email: string;
  status: string;
  total_amount: number;
  items: OrderItem[];
  created_at: string;
  updated_at: string;
}
