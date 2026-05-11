import { Component, OnInit, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';
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
            <button
              class="btn btn-primary btn-lg"
              (click)="addToCart()"
              [disabled]="stock() === 0"
            >
              Add to Cart
            </button>
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

  constructor(
    private route: ActivatedRoute,
    private api: ApiService,
    private cart: CartService,
    private notify: NotificationService
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.api.getProduct(id).subscribe({
      next: (product) => {
        this.product.set(product);
        this.loading.set(false);
        this.loadStock(product.id);
      },
      error: () => {
        this.loading.set(false);
      },
    });
  }

  private loadStock(productId: string): void {
    this.api.getInventory(productId).subscribe({
      next: (inv) => this.stock.set(inv.quantity - inv.reserved),
      error: () => this.stock.set(null),
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
