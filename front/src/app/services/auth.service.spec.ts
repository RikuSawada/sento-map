import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { AuthService } from './auth.service';
import { RegisterRequest } from '../models';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();

    TestBed.configureTestingModule({
      providers: [
        AuthService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ]
    });
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('サービスが生成される', () => {
    expect(service).toBeTruthy();
  });

  describe('register', () => {
    it('POST /auth/register を呼ぶ', () => {
      const data: RegisterRequest = { username: 'taro', email: 'taro@example.com', password: 'pass1234' };
      service.register(data).subscribe();
      const req = httpMock.expectOne(r => r.url.includes('/auth/register') && r.method === 'POST');
      expect(req.request.method).toBe('POST');
      req.flush({
        id: 1,
        username: 'taro',
        email: 'taro@example.com',
        created_at: '2024-01-01T00:00:00'
      });
    });

    it('正しいペイロードを送信する', () => {
      const data: RegisterRequest = { username: 'hanako', email: 'hanako@example.com', password: 'secret' };
      service.register(data).subscribe();
      const req = httpMock.expectOne(r => r.url.includes('/auth/register'));
      expect(req.request.body).toEqual(data);
      req.flush({ id: 2, username: 'hanako', email: 'hanako@example.com', created_at: '2024-01-01T00:00:00' });
    });

    it('snake_case レスポンスを camelCase に変換する', () => {
      let result: unknown;
      service.register({ username: 'jiro', email: 'jiro@example.com', password: 'pw' }).subscribe(r => { result = r; });
      const req = httpMock.expectOne(r => r.url.includes('/auth/register'));
      req.flush({ id: 3, username: 'jiro', email: 'jiro@example.com', created_at: '2024-02-01T00:00:00' });
      const user = result as Record<string, unknown>;
      expect(user['createdAt']).toBe('2024-02-01T00:00:00');
    });
  });

  describe('login', () => {
    it('POST /auth/login を application/x-www-form-urlencoded で呼ぶ', () => {
      service.login({ email: 'taro@example.com', password: 'pass1234' }).subscribe();
      const req = httpMock.expectOne(r => r.url.includes('/auth/login') && r.method === 'POST');
      expect(req.request.headers.get('Content-Type')).toBe('application/x-www-form-urlencoded');
      req.flush({ access_token: 'tok123', token_type: 'bearer' });
    });

    it('username=email, password を x-www-form-urlencoded ボディで送信する', () => {
      service.login({ email: 'taro@example.com', password: 'mypassword' }).subscribe();
      const req = httpMock.expectOne(r => r.url.includes('/auth/login'));
      const body = req.request.body as string;
      // HttpParams.toString() は @ をエンコードせずそのまま出力する
      expect(body).toContain('username=taro@example.com');
      expect(body).toContain('password=mypassword');
      req.flush({ access_token: 'tok456', token_type: 'bearer' });
    });

    it('ログイン成功後に localStorage に access_token を保存する', () => {
      service.login({ email: 'taro@example.com', password: 'pass1234' }).subscribe();
      const req = httpMock.expectOne(r => r.url.includes('/auth/login'));
      req.flush({ access_token: 'mytoken', token_type: 'bearer' });
      expect(localStorage.getItem('access_token')).toBe('mytoken');
    });

    it('ログイン成功後に accessToken (camelCase) を返す', () => {
      let result: unknown;
      service.login({ email: 'taro@example.com', password: 'pass1234' }).subscribe(r => { result = r; });
      const req = httpMock.expectOne(r => r.url.includes('/auth/login'));
      req.flush({ access_token: 'tok789', token_type: 'bearer' });
      const token = result as Record<string, unknown>;
      expect(token['accessToken']).toBe('tok789');
      expect(token['tokenType']).toBe('bearer');
    });
  });

  describe('logout', () => {
    it('localStorage から access_token を削除する', () => {
      localStorage.setItem('access_token', 'dummy-token');
      service.logout();
      expect(localStorage.getItem('access_token')).toBeNull();
    });

    it('トークンがない状態でも例外を投げない', () => {
      expect(() => service.logout()).not.toThrow();
    });
  });

  describe('isLoggedIn', () => {
    it('access_token がある場合 true を返す', () => {
      localStorage.setItem('access_token', 'some-token');
      expect(service.isLoggedIn()).toBe(true);
    });

    it('access_token がない場合 false を返す', () => {
      localStorage.removeItem('access_token');
      expect(service.isLoggedIn()).toBe(false);
    });
  });

  describe('getToken', () => {
    it('localStorage の access_token を返す', () => {
      localStorage.setItem('access_token', 'my-jwt-token');
      expect(service.getToken()).toBe('my-jwt-token');
    });

    it('access_token がない場合 null を返す', () => {
      localStorage.removeItem('access_token');
      expect(service.getToken()).toBeNull();
    });
  });

  describe('getMe', () => {
    it('GET /auth/me を呼ぶ', () => {
      service.getMe().subscribe();
      const req = httpMock.expectOne(r => r.url.includes('/auth/me') && r.method === 'GET');
      expect(req.request.method).toBe('GET');
      req.flush({ id: 1, username: 'taro', email: 'taro@example.com', created_at: '2024-01-01T00:00:00' });
    });

    it('snake_case レスポンスを camelCase に変換する', () => {
      let result: unknown;
      service.getMe().subscribe(r => { result = r; });
      const req = httpMock.expectOne(r => r.url.includes('/auth/me'));
      req.flush({ id: 1, username: 'taro', email: 'taro@example.com', created_at: '2024-05-01T00:00:00' });
      const user = result as Record<string, unknown>;
      expect(user['createdAt']).toBe('2024-05-01T00:00:00');
    });
  });
});
