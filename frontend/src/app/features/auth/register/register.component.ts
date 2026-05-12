import { Component, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [FormsModule, RouterLink],
  template: `
    <div class="register-container">
      <div class="card register-card">
        <div class="register-header">
          <div class="register-icon">N</div>
          <h1>Create Account</h1>
          <p>Join NexuShop today</p>
        </div>

        <form (ngSubmit)="register()">
          <div class="form-group">
            <label for="name">Full Name</label>
            <input
              id="name"
              type="text"
              class="form-control"
              [(ngModel)]="name"
              name="name"
              placeholder="John Doe"
              required
            />
          </div>

          <div class="form-group">
            <label for="email">Email Address</label>
            <input
              id="email"
              type="email"
              class="form-control"
              [(ngModel)]="email"
              name="email"
              placeholder="you&#64;example.com"
              required
            />
          </div>

          <div class="form-group">
            <label for="password">Password</label>
            <input
              id="password"
              type="password"
              class="form-control"
              [(ngModel)]="password"
              name="password"
              placeholder="Min. 8 characters"
              required
            />
          </div>

          <div class="form-group">
            <label for="confirmPassword">Confirm Password</label>
            <input
              id="confirmPassword"
              type="password"
              class="form-control"
              [(ngModel)]="confirmPassword"
              name="confirmPassword"
              placeholder="Re-enter password"
              required
            />
          </div>

          <button
            type="submit"
            class="btn btn-primary btn-lg"
            style="width: 100%;"
            [disabled]="submitting()"
          >
            @if (submitting()) {
              Creating Account...
            } @else {
              Create Account
            }
          </button>
        </form>

        <p class="register-hint">
          Already have an account?
          <a routerLink="/login" class="auth-link">Sign in</a>
        </p>
      </div>
    </div>
  `,
  styles: [`
    .register-container {
      display: flex;
      justify-content: center;
      padding-top: 3rem;
    }

    .register-card {
      width: 100%;
      max-width: 400px;
      padding: 2rem;
    }

    .register-header {
      text-align: center;
      margin-bottom: 2rem;
    }

    .register-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 3rem;
      height: 3rem;
      background: var(--color-primary);
      color: #fff;
      border-radius: 10px;
      font-size: 1.25rem;
      font-weight: 700;
      margin-bottom: 1rem;
    }

    .register-header h1 {
      font-size: 1.375rem;
      font-weight: 700;
      margin-bottom: 0.25rem;
    }

    .register-header p {
      color: var(--color-gray-500);
      font-size: 0.9375rem;
    }

    .register-hint {
      text-align: center;
      font-size: 0.875rem;
      color: var(--color-gray-500);
      margin-top: 1.5rem;
    }

    .auth-link {
      color: var(--color-primary);
      text-decoration: none;
      font-weight: 600;
    }

    .auth-link:hover {
      text-decoration: underline;
    }
  `],
})
export class RegisterComponent {
  name = '';
  email = '';
  password = '';
  confirmPassword = '';
  submitting = signal(false);

  constructor(
    private api: ApiService,
    private auth: AuthService,
    private notify: NotificationService,
    private router: Router
  ) {}

  register(): void {
    if (!this.name.trim()) {
      this.notify.error('Please enter your name');
      return;
    }
    if (!this.email.trim()) {
      this.notify.error('Please enter an email address');
      return;
    }
    if (this.password.length < 8) {
      this.notify.error('Password must be at least 8 characters');
      return;
    }
    if (this.password !== this.confirmPassword) {
      this.notify.error('Passwords do not match');
      return;
    }

    this.submitting.set(true);
    this.api
      .register(this.email.trim(), this.password, this.name.trim())
      .subscribe({
        next: (res) => {
          this.auth.setAuth(res.access_token, res.user.email, res.user.name);
          this.submitting.set(false);
          this.notify.success('Account created successfully!');
          this.router.navigate(['/products']);
        },
        error: (err) => {
          this.submitting.set(false);
          const msg =
            err?.error?.error || 'Registration failed. Please try again.';
          this.notify.error(msg);
        },
      });
  }
}
