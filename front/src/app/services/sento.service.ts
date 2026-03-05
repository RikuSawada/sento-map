import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../environments/environment';
import { Sento, SentoListResponse } from '../models';

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

export interface SentoQueryParams {
  lat_min?: number;
  lat_max?: number;
  lng_min?: number;
  lng_max?: number;
  page?: number;
  per_page?: number;
  prefecture?: string;
}

@Injectable({
  providedIn: 'root'
})
export class SentoService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  getSentos(params?: SentoQueryParams): Observable<SentoListResponse> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.lat_min !== undefined) httpParams = httpParams.set('lat_min', params.lat_min);
      if (params.lat_max !== undefined) httpParams = httpParams.set('lat_max', params.lat_max);
      if (params.lng_min !== undefined) httpParams = httpParams.set('lng_min', params.lng_min);
      if (params.lng_max !== undefined) httpParams = httpParams.set('lng_max', params.lng_max);
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page);
      if (params.per_page !== undefined) httpParams = httpParams.set('per_page', params.per_page);
      if (params.prefecture !== undefined) httpParams = httpParams.set('prefecture', params.prefecture);
    }
    return this.http
      .get<unknown>(`${this.apiUrl}/sentos`, { params: httpParams })
      .pipe(map(res => toCamel(res) as SentoListResponse));
  }

  getSento(id: number): Observable<Sento> {
    return this.http
      .get<unknown>(`${this.apiUrl}/sentos/${id}`)
      .pipe(map(res => toCamel(res) as Sento));
  }
}
