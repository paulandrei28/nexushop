import { Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../../core/services/auth.service';
import { CartService } from '../../../core/services/cart.service';
import { NotificationService } from '../../../core/services/notification.service';
import { Product } from '../../../core/models/product.model';

@Component({
  selector: 'app-product-detail',
  standalone: true,
  imports: [RouterLink],
  template: `
    @if (loading()) {
      <div class="detail-container">
        <div class="skeleton" style="height: 300px; width: 100%;"></div>
        <div style="padding: 1.5rem;">
          <div class="skeleton" style="height: 2rem; width: 60%; margin-bottom: 1rem;"></div>
          <div class="skeleton" style="height: 1rem; width: 80%;"></div>
        </div>
      </div>
    }

    @if (!loading() && product()) {
      <div class="breadcrumb">
        <a routerLink="/products">Products</a>
        <span class="sep">/</span>
        <span>{{ product()!.name }}</span>
      </div>

      <div class="detail-container">
        <div class="detail-image">
          <span class="detail-icon">{{ product()!.category.charAt(0).toUpperCase() }}</span>
        </div>

        <div class="detail-info">
          <span class="detail-category">{{ product()!.category }}</span>
          <h1 class="detail-name">{{ product()!.name }}</h1>
          <p class="detail-description">
            {{ product()!.description || 'No description available for this product.' }}
          </p>

          <div class="detail-price">\${{ product()!.price.toFixed(2) }}</div>

          @if (stock() !== null) {
            <div class="stock-info">
              @if (stock()! > 0) {
                <span class="badge badge-success">In Stock ({{ stock() }})</span>
              } @else {
                <span class="badge badge-danger">Out of Stock</span>
              }
            </div>
          }

          <div class="detail-actions">
            @if (stock() !== 0) {
              <button
                class="btn btn-primary btn-lg"
                (click)="addToCart()"
                [disabled]="stock() === 0"
              >
                Add to Cart
              </button>
            } @else {
              @if (watching()) {
                <button
                  class="btn btn-notify-active btn-lg"
                  (click)="unwatchProduct()"
                >
                  Watching - Click to Unsubscribe
                </button>
              } @else {
                <button
                  class="btn btn-notify btn-lg"
                  (click)="watchProduct()"
                >
                  Notify Me When Available
                </button>
              }
            }
            <a routerLink="/products" class="btn btn-secondary btn-lg">
              Back to Products
            </a>
          </div>

          <div class="detail-meta">
            <span>Added: {{ formatDate(product()!.created_at) }}</span>
          </div>
        </div>
      </div>
    }

    @if (!loading() && !product()) {
      <div class="empty-state">
        <h3>Product not found</h3>
        <a routerLink="/products" class="btn btn-primary" style="margin-top: 1rem;">
          Browse Products
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

    .breadcrumb a:hover {
      text-decoration: underline;
    }

    .sep {
      margin: 0 0.5rem;
    }

    .detail-container {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 2rem;
      background: #fff;
      border-radius: var(--radius-lg);
      border: 1px solid var(--color-gray-200);
      overflow: hidden;
    }

    .detail-image {
      height: 400px;
      background: linear-gradient(135deg, var(--color-primary-light), var(--color-gray-100));
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .detail-icon {
      font-size: 5rem;
      font-weight: 700;
      color: var(--color-primary);
      opacity: 0.5;
    }

    .detail-info {
      padding: 2rem;
      display: flex;
      flex-direction: column;
    }

    .detail-category {
      font-size: 0.8125rem;
      font-weight: 600;
      color: var(--color-primary);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 0.5rem;
    }

    .detail-name {
      font-size: 1.75rem;
      font-weight: 700;
      color: var(--color-gray-900);
      margin-bottom: 0.75rem;
    }

    .detail-description {
      font-size: 0.9375rem;
      color: var(--color-gray-600);
      line-height: 1.6;
      margin-bottom: 1.5rem;
    }

    .detail-price {
      font-size: 2rem;
      font-weight: 700;
      color: var(--color-gray-900);
      margin-bottom: 1rem;
    }

    .stock-info {
      margin-bottom: 1.5rem;
    }

    .detail-actions {
      display: flex;
      gap: 0.75rem;
      margin-bottom: 1.5rem;
    }

    .detail-meta {
      margin-top: auto;
      font-size: 0.8125rem;
      color: var(--color-gray-400);
    }

    .btn-notify {
      background: transparent;
      color: var(--color-primary);
      border: 1.5px solid var(--color-primary);
      font-weight: 600;
      cursor: pointer;
      font-family: inherit;
      transition: all 0.15s ease;
    }

    .btn-notify:hover {
      background: var(--color-primary);
      color: #fff;
    }

    .btn-notify-active {
      background: var(--color-success, #16a34a);
      color: #fff;
      border: 1.5px solid var(--color-success, #16a34a);
      font-weight: 600;
      cursor: pointer;
      font-family: inherit;
      transition: all 0.15s ease;
    }

    .btn-notify-active:hover {
      background: var(--color-danger, #dc2626);
      border-color: var(--color-danger, #dc2626);
    }

    @media (max-width: 768px) {
      .detail-container {
        grid-template-columns: 1fr;
      }

      .detail-image {
        height: 250px;
      }
    }
  `],
})
export class ProductDetailComponent implements OnInit {
  product = signal<Product | null>(null);
  stock = signal<number | null>(null);
  loading = signal(true);
  watching = signal(false);

  private destroyRef = inject(DestroyRef);

  constructor(
    private route: ActivatedRoute,
    private api: ApiService,
    private auth: AuthService,
    private cart: CartService,
    private notify: NotificationService
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.api
      .getProduct(id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (product) => {
          this.product.set(product);
          this.loading.set(false);
          this.loadStock(product.id);
          this.checkWatchStatus(product.id);
        },
        error: () => {
          this.loading.set(false);
        },
      });
  }

  private loadStock(productId: string): void {
    this.api
      .getInventory(productId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (inv) => this.stock.set(inv.available),
        error: () => this.stock.set(null),
      });
  }

  private checkWatchStatus(productId: string): void {
    const email = this.auth.email();
    if (!email) return;
    this.api
      .isWatchingStock(productId, email)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => this.watching.set(res.watching),
        error: () => {},
      });
  }

  watchProduct(): void {
    const p = this.product();
    const email = this.auth.email();
    if (!p || !email) {
      this.notify.error('Please log in to get stock notifications');
      return;
    }
    this.api.watchStock(p.id, email).subscribe({
      next: () => {
        this.watching.set(true);
        this.notify.success('You will be notified when this item is back in stock');
      },
      error: () => this.notify.error('Failed to subscribe to notifications'),
    });
  }

  unwatchProduct(): void {
    const p = this.product();
    const email = this.auth.email();
    if (!p || !email) return;
    this.api.unwatchStock(p.id, email).subscribe({
      next: () => {
        this.watching.set(false);
        this.notify.success('Notification removed');
      },
      error: () => this.notify.error('Failed to unsubscribe'),
    });
  }

  addToCart(): void {
    const p = this.product();
    if (p) {
      this.cart.addItem(p.id, p.name, p.price);
      this.notify.success(`${p.name} added to cart`);
    }
  }

  formatDate(iso: string): string {
    return new Date(iso).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }
}
