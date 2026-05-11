import { Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { ApiService } from '../../../core/services/api.service';
import { CartService } from '../../../core/services/cart.service';
import { NotificationService } from '../../../core/services/notification.service';
import { Product } from '../../../core/models/product.model';

@Component({
  selector: 'app-product-list',
  standalone: true,
  imports: [RouterLink, FormsModule],
  template: `
    <div class="page-header">
      <h1>Products</h1>
      <p>Browse our catalog</p>
    </div>

    <!-- Filters -->
    <div class="filters">
      <div class="search-box">
        <input
          type="text"
          class="form-control"
          placeholder="Search products..."
          [ngModel]="searchQuery()"
          (ngModelChange)="onSearch($event)"
        />
      </div>
      <div class="category-chips">
        <button
          class="chip"
          [class.active]="!selectedCategory()"
          (click)="filterByCategory('')"
        >
          All
        </button>
        @for (cat of categories(); track cat) {
          <button
            class="chip"
            [class.active]="selectedCategory() === cat"
            (click)="filterByCategory(cat)"
          >
            {{ cat }}
          </button>
        }
      </div>
    </div>

    <!-- Loading State -->
    @if (loading()) {
      <div class="product-grid">
        @for (i of [1, 2, 3, 4, 5, 6]; track i) {
          <div class="card product-card">
            <div class="skeleton" style="height: 160px;"></div>
            <div style="padding: 1rem;">
              <div class="skeleton" style="height: 1.25rem; width: 70%; margin-bottom: 0.5rem;"></div>
              <div class="skeleton" style="height: 1rem; width: 40%;"></div>
            </div>
          </div>
        }
      </div>
    }

    <!-- Products Grid -->
    @if (!loading() && products().length > 0) {
      <div class="product-grid">
        @for (product of products(); track product.id) {
          <div class="card product-card">
            <div class="product-image">
              <span class="product-icon">{{ product.category.charAt(0).toUpperCase() }}</span>
            </div>
            <div class="product-body">
              <span class="product-category">{{ product.category }}</span>
              <a [routerLink]="['/products', product.id]" class="product-name">
                {{ product.name }}
              </a>
              <p class="product-description">
                {{ product.description || 'No description available' }}
              </p>
              <div class="product-footer">
                <span class="product-price">\${{ product.price.toFixed(2) }}</span>
                <button
                  class="btn btn-primary btn-sm"
                  (click)="addToCart(product)"
                >
                  Add to Cart
                </button>
              </div>
            </div>
          </div>
        }
      </div>
    }

    <!-- Empty State -->
    @if (!loading() && products().length === 0) {
      <div class="empty-state">
        <h3>No products found</h3>
        <p>Try adjusting your search or filters</p>
      </div>
    }
  `,
  styles: [`
    .filters {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      margin-bottom: 1.5rem;
    }

    .search-box {
      max-width: 400px;
    }

    .category-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    .chip {
      padding: 0.375rem 0.875rem;
      font-size: 0.8125rem;
      font-weight: 500;
      background: #fff;
      border: 1px solid var(--color-gray-300);
      border-radius: 9999px;
      cursor: pointer;
      color: var(--color-gray-600);
      font-family: inherit;
      transition: all 0.15s ease;
    }

    .chip:hover {
      border-color: var(--color-primary);
      color: var(--color-primary);
    }

    .chip.active {
      background: var(--color-primary);
      color: #fff;
      border-color: var(--color-primary);
    }

    .product-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 1.25rem;
    }

    .product-card {
      display: flex;
      flex-direction: column;
      transition: box-shadow 0.2s ease;
      overflow: hidden;
    }

    .product-card:hover {
      box-shadow: var(--shadow-md);
    }

    .product-image {
      height: 160px;
      background: linear-gradient(135deg, var(--color-primary-light), var(--color-gray-100));
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .product-icon {
      font-size: 2.5rem;
      font-weight: 700;
      color: var(--color-primary);
      opacity: 0.6;
    }

    .product-body {
      padding: 1rem;
      flex: 1;
      display: flex;
      flex-direction: column;
    }

    .product-category {
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--color-primary);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 0.25rem;
    }

    .product-name {
      font-size: 1rem;
      font-weight: 600;
      color: var(--color-gray-900);
      text-decoration: none;
      margin-bottom: 0.375rem;
    }

    .product-name:hover {
      color: var(--color-primary);
      text-decoration: none;
    }

    .product-description {
      font-size: 0.8125rem;
      color: var(--color-gray-500);
      flex: 1;
      margin-bottom: 0.75rem;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .product-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .product-price {
      font-size: 1.125rem;
      font-weight: 700;
      color: var(--color-gray-900);
    }
  `],
})
export class ProductListComponent implements OnInit {
  products = signal<Product[]>([]);
  categories = signal<string[]>([]);
  loading = signal(true);
  searchQuery = signal('');
  selectedCategory = signal('');

  private destroyRef = inject(DestroyRef);
  private searchSubject = new Subject<string>();

  constructor(
    private api: ApiService,
    private cart: CartService,
    private notify: NotificationService
  ) {}

  ngOnInit(): void {
    this.loadProducts();
    this.loadCategories();

    this.searchSubject
      .pipe(
        debounceTime(350),
        distinctUntilChanged(),
        switchMap((query) => {
          const params: { category?: string; search?: string } = {};
          if (this.selectedCategory()) params.category = this.selectedCategory();
          if (query) params.search = query;
          return this.api.getProducts(params);
        }),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe({
        next: (res) => {
          this.products.set(res.items);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.notify.error('Failed to load products');
        },
      });
  }

  loadProducts(): void {
    this.loading.set(true);
    const params: { category?: string; search?: string } = {};
    if (this.selectedCategory()) params.category = this.selectedCategory();
    if (this.searchQuery()) params.search = this.searchQuery();

    this.api
      .getProducts(params)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => {
          this.products.set(res.items);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.notify.error('Failed to load products');
        },
      });
  }

  loadCategories(): void {
    this.api
      .getCategories()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => this.categories.set(res.categories),
      });
  }

  onSearch(query: string): void {
    this.searchQuery.set(query);
    this.searchSubject.next(query);
  }

  filterByCategory(category: string): void {
    this.selectedCategory.set(category);
    this.loadProducts();
  }

  addToCart(product: Product): void {
    this.cart.addItem(product.id, product.name, product.price);
    this.notify.success(`${product.name} added to cart`);
  }
}
