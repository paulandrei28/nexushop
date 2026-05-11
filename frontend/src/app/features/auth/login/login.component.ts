import { Component, signal } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="login-container">
      <div class="card login-card">
        <div class="login-header">
          <div class="login-icon">N</div>
          <h1>Welcome to NexuShop</h1>
          <p>Enter your email to get started</p>
        </div>

        <form (ngSubmit)="login()">
          <div class="form-group">
            <label for="email">Email Address</label>
            <input
              id="email"
              type="email"
              class="form-control"
              [(ngModel)]="email"
              name="email"
              placeholder="demo&#64;nexushop.com"
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
              Logging in...
            } @else {
              Login
            }
          </button>
        </form>

        <p class="login-hint">
          This is a demo -- any email will work. No password required.
        </p>
      </div>
    </div>
  `,
  styles: [`
    .login-container {
      display: flex;
      justify-content: center;
      padding-top: 3rem;
    }

    .login-card {
      width: 100%;
      max-width: 400px;
      padding: 2rem;
    }

    .login-header {
      text-align: center;
      margin-bottom: 2rem;
    }

    .login-icon {
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

    .login-header h1 {
      font-size: 1.375rem;
      font-weight: 700;
      margin-bottom: 0.25rem;
    }

    .login-header p {
      color: var(--color-gray-500);
      font-size: 0.9375rem;
    }

    .login-hint {
      text-align: center;
      font-size: 0.8125rem;
      color: var(--color-gray-400);
      margin-top: 1.5rem;
    }
  `],
})
export class LoginComponent {
  email = '';
  submitting = signal(false);

  constructor(
    private api: ApiService,
    private auth: AuthService,
    private notify: NotificationService,
    private router: Router
  ) {}

  login(): void {
    if (!this.email.trim()) {
      this.notify.error('Please enter an email address');
      return;
    }

    this.submitting.set(true);
    this.api.login(this.email.trim()).subscribe({
      next: (res) => {
        this.auth.setAuth(res.access_token, this.email.trim());
        this.submitting.set(false);
        this.notify.success('Logged in successfully');
        this.router.navigate(['/products']);
      },
      error: (err) => {
        this.submitting.set(false);
        this.notify.error('Login failed. Please try again.');
      },
    });
  }
}
