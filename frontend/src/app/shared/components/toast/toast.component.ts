import { Component } from '@angular/core';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-toast',
  standalone: true,
  template: `
    <div class="toast-container">
      @for (toast of notification.toasts(); track toast.id) {
        <div class="toast toast-{{ toast.type }}">
          {{ toast.message }}
        </div>
      }
    </div>
  `,
})
export class ToastComponent {
  constructor(public notification: NotificationService) {}
}
