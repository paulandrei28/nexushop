import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CartService } from '../../core/services/cart.service';
import { NotificationService } from '../../core/services/notification.service';

@Component({
  selector: 'app-cart',
  standalone: true,
  imports: [RouterLink],
  template: `
    <div class="page-header">
      <h1>Shopping Cart</h1>
    </div>

    @if (cart.cartItems().length === 0) {
      <div class="empty-state">
        <h3>Your cart is empty</h3>
        <p>Browse products and add items to your cart</p>
        <a routerLink="/products" class="btn btn-primary" style="margin-top: 1rem;">
          Browse Products
        </a>
      </div>
    } @else {
      <div class="cart-layout">
        <div class="cart-items">
          @for (item of cart.cartItems(); track item.productId) {
            <div class="card cart-item">
              <div class="cart-item-icon">
                {{ item.productName.charAt(0).toUpperCase() }}
              </div>
              <div class="cart-item-info">
                <h3 class="cart-item-name">{{ item.productName }}</h3>
                <span class="cart-item-price">\${{ item.unitPrice.toFixed(2) }} each</span>
              </div>
              <div class="cart-item-quantity">
                <button
                  class="qty-btn"
                  (click)="updateQty(item.productId, item.quantity - 1)"
                >
                  -
                </button>
                <span class="qty-value">{{ item.quantity }}</span>
                <button
                  class="qty-btn"
                  (click)="updateQty(item.productId, item.quantity + 1)"
                >
                  +
                </button>
              </div>
              <div class="cart-item-total">
                \${{ (item.unitPrice * item.quantity).toFixed(2) }}
              </div>
              <button
                class="btn-remove"
                (click)="removeItem(item.productId, item.productName)"
              >
                Remove
              </button>
            </div>
          }
        </div>

        <div class="cart-summary card">
          <h3>Order Summary</h3>
          <div class="summary-row">
            <span>Items ({{ cart.itemCount() }})</span>
            <span>\${{ cart.total().toFixed(2) }}</span>
          </div>
          <hr />
          <div class="summary-row summary-total">
            <span>Total</span>
            <span>\${{ cart.total().toFixed(2) }}</span>
          </div>
          <a routerLink="/checkout" class="btn btn-primary btn-lg" style="width: 100%; margin-top: 1rem;">
            Proceed to Checkout
          </a>
        </div>
      </div>
    }
  `,
  styles: [`
    .cart-layout {
      display: grid;
      grid-template-columns: 1fr 340px;
      gap: 1.5rem;
      align-items: start;
    }

    .cart-items {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .cart-item {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1rem;
    }

    .cart-item-icon {
      width: 3rem;
      height: 3rem;
      background: var(--color-primary-light);
      color: var(--color-primary);
      border-radius: var(--radius);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 1.25rem;
      flex-shrink: 0;
    }

    .cart-item-info {
      flex: 1;
      min-width: 0;
    }

    .cart-item-name {
      font-size: 0.9375rem;
      font-weight: 600;
      color: var(--color-gray-900);
      margin-bottom: 0.125rem;
    }

    .cart-item-price {
      font-size: 0.8125rem;
      color: var(--color-gray-500);
    }

    .cart-item-quantity {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .qty-btn {
      width: 2rem;
      height: 2rem;
      border: 1px solid var(--color-gray-300);
      background: #fff;
      border-radius: var(--radius);
      cursor: pointer;
      font-size: 1rem;
      font-weight: 600;
      color: var(--color-gray-700);
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.15s ease;
    }

    .qty-btn:hover {
      background: var(--color-gray-50);
      border-color: var(--color-gray-400);
    }

    .qty-value {
      font-size: 0.9375rem;
      font-weight: 600;
      min-width: 2rem;
      text-align: center;
    }

    .cart-item-total {
      font-size: 1rem;
      font-weight: 700;
      color: var(--color-gray-900);
      min-width: 80px;
      text-align: right;
    }

    .btn-remove {
      background: none;
      border: none;
      color: var(--color-danger);
      font-size: 0.8125rem;
      font-weight: 500;
      cursor: pointer;
      font-family: inherit;
      padding: 0.25rem;
    }

    .btn-remove:hover {
      text-decoration: underline;
    }

    .cart-summary {
      padding: 1.5rem;
      position: sticky;
      top: 5rem;
    }

    .cart-summary h3 {
      font-size: 1.0625rem;
      font-weight: 700;
      margin-bottom: 1rem;
    }

    .summary-row {
      display: flex;
      justify-content: space-between;
      font-size: 0.9375rem;
      color: var(--color-gray-600);
      margin-bottom: 0.5rem;
    }

    .summary-total {
      font-weight: 700;
      font-size: 1.125rem;
      color: var(--color-gray-900);
    }

    hr {
      border: none;
      border-top: 1px solid var(--color-gray-200);
      margin: 0.75rem 0;
    }

    @media (max-width: 768px) {
      .cart-layout {
        grid-template-columns: 1fr;
      }
    }
  `],
})
export class CartComponent {
  constructor(
    public cart: CartService,
    private notify: NotificationService
  ) {}

  updateQty(productId: string, quantity: number): void {
    this.cart.updateQuantity(productId, quantity);
  }

  removeItem(productId: string, name: string): void {
    this.cart.removeItem(productId);
    this.notify.show(`${name} removed from cart`, 'info');
  }
}
