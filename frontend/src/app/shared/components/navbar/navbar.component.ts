import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { CartService } from '../../../core/services/cart.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  template: `
    <nav class="navbar">
      <div class="container navbar-inner">
        <a class="navbar-brand" routerLink="/products">
          <span class="brand-icon">N</span>
          <span class="brand-text">NexuShop</span>
        </a>

        <div class="navbar-links">
          <a routerLink="/products" routerLinkActive="active"
             [routerLinkActiveOptions]="{ exact: true }">
            Products
          </a>

          @if (auth.isLoggedIn()) {
            <a routerLink="/orders" routerLinkActive="active">
              Orders
            </a>
          }

          <a routerLink="/cart" routerLinkActive="active" class="cart-link">
            Cart
            @if (cart.itemCount() > 0) {
              <span class="cart-badge">{{ cart.itemCount() }}</span>
            }
          </a>
        </div>

        <div class="navbar-actions">
          @if (auth.isLoggedIn()) {
            <span class="user-name">{{ auth.name() || auth.email() }}</span>
            <button class="btn btn-secondary btn-sm" (click)="auth.logout()">
              Logout
            </button>
          } @else {
            <a routerLink="/login" class="btn btn-secondary btn-sm">Sign In</a>
            <a routerLink="/register" class="btn btn-primary btn-sm">Register</a>
          }
        </div>
      </div>
    </nav>
  `,
  styles: [`
    .navbar {
      background: #fff;
      border-bottom: 1px solid var(--color-gray-200);
      position: sticky;
      top: 0;
      z-index: 100;
      box-shadow: var(--shadow-sm);
    }

    .navbar-inner {
      display: flex;
      align-items: center;
      height: 3.5rem;
      gap: 2rem;
    }

    .navbar-brand {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-weight: 700;
      font-size: 1.125rem;
      color: var(--color-gray-900);
      text-decoration: none;
    }

    .brand-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 2rem;
      height: 2rem;
      background: var(--color-primary);
      color: #fff;
      border-radius: 6px;
      font-size: 0.875rem;
      font-weight: 700;
    }

    .navbar-links {
      display: flex;
      gap: 1.5rem;
      flex: 1;
    }

    .navbar-links a {
      font-size: 0.875rem;
      font-weight: 500;
      color: var(--color-gray-600);
      text-decoration: none;
      padding: 0.25rem 0;
      border-bottom: 2px solid transparent;
      transition: all 0.15s ease;
    }

    .navbar-links a:hover,
    .navbar-links a.active {
      color: var(--color-primary);
      border-bottom-color: var(--color-primary);
    }

    .cart-link {
      position: relative;
    }

    .cart-badge {
      position: absolute;
      top: -8px;
      right: -12px;
      background: var(--color-primary);
      color: #fff;
      font-size: 0.6875rem;
      font-weight: 700;
      width: 18px;
      height: 18px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .navbar-actions {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .user-name {
      font-size: 0.8125rem;
      color: var(--color-gray-500);
      font-weight: 500;
    }
  `],
})
export class NavbarComponent {
  constructor(
    public auth: AuthService,
    public cart: CartService
  ) {}
}
