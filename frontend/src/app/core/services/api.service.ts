import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Product } from '../models/product.model';
import { Order } from '../models/order.model';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  // ── Products ──────────────────────────────────────────
  getProducts(params?: {
    category?: string;
    search?: string;
    page?: number;
    per_page?: number;
  }): Observable<{
    items: Product[];
    total: number;
    page: number;
    per_page: number;
    pages: number;
  }> {
    let httpParams = new HttpParams();
    if (params?.category) httpParams = httpParams.set('category', params.category);
    if (params?.search) httpParams = httpParams.set('search', params.search);
    if (params?.page) httpParams = httpParams.set('page', params.page.toString());
    if (params?.per_page)
      httpParams = httpParams.set('per_page', params.per_page.toString());
    return this.http.get<{
      items: Product[];
      total: number;
      page: number;
      per_page: number;
      pages: number;
    }>(`${this.baseUrl}/products`, {
      params: httpParams,
    });
  }

  getProduct(id: string): Observable<Product> {
    return this.http.get<Product>(`${this.baseUrl}/products/${id}`);
  }

  getCategories(): Observable<{ categories: string[] }> {
    return this.http.get<{ categories: string[] }>(
      `${this.baseUrl}/products/categories`
    );
  }

  getInventory(productId: string): Observable<{
    product_id: string;
    quantity: number;
    reserved: number;
    available: number;
  }> {
    return this.http.get<{
      product_id: string;
      quantity: number;
      reserved: number;
      available: number;
    }>(`${this.baseUrl}/inventory/${productId}`);
  }

  getBatchInventory(
    productIds: string[]
  ): Observable<Record<string, { product_id: string; quantity: number; reserved: number; available: number }>> {
    return this.http.post<
      Record<string, { product_id: string; quantity: number; reserved: number; available: number }>
    >(`${this.baseUrl}/inventory/batch`, { product_ids: productIds });
  }

  watchStock(productId: string, email: string): Observable<{ id: string; product_id: string; email: string }> {
    return this.http.post<{ id: string; product_id: string; email: string }>(
      `${this.baseUrl}/inventory/${productId}/watch`,
      { email }
    );
  }

  unwatchStock(productId: string, email: string): Observable<{ message: string }> {
    return this.http.request<{ message: string }>(
      'DELETE',
      `${this.baseUrl}/inventory/${productId}/watch`,
      { body: { email } }
    );
  }

  isWatchingStock(productId: string, email: string): Observable<{ watching: boolean }> {
    return this.http.get<{ watching: boolean }>(
      `${this.baseUrl}/inventory/${productId}/watchers`,
      { params: new HttpParams().set('email', email) }
    );
  }

  // ── Orders ────────────────────────────────────────────
  getOrders(params?: {
    status?: string;
    customer_email?: string;
    page?: number;
  }): Observable<{ items: Order[]; total: number; page: number; per_page: number }> {
    let httpParams = new HttpParams();
    if (params?.status) httpParams = httpParams.set('status', params.status);
    if (params?.customer_email)
      httpParams = httpParams.set('customer_email', params.customer_email);
    if (params?.page) httpParams = httpParams.set('page', params.page.toString());
    return this.http.get<{
      items: Order[];
      total: number;
      page: number;
      per_page: number;
    }>(`${this.baseUrl}/orders`, { params: httpParams });
  }

  getOrder(id: string): Observable<Order> {
    return this.http.get<Order>(`${this.baseUrl}/orders/${id}`);
  }

  createOrder(order: {
    customer_email: string;
    items: {
      product_id: string;
      product_name: string;
      quantity: number;
      unit_price: number;
    }[];
  }): Observable<Order> {
    return this.http.post<Order>(`${this.baseUrl}/orders`, order);
  }

  // ── Auth ──────────────────────────────────────────────
  login(
    email: string,
    password: string
  ): Observable<{ access_token: string; token_type: string; user: AuthUser }> {
    return this.http.post<{
      access_token: string;
      token_type: string;
      user: AuthUser;
    }>(`${this.baseUrl}/auth/login`, { email, password });
  }

  register(
    email: string,
    password: string,
    name: string
  ): Observable<{ access_token: string; token_type: string; user: AuthUser }> {
    return this.http.post<{
      access_token: string;
      token_type: string;
      user: AuthUser;
    }>(`${this.baseUrl}/auth/register`, { email, password, name });
  }
}

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  role: string;
}
