import { Component, inject, signal } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  ValidatorFn,
  Validators
} from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';

const passwordMatchValidator: ValidatorFn = (control: AbstractControl): ValidationErrors | null => {
  const password = control.get('password');
  const passwordConfirm = control.get('passwordConfirm');
  if (!password || !passwordConfirm) return null;
  return password.value !== passwordConfirm.value ? { passwordMismatch: true } : null;
};

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './register.component.html',
  styleUrl: './register.component.css'
})
export class RegisterComponent {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  readonly form = this.fb.nonNullable.group(
    {
      username: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(50)]],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      passwordConfirm: ['', [Validators.required]]
    },
    { validators: passwordMatchValidator }
  );

  readonly errorMessage = signal<string | null>(null);
  readonly loading = signal(false);

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    this.errorMessage.set(null);

    const { username, email, password } = this.form.getRawValue();

    this.authService.register({ username, email, password }).subscribe({
      next: () => {
        void this.router.navigate(['/login']);
      },
      error: (err: { status?: number }) => {
        this.loading.set(false);
        if (err.status === 409) {
          this.errorMessage.set('このメールアドレスはすでに登録されています');
        } else {
          this.errorMessage.set('登録に失敗しました。しばらく後でお試しください');
        }
      }
    });
  }

  get usernameControl() {
    return this.form.controls.username;
  }

  get emailControl() {
    return this.form.controls.email;
  }

  get passwordControl() {
    return this.form.controls.password;
  }

  get passwordConfirmControl() {
    return this.form.controls.passwordConfirm;
  }

  get hasPasswordMismatch(): boolean {
    return (
      this.form.hasError('passwordMismatch') &&
      this.passwordConfirmControl.touched
    );
  }
}
