import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { ReviewService } from './review.service';
import { ReviewCreate } from '../models';

describe('ReviewService', () => {
  let service: ReviewService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        ReviewService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ]
    });
    service = TestBed.inject(ReviewService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('サービスが生成される', () => {
    expect(service).toBeTruthy();
  });

  it('getReviews: GET /sentos/:id/reviews を呼ぶ', () => {
    service.getReviews(1).subscribe();
    const req = httpMock.expectOne(r => r.url.includes('/sentos/1/reviews') && r.method === 'GET');
    expect(req.request.method).toBe('GET');
    req.flush([]);
  });

  it('getReviews: page パラメータを付与する', () => {
    service.getReviews(1, 2).subscribe();
    const req = httpMock.expectOne(r => r.url.includes('/sentos/1/reviews'));
    expect(req.request.params.get('page')).toBe('2');
    req.flush([]);
  });

  it('getReviews: page なしのとき page クエリを付与しない', () => {
    service.getReviews(5).subscribe();
    const req = httpMock.expectOne(r => r.url.includes('/sentos/5/reviews'));
    expect(req.request.params.get('page')).toBeNull();
    req.flush([]);
  });

  it('getReviews: snake_case レスポンスを camelCase に変換する', () => {
    let result: unknown;
    service.getReviews(1).subscribe(r => { result = r; });
    const req = httpMock.expectOne(r => r.url.includes('/sentos/1/reviews'));
    req.flush([
      {
        id: 10,
        sento_id: 1,
        user_id: 5,
        username: 'testuser',
        rating: 4,
        comment: '良い銭湯です',
        created_at: '2024-03-01T00:00:00'
      }
    ]);
    const reviews = result as Record<string, unknown>[];
    expect(reviews[0]['sentoId']).toBe(1);
    expect(reviews[0]['userId']).toBe(5);
    expect(reviews[0]['createdAt']).toBe('2024-03-01T00:00:00');
  });

  it('createReview: POST /sentos/:id/reviews を呼ぶ', () => {
    const data: ReviewCreate = { rating: 5, comment: '最高でした' };
    service.createReview(1, data).subscribe();
    const req = httpMock.expectOne(r => r.url.includes('/sentos/1/reviews') && r.method === 'POST');
    expect(req.request.method).toBe('POST');
    req.flush({
      id: 100,
      sento_id: 1,
      user_id: 5,
      username: 'testuser',
      rating: 5,
      comment: '最高でした',
      created_at: '2024-03-01T00:00:00'
    });
  });

  it('createReview: 正しいペイロードを送信する', () => {
    const data: ReviewCreate = { rating: 3, comment: 'まあまあ' };
    service.createReview(7, data).subscribe();
    const req = httpMock.expectOne(r => r.url.includes('/sentos/7/reviews'));
    expect(req.request.body).toEqual({ rating: 3, comment: 'まあまあ' });
    req.flush({
      id: 200,
      sento_id: 7,
      user_id: 1,
      username: 'user1',
      rating: 3,
      comment: 'まあまあ',
      created_at: '2024-03-02T00:00:00'
    });
  });

  it('createReview: comment なしでも送信できる', () => {
    const data: ReviewCreate = { rating: 4 };
    service.createReview(2, data).subscribe();
    const req = httpMock.expectOne(r => r.url.includes('/sentos/2/reviews') && r.method === 'POST');
    expect(req.request.body).toEqual({ rating: 4 });
    req.flush({
      id: 300,
      sento_id: 2,
      user_id: 1,
      username: 'user1',
      rating: 4,
      comment: null,
      created_at: '2024-03-03T00:00:00'
    });
  });

  it('createReview: snake_case レスポンスを camelCase に変換する', () => {
    let result: unknown;
    service.createReview(3, { rating: 5 }).subscribe(r => { result = r; });
    const req = httpMock.expectOne(r => r.url.includes('/sentos/3/reviews') && r.method === 'POST');
    req.flush({
      id: 400,
      sento_id: 3,
      user_id: 2,
      username: 'user2',
      rating: 5,
      comment: null,
      created_at: '2024-04-01T00:00:00'
    });
    const review = result as Record<string, unknown>;
    expect(review['sentoId']).toBe(3);
    expect(review['userId']).toBe(2);
    expect(review['createdAt']).toBe('2024-04-01T00:00:00');
  });
});
