import { Component, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';
import { CartService } from '../../core/services/cart.service';
import { NotificationService } from '../../core/services/notification.service';

@Component({
  selector: 'app-checkout',
  standalone: true,
  imports: [RouterLink, FormsModule],
  template: `
    @if (cart.cartItems().length === 0) {
      <div class="empty-state">
        <h3>Nothing to check out</h3>
        <p>Add some products to your cart first</p>
        <a routerLink="/products" class="btn btn-primary" style="margin-top: 1rem;">
          Browse Products
        </a>
      </div>
    } @else {
      <div class="page-header">
        <h1>Checkout</h1>
      </div>

      @if (!auth.isLoggedIn()) {
        <div class="card" style="padding: 2rem; text-align: center; margin-bottom: 1.5rem;">
          <h3 style="margin-bottom: 0.5rem;">Login Required</h3>
          <p style="color: var(--color-gray-500); margin-bottom: 1rem;">
            Please log in to complete your order
          </p>
          <a routerLink="/login" class="btn btn-primary">Login</a>
        </div>
      } @else {
        <div class="checkout-layout">
          <div class="checkout-form card">
            <h3>Customer Information</h3>
            <div class="form-group">
              <label for="email">Email Address</label>
              <input
                id="email"
                type="email"
                class="form-control"
                [ngModel]="email()"
                (ngModelChange)="email.set($event)"
                placeholder="your@email.com"
              />
            </div>

            <h3 style="margin-top: 1.5rem;">Order Items</h3>
            <div class="checkout-items">
              @for (item of cart.cartItems(); track item.productId) {
                <div class="checkout-item">
                  <span class="item-name">
                    {{ item.productName }}
                    <span class="item-qty">x{{ item.quantity }}</span>
                  </span>
                  <span class="item-price">
                    \${{ (item.unitPrice * item.quantity).toFixed(2) }}
                  </span>
                </div>
              }
            </div>

            <hr style="margin: 1rem 0;" />
            <div class="checkout-total">
              <span>Total</span>
              <span>\${{ cart.total().toFixed(2) }}</span>
            </div>

            <button
              class="btn btn-primary btn-lg"
              style="width: 100%; margin-top: 1.5rem;"
              (click)="placeOrder()"
              [disabled]="submitting()"
            >
              @if (submitting()) {
                Placing Order...
              } @else {
                Place Order
              }
            </button>
          </div>
        </div>
      }
    }
  `,
  styles: [`
    .checkout-layout {
      max-width: 600px;
    }

    .checkout-form {
      padding: 1.5rem;
    }

    .checkout-form h3 {
      font-size: 1.0625rem;
      font-weight: 700;
      margin-bottom: 1rem;
    }

    .checkout-items {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .checkout-item {
      display: flex;
      justify-content: space-between;
      font-size: 0.9375rem;
    }

    .item-name {
      color: var(--color-gray-700);
    }

    .item-qty {
      color: var(--color-gray-400);
      margin-left: 0.25rem;
    }

    .item-price {
      font-weight: 600;
      color: var(--color-gray-900);
    }

    .checkout-total {
      display: flex;
      justify-content: space-between;
      font-size: 1.125rem;
      font-weight: 700;
      color: var(--color-gray-900);
    }
  `],
})
export class CheckoutComponent {
  email = signal('');
  submitting = signal(false);

  constructor(
    public auth: AuthService,
    public cart: CartService,
    private api: ApiService,
    private notify: NotificationService,
    private router: Router
  ) {
    const userEmail = this.auth.email();
    if (userEmail) {
      this.email.set(userEmail);
    }
  }

  placeOrder(): void {
    const emailVal = this.email().trim();
    if (!emailVal) {
      this.notify.error('Please enter an email address');
      return;
    }

    this.submitting.set(true);

    const items = this.cart.cartItems().map((item) => ({
      product_id: item.productId,
      product_name: item.productName,
      quantity: item.quantity,
      unit_price: item.unitPrice,
    }));

    this.api.createOrder({ customer_email: emailVal, items }).subscribe({
      next: (order) => {
        this.submitting.set(false);
        this.cart.clear();
        this.notify.success('Order placed successfully!');
        this.router.navigate(['/orders', order.id]);
      },
      error: (err) => {
        this.submitting.set(false);
        const msg = err?.error?.detail || err?.error?.error || 'Failed to place order';
        this.notify.error(msg);
      },
    });
  }
}
