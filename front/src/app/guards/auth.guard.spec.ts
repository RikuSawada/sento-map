import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { authGuard, guestGuard } from './auth.guard';
import { AuthService } from '../services/auth.service';
import { ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';

describe('authGuard', () => {
  let authServiceMock: { isLoggedIn: ReturnType<typeof vi.fn> };
  let routerMock: { createUrlTree: ReturnType<typeof vi.fn> };

  const dummyRoute = {} as ActivatedRouteSnapshot;
  const dummyState = {} as RouterStateSnapshot;

  beforeEach(() => {
    authServiceMock = { isLoggedIn: vi.fn() };
    routerMock = { createUrlTree: vi.fn().mockReturnValue('/login') };

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: authServiceMock },
        { provide: Router, useValue: routerMock }
      ]
    });
  });

  it('ログイン済みなら true を返す', () => {
    authServiceMock.isLoggedIn.mockReturnValue(true);
    const result = TestBed.runInInjectionContext(() => authGuard(dummyRoute, dummyState));
    expect(result).toBe(true);
  });

  it('未ログインなら /login へのリダイレクトを返す', () => {
    authServiceMock.isLoggedIn.mockReturnValue(false);
    routerMock.createUrlTree.mockReturnValue('/login-url-tree');
    const result = TestBed.runInInjectionContext(() => authGuard(dummyRoute, dummyState));
    expect(routerMock.createUrlTree).toHaveBeenCalledWith(['/login']);
    expect(result).toBe('/login-url-tree');
  });
});

describe('guestGuard', () => {
  let authServiceMock: { isLoggedIn: ReturnType<typeof vi.fn> };
  let routerMock: { createUrlTree: ReturnType<typeof vi.fn> };

  const dummyRoute = {} as ActivatedRouteSnapshot;
  const dummyState = {} as RouterStateSnapshot;

  beforeEach(() => {
    authServiceMock = { isLoggedIn: vi.fn() };
    routerMock = { createUrlTree: vi.fn().mockReturnValue('/map') };

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: authServiceMock },
        { provide: Router, useValue: routerMock }
      ]
    });
  });

  it('未ログインなら true を返す', () => {
    authServiceMock.isLoggedIn.mockReturnValue(false);
    const result = TestBed.runInInjectionContext(() => guestGuard(dummyRoute, dummyState));
    expect(result).toBe(true);
  });

  it('ログイン済みなら /map へのリダイレクトを返す', () => {
    authServiceMock.isLoggedIn.mockReturnValue(true);
    routerMock.createUrlTree.mockReturnValue('/map-url-tree');
    const result = TestBed.runInInjectionContext(() => guestGuard(dummyRoute, dummyState));
    expect(routerMock.createUrlTree).toHaveBeenCalledWith(['/map']);
    expect(result).toBe('/map-url-tree');
  });
});
