import { Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../../core/services/auth.service';
import { Order } from '../../../core/models/order.model';

@Component({
  selector: 'app-order-detail',
  standalone: true,
  imports: [RouterLink],
  template: `
    @if (loading()) {
      <div class="card" style="padding: 2rem;">
        <div class="skeleton" style="height: 2rem; width: 50%; margin-bottom: 1rem;"></div>
        <div class="skeleton" style="height: 1rem; width: 70%;"></div>
      </div>
    }

    @if (!loading() && order()) {
      <div class="breadcrumb">
        <a routerLink="/orders">Orders</a>
        <span class="sep">/</span>
        <span>Order #{{ order()!.id.slice(0, 8) }}</span>
      </div>

      <div class="order-detail card">
        <div class="order-header">
          <div>
            <h1>Order #{{ order()!.id.slice(0, 8) }}</h1>
            <p class="order-date">{{ formatDate(order()!.created_at) }}</p>
          </div>
          <span class="badge badge-lg"
            [class.badge-warning]="order()!.status === 'pending'"
            [class.badge-success]="order()!.status === 'confirmed'"
            [class.badge-danger]="order()!.status === 'failed' || order()!.status === 'cancelled'"
            [class.badge-info]="order()!.status !== 'pending' && order()!.status !== 'confirmed' && order()!.status !== 'failed' && order()!.status !== 'cancelled'"
          >
            {{ order()!.status }}
          </span>
        </div>

        <div class="order-info">
          <div class="info-item">
            <span class="info-label">Customer Email</span>
            <span class="info-value">{{ order()!.customer_email }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Order ID</span>
            <span class="info-value" style="font-family: monospace; font-size: 0.8125rem;">{{ order()!.id }}</span>
          </div>
        </div>

        <h3 class="section-title">Items</h3>
        <table class="items-table">
          <thead>
            <tr>
              <th>Product</th>
              <th>Quantity</th>
              <th>Unit Price</th>
              <th>Subtotal</th>
            </tr>
          </thead>
          <tbody>
            @for (item of order()!.items; track item.id) {
              <tr>
                <td>{{ item.product_name }}</td>
                <td>{{ item.quantity }}</td>
                <td>\${{ item.unit_price.toFixed(2) }}</td>
                <td class="subtotal">\${{ (item.unit_price * item.quantity).toFixed(2) }}</td>
              </tr>
            }
          </tbody>
        </table>

        <div class="order-total-row">
          <span>Total</span>
          <span>\${{ order()!.total_amount.toFixed(2) }}</span>
        </div>

        @if (order()!.status === 'pending') {
          <div class="status-note">
            <p>Your order is being processed. Inventory will be reserved shortly.</p>
          </div>
        } @else if (order()!.status === 'confirmed') {
          <div class="status-note status-success">
            <p>Your order has been confirmed! Check your email for details.</p>
          </div>
        } @else if (order()!.status === 'failed') {
          <div class="status-note status-error">
            <p>This order could not be fulfilled. Inventory may have been unavailable.</p>
          </div>
        }

        <div style="margin-top: 1.5rem;">
          <button class="btn btn-secondary" (click)="refresh()">Refresh Status</button>
        </div>
      </div>
    }

    @if (!loading() && !order()) {
      <div class="empty-state">
        <h3>Order not found</h3>
        <a routerLink="/orders" class="btn btn-primary" style="margin-top: 1rem;">
          View All Orders
        </a>
      </div>
    }
  `,
  styles: [`
    .breadcrumb {
      font-size: 0.875rem;
      color: var(--color-gray-500);
      margin-bottom: 1.5rem;
    }

    .breadcrumb a {
      color: var(--color-primary);
      text-decoration: none;
    }

    .sep { margin: 0 0.5rem; }

    .order-detail {
      padding: 2rem;
      max-width: 800px;
    }

    .order-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 1.5rem;
    }

    .order-header h1 {
      font-size: 1.5rem;
      font-weight: 700;
    }

    .order-date {
      font-size: 0.875rem;
      color: var(--color-gray-500);
      margin-top: 0.25rem;
    }

    .badge-lg {
      padding: 0.375rem 1rem;
      font-size: 0.875rem;
    }

    .order-info {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
      margin-bottom: 1.5rem;
      padding: 1rem;
      background: var(--color-gray-50);
      border-radius: var(--radius);
    }

    .info-label {
      display: block;
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--color-gray-500);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 0.25rem;
    }

    .info-value {
      font-size: 0.9375rem;
      color: var(--color-gray-800);
    }

    .section-title {
      font-size: 1rem;
      font-weight: 700;
      margin-bottom: 0.75rem;
    }

    .items-table {
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 1rem;
    }

    .items-table th {
      text-align: left;
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--color-gray-500);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 0.5rem 0;
      border-bottom: 1px solid var(--color-gray-200);
    }

    .items-table td {
      padding: 0.75rem 0;
      font-size: 0.9375rem;
      border-bottom: 1px solid var(--color-gray-100);
    }

    .subtotal {
      font-weight: 600;
    }

    .order-total-row {
      display: flex;
      justify-content: space-between;
      font-size: 1.25rem;
      font-weight: 700;
      padding-top: 0.75rem;
    }

    .status-note {
      margin-top: 1.5rem;
      padding: 1rem;
      border-radius: var(--radius);
      background: var(--color-warning-light);
      color: var(--color-warning);
      font-size: 0.9375rem;
    }

    .status-success {
      background: var(--color-success-light);
      color: var(--color-success);
    }

    .status-error {
      background: var(--color-danger-light);
      color: var(--color-danger);
    }
  `],
})
export class OrderDetailComponent implements OnInit {
  order = signal<Order | null>(null);
  loading = signal(true);
  private orderId = '';
  private destroyRef = inject(DestroyRef);

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService,
    private auth: AuthService
  ) {}

  ngOnInit(): void {
    if (!this.auth.isLoggedIn()) {
      this.router.navigate(['/login']);
      return;
    }
    this.orderId = this.route.snapshot.paramMap.get('id')!;
    this.loadOrder();
  }

  loadOrder(): void {
    this.api
      .getOrder(this.orderId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (order) => {
          if (order.customer_email !== this.auth.email()) {
            this.order.set(null);
          } else {
            this.order.set(order);
          }
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
        },
      });
  }

  refresh(): void {
    this.loadOrder();
  }

  formatDate(iso: string): string {
    return new Date(iso).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }
}
