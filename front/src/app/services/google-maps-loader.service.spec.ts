import { TestBed } from '@angular/core/testing';
import { GoogleMapsLoaderService } from './google-maps-loader.service';

describe('GoogleMapsLoaderService', () => {
  let service: GoogleMapsLoaderService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(GoogleMapsLoaderService);
  });

  it('サービスが生成される', () => {
    expect(service).toBeTruthy();
  });

  it('2回 load() を呼んでも同じ Promise を返す（冪等）', () => {
    const p1 = service.load();
    const p2 = service.load();
    expect(p1).toBe(p2);
  });
});
