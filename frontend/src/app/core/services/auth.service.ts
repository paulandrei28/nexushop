import { Injectable, signal, computed } from '@angular/core';

interface AuthState {
  token: string | null;
  email: string | null;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private state = signal<AuthState>(this.loadState());

  readonly isLoggedIn = computed(() => !!this.state().token);
  readonly email = computed(() => this.state().email);
  readonly token = computed(() => this.state().token);

  setAuth(token: string, email: string): void {
    const newState: AuthState = { token, email };
    this.state.set(newState);
    localStorage.setItem('nexushop_auth', JSON.stringify(newState));
  }

  logout(): void {
    this.state.set({ token: null, email: null });
    localStorage.removeItem('nexushop_auth');
  }

  getToken(): string | null {
    return this.state().token;
  }

  private loadState(): AuthState {
    try {
      const stored = localStorage.getItem('nexushop_auth');
      if (stored) {
        return JSON.parse(stored);
      }
    } catch {
      // Ignore parse errors
    }
    return { token: null, email: null };
  }
}
