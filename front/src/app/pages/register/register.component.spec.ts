import { TestBed } from '@angular/core/testing';
import { ComponentFixture } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { RegisterComponent } from './register.component';
import { AuthService } from '../../services/auth.service';
import { provideHttpClient } from '@angular/common/http';

describe('RegisterComponent', () => {
  let fixture: ComponentFixture<RegisterComponent>;
  let component: RegisterComponent;
  let authServiceMock: {
    register: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    authServiceMock = {
      register: vi.fn()
    };

    await TestBed.configureTestingModule({
      imports: [RegisterComponent],
      providers: [
        { provide: AuthService, useValue: authServiceMock },
        provideRouter([]),
        provideHttpClient()
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(RegisterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('コンポーネントが生成される', () => {
    expect(component).toBeTruthy();
  });

  it('全フォームフィールドが存在する', () => {
    expect(component.form.controls.username).toBeDefined();
    expect(component.form.controls.email).toBeDefined();
    expect(component.form.controls.password).toBeDefined();
    expect(component.form.controls.passwordConfirm).toBeDefined();
  });

  it('フォームが空の場合は送信しない', () => {
    component.submit();
    expect(authServiceMock.register).not.toHaveBeenCalled();
  });

  it('パスワードが一致しない場合はバリデーションエラー', () => {
    component.form.controls.username.setValue('testuser');
    component.form.controls.email.setValue('test@example.com');
    component.form.controls.password.setValue('password123');
    component.form.controls.passwordConfirm.setValue('different');
    component.form.controls.passwordConfirm.markAsTouched();
    component.submit();
    expect(component.hasPasswordMismatch).toBe(true);
    expect(authServiceMock.register).not.toHaveBeenCalled();
  });

  it('パスワードが一致する場合は送信できる', async () => {
    const mockUser = { id: 1, username: 'testuser', email: 'test@example.com', createdAt: '' };
    authServiceMock.register.mockReturnValue(of(mockUser));
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate').mockResolvedValue(true);

    component.form.controls.username.setValue('testuser');
    component.form.controls.email.setValue('test@example.com');
    component.form.controls.password.setValue('password123');
    component.form.controls.passwordConfirm.setValue('password123');
    component.submit();

    expect(authServiceMock.register).toHaveBeenCalledWith({
      username: 'testuser',
      email: 'test@example.com',
      password: 'password123'
    });
    expect(navigateSpy).toHaveBeenCalledWith(['/login']);
  });

  it('409エラー時に重複メッセージを表示', () => {
    authServiceMock.register.mockReturnValue(throwError(() => ({ status: 409 })));
    component.form.controls.username.setValue('testuser');
    component.form.controls.email.setValue('dup@example.com');
    component.form.controls.password.setValue('password123');
    component.form.controls.passwordConfirm.setValue('password123');
    component.submit();
    expect(component.errorMessage()).toContain('すでに登録されています');
  });
});
