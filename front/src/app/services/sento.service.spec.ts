import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { SentoService } from './sento.service';

describe('SentoService', () => {
  let service: SentoService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        SentoService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ]
    });
    service = TestBed.inject(SentoService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('サービスが生成される', () => {
    expect(service).toBeTruthy();
  });

  it('getSentos: GET /sentos を呼ぶ', () => {
    service.getSentos().subscribe();
    const req = httpMock.expectOne(r => r.url.includes('/sentos') && r.method === 'GET');
    expect(req.request.method).toBe('GET');
    req.flush({ items: [], total: 0, page: 1, per_page: 50 });
  });

  it('getSentos: lat/lng クエリパラメータを付与する', () => {
    service.getSentos({ lat_min: 35.0, lat_max: 36.0, lng_min: 139.0, lng_max: 140.0 }).subscribe();
    const req = httpMock.expectOne(r => r.url.includes('/sentos'));
    expect(req.request.params.get('lat_min')).toBe('35');
    expect(req.request.params.get('lat_max')).toBe('36');
    expect(req.request.params.get('lng_min')).toBe('139');
    expect(req.request.params.get('lng_max')).toBe('140');
    req.flush({ items: [], total: 0, page: 1, per_page: 50 });
  });

  it('getSentos: page/per_page パラメータを付与する', () => {
    service.getSentos({ page: 2, per_page: 100 }).subscribe();
    const req = httpMock.expectOne(r => r.url.includes('/sentos'));
    expect(req.request.params.get('page')).toBe('2');
    expect(req.request.params.get('per_page')).toBe('100');
    req.flush({ items: [], total: 0, page: 2, per_page: 100 });
  });

  it('getSentos: パラメータなしのとき余分なクエリを付与しない', () => {
    service.getSentos().subscribe();
    const req = httpMock.expectOne(r => r.url.includes('/sentos'));
    expect(req.request.params.keys().length).toBe(0);
    req.flush({ items: [], total: 0, page: 1, per_page: 50 });
  });

  it('getSentos: snake_case レスポンスを camelCase に変換する', () => {
    let result: unknown;
    service.getSentos().subscribe(r => { result = r; });
    const req = httpMock.expectOne(r => r.url.includes('/sentos'));
    req.flush({
      items: [
        {
          id: 1,
          name: 'テスト銭湯',
          address: '東京都',
          lat: 35.0,
          lng: 139.0,
          phone: null,
          url: null,
          open_hours: '10:00-22:00',
          holiday: '月曜',
          created_at: '2024-01-01T00:00:00',
          updated_at: '2024-01-01T00:00:00'
        }
      ],
      total: 1,
      page: 1,
      per_page: 50
    });
    const res = result as { items: Record<string, unknown>[] };
    expect(res.items[0]['openHours']).toBe('10:00-22:00');
    expect(res.items[0]['createdAt']).toBe('2024-01-01T00:00:00');
  });

  it('getSento: GET /sentos/:id を呼ぶ', () => {
    service.getSento(1).subscribe();
    const req = httpMock.expectOne(r => r.url.includes('/sentos/1'));
    expect(req.request.method).toBe('GET');
    req.flush({
      id: 1,
      name: 'テスト銭湯',
      address: '東京都渋谷区',
      lat: 35.0,
      lng: 139.0,
      phone: null,
      url: null,
      open_hours: null,
      holiday: null,
      created_at: '2024-01-01T00:00:00',
      updated_at: '2024-01-01T00:00:00'
    });
  });

  it('getSento: snake_case レスポンスを camelCase に変換する', () => {
    let result: unknown;
    service.getSento(42).subscribe(r => { result = r; });
    const req = httpMock.expectOne(r => r.url.includes('/sentos/42'));
    req.flush({
      id: 42,
      name: '銭湯ABC',
      address: '東京都新宿区',
      lat: 35.6,
      lng: 139.7,
      phone: '03-1234-5678',
      url: 'https://example.com',
      open_hours: '15:00-24:00',
      holiday: '水曜',
      created_at: '2024-06-01T00:00:00',
      updated_at: '2024-06-02T00:00:00'
    });
    const sento = result as Record<string, unknown>;
    expect(sento['id']).toBe(42);
    expect(sento['openHours']).toBe('15:00-24:00');
    expect(sento['createdAt']).toBe('2024-06-01T00:00:00');
    expect(sento['updatedAt']).toBe('2024-06-02T00:00:00');
  });
});
