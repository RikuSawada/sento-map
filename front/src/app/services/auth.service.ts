import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map, tap } from 'rxjs';
import { environment } from '../../environments/environment';
import { User, LoginRequest, RegisterRequest, TokenResponse } from '../models';

function toCamel(o: unknown): unknown {
  if (Array.isArray(o)) return o.map(toCamel);
  if (o !== null && typeof o === 'object') {
    return Object.fromEntries(
      Object.entries(o as Record<string, unknown>).map(([k, v]) => [
        k.replace(/_([a-z])/g, (_, c: string) => c.toUpperCase()),
        toCamel(v)
      ])
    );
  }
  return o;
}

const TOKEN_KEY = 'access_token';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  register(data: RegisterRequest): Observable<User> {
    return this.http
      .post<unknown>(`${this.apiUrl}/auth/register`, data)
      .pipe(map(res => toCamel(res) as User));
  }

  login(data: LoginRequest): Observable<TokenResponse> {
    // OAuth2PasswordRequestForm expects application/x-www-form-urlencoded
    // フィールド名は username と password (email を username として送る)
    const body = new HttpParams()
      .set('username', data.email)
      .set('password', data.password);
    return this.http
      .post<unknown>(`${this.apiUrl}/auth/login`, body.toString(), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })
      .pipe(
        map(res => toCamel(res) as TokenResponse),
        tap(token => localStorage.setItem(TOKEN_KEY, token.accessToken))
      );
  }

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
  }

  getMe(): Observable<User> {
    return this.http
      .get<unknown>(`${this.apiUrl}/auth/me`)
      .pipe(map(res => toCamel(res) as User));
  }

  isLoggedIn(): boolean {
    return localStorage.getItem(TOKEN_KEY) !== null;
  }

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }
}
