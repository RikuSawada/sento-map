import { TestBed } from '@angular/core/testing';
import { ComponentFixture } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { LoginComponent } from './login.component';
import { AuthService } from '../../services/auth.service';
import { provideHttpClient } from '@angular/common/http';

describe('LoginComponent', () => {
  let fixture: ComponentFixture<LoginComponent>;
  let component: LoginComponent;
  let authServiceMock: {
    isLoggedIn: ReturnType<typeof vi.fn>;
    login: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    authServiceMock = {
      isLoggedIn: vi.fn().mockReturnValue(false),
      login: vi.fn()
    };

    await TestBed.configureTestingModule({
      imports: [LoginComponent],
      providers: [
        { provide: AuthService, useValue: authServiceMock },
        provideRouter([]),
        provideHttpClient()
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('コンポーネントが生成される', () => {
    expect(component).toBeTruthy();
  });

  it('email/password フォームが存在する', () => {
    expect(component.form.controls.email).toBeDefined();
    expect(component.form.controls.password).toBeDefined();
  });

  it('フォームが空の場合は送信しない', () => {
    component.submit();
    expect(authServiceMock.login).not.toHaveBeenCalled();
  });

  it('メールアドレス形式が不正な場合はバリデーションエラー', () => {
    component.form.controls.email.setValue('invalid-email');
    component.form.controls.password.setValue('password123');
    component.submit();
    expect(component.emailControl.hasError('email')).toBe(true);
    expect(authServiceMock.login).not.toHaveBeenCalled();
  });

  it('401エラー時にエラーメッセージを表示', () => {
    authServiceMock.login.mockReturnValue(throwError(() => ({ status: 401 })));
    component.form.controls.email.setValue('test@example.com');
    component.form.controls.password.setValue('password123');
    component.submit();
    expect(component.errorMessage()).toBe('メールアドレスまたはパスワードが違います');
  });

  it('ログイン成功後に /map に遷移', async () => {
    authServiceMock.login.mockReturnValue(of({ accessToken: 'token', tokenType: 'bearer' }));
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate').mockResolvedValue(true);
    component.form.controls.email.setValue('test@example.com');
    component.form.controls.password.setValue('password123');
    component.submit();
    expect(navigateSpy).toHaveBeenCalledWith(['/map']);
  });

  it('ログイン済みなら ngOnInit で /map に遷移', async () => {
    authServiceMock.isLoggedIn.mockReturnValue(true);
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate').mockResolvedValue(true);
    component.ngOnInit();
    expect(navigateSpy).toHaveBeenCalledWith(['/map']);
  });
});
