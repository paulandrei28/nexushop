import { Injectable, signal, computed } from '@angular/core';
import { CartItem } from '../models/cart.model';

@Injectable({ providedIn: 'root' })
export class CartService {
  private items = signal<CartItem[]>(this.loadCart());

  readonly cartItems = computed(() => this.items());
  readonly itemCount = computed(() =>
    this.items().reduce((sum, item) => sum + item.quantity, 0)
  );
  readonly total = computed(() =>
    this.items().reduce((sum, item) => sum + item.unitPrice * item.quantity, 0)
  );

  addItem(productId: string, productName: string, unitPrice: number): void {
    const current = this.items();
    const existing = current.find((item) => item.productId === productId);

    if (existing) {
      this.items.set(
        current.map((item) =>
          item.productId === productId
            ? { ...item, quantity: item.quantity + 1 }
            : item
        )
      );
    } else {
      this.items.set([
        ...current,
        { productId, productName, unitPrice, quantity: 1 },
      ]);
    }
    this.saveCart();
  }

  removeItem(productId: string): void {
    this.items.set(this.items().filter((item) => item.productId !== productId));
    this.saveCart();
  }

  updateQuantity(productId: string, quantity: number): void {
    if (quantity <= 0) {
      this.removeItem(productId);
      return;
    }
    this.items.set(
      this.items().map((item) =>
        item.productId === productId ? { ...item, quantity } : item
      )
    );
    this.saveCart();
  }

  clear(): void {
    this.items.set([]);
    this.saveCart();
  }

  private saveCart(): void {
    localStorage.setItem('nexushop_cart', JSON.stringify(this.items()));
  }

  private loadCart(): CartItem[] {
    try {
      const stored = localStorage.getItem('nexushop_cart');
      if (stored) {
        return JSON.parse(stored);
      }
    } catch {
      // Ignore parse errors
    }
    return [];
  }
}
