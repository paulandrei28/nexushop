import { Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../../core/services/auth.service';
import { Order } from '../../../core/models/order.model';

@Component({
  selector: 'app-order-list',
  standalone: true,
  imports: [RouterLink],
  template: `
    <div class="page-header">
      <h1>My Orders</h1>
    </div>

    @if (!auth.isLoggedIn()) {
      <div class="empty-state">
        <h3>Please log in to view orders</h3>
        <a routerLink="/login" class="btn btn-primary" style="margin-top: 1rem;">Login</a>
      </div>
    } @else if (loading()) {
      <div class="order-list">
        @for (i of [1, 2, 3]; track i) {
          <div class="card" style="padding: 1.25rem;">
            <div class="skeleton" style="height: 1.25rem; width: 40%; margin-bottom: 0.5rem;"></div>
            <div class="skeleton" style="height: 1rem; width: 60%;"></div>
          </div>
        }
      </div>
    } @else if (orders().length === 0) {
      <div class="empty-state">
        <h3>No orders yet</h3>
        <p>Place your first order!</p>
        <a routerLink="/products" class="btn btn-primary" style="margin-top: 1rem;">
          Browse Products
        </a>
      </div>
    } @else {
      <div class="order-list">
        @for (order of orders(); track order.id) {
          <a [routerLink]="['/orders', order.id]" class="card order-card">
            <div class="order-card-header">
              <span class="order-id">Order #{{ order.id.slice(0, 8) }}</span>
              <span class="badge"
                [class.badge-warning]="order.status === 'pending'"
                [class.badge-success]="order.status === 'confirmed'"
                [class.badge-danger]="order.status === 'failed' || order.status === 'cancelled'"
                [class.badge-info]="order.status !== 'pending' && order.status !== 'confirmed' && order.status !== 'failed' && order.status !== 'cancelled'"
              >
                {{ order.status }}
              </span>
            </div>
            <div class="order-card-body">
              <span class="order-items-count">{{ order.items.length }} item(s)</span>
              <span class="order-total">\${{ order.total_amount.toFixed(2) }}</span>
            </div>
            <div class="order-card-footer">
              <span>{{ formatDate(order.created_at) }}</span>
            </div>
          </a>
        }
      </div>
    }
  `,
  styles: [`
    .order-list {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      max-width: 700px;
    }

    .order-card {
      display: block;
      padding: 1.25rem;
      text-decoration: none;
      transition: box-shadow 0.2s ease;
      cursor: pointer;
    }

    .order-card:hover {
      box-shadow: var(--shadow-md);
      text-decoration: none;
    }

    .order-card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.5rem;
    }

    .order-id {
      font-weight: 600;
      color: var(--color-gray-900);
    }

    .order-card-body {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.5rem;
    }

    .order-items-count {
      font-size: 0.875rem;
      color: var(--color-gray-500);
    }

    .order-total {
      font-size: 1.125rem;
      font-weight: 700;
      color: var(--color-gray-900);
    }

    .order-card-footer {
      font-size: 0.8125rem;
      color: var(--color-gray-400);
    }
  `],
})
export class OrderListComponent implements OnInit {
  orders = signal<Order[]>([]);
  loading = signal(true);

  private destroyRef = inject(DestroyRef);

  constructor(
    private api: ApiService,
    public auth: AuthService
  ) {}

  ngOnInit(): void {
    if (!this.auth.isLoggedIn()) {
      this.loading.set(false);
      return;
    }
    this.api
      .getOrders({ customer_email: this.auth.email()! })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => {
          this.orders.set(res.items);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
        },
      });
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
