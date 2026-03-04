import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../environments/environment';
import { Review, ReviewCreate } from '../models';

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

@Injectable({
  providedIn: 'root'
})
export class ReviewService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  getReviews(sentoId: number, page?: number): Observable<Review[]> {
    let httpParams = new HttpParams();
    if (page !== undefined) httpParams = httpParams.set('page', page);
    return this.http
      .get<unknown>(`${this.apiUrl}/sentos/${sentoId}/reviews`, { params: httpParams })
      .pipe(map(res => toCamel(res) as Review[]));
  }

  createReview(sentoId: number, data: ReviewCreate): Observable<Review> {
    return this.http
      .post<unknown>(`${this.apiUrl}/sentos/${sentoId}/reviews`, data)
      .pipe(map(res => toCamel(res) as Review));
  }
}
