import { TestBed } from '@angular/core/testing';
import { ComponentFixture } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { MapComponent } from './map.component';
import { SentoService } from '../../services/sento.service';
import { GoogleMapsLoaderService } from '../../services/google-maps-loader.service';
import { SentoListResponse, Sento } from '../../models';
import { provideHttpClient } from '@angular/common/http';

const mockSento: Sento = {
  id: 1,
  name: 'テスト銭湯',
  address: '東京都新宿区1-1-1',
  lat: 35.6762,
  lng: 139.6503,
  phone: null,
  url: null,
  openHours: null,
  holiday: null,
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z'
};

const mockListResponse: SentoListResponse = {
  items: [mockSento],
  total: 1,
  page: 1,
  perPage: 500
};

describe('MapComponent', () => {
  let fixture: ComponentFixture<MapComponent>;
  let component: MapComponent;
  let sentoServiceMock: { getSentos: ReturnType<typeof vi.fn> };
  let googleMapsLoaderMock: { load: ReturnType<typeof vi.fn> };

  beforeEach(async () => {
    sentoServiceMock = {
      getSentos: vi.fn().mockReturnValue(of(mockListResponse))
    };
    googleMapsLoaderMock = {
      load: vi.fn().mockResolvedValue(undefined)
    };

    await TestBed.configureTestingModule({
      imports: [MapComponent],
      providers: [
        { provide: SentoService, useValue: sentoServiceMock },
        { provide: GoogleMapsLoaderService, useValue: googleMapsLoaderMock },
        provideRouter([]),
        provideHttpClient()
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(MapComponent);
    component = fixture.componentInstance;
  });

  it('コンポーネントが生成される', () => {
    expect(component).toBeTruthy();
  });

  it('初期状態: loading が false, error が null, sentos が空配列', () => {
    expect(component.loading()).toBe(false);
    expect(component.error()).toBeNull();
    expect(component.sentos()).toEqual([]);
  });

  it('初期状態: mapsLoaded が false', () => {
    expect(component.mapsLoaded()).toBe(false);
  });

  it('center が東京のデフォルト座標に設定される', () => {
    expect(component.center.lat).toBeCloseTo(35.6762, 3);
    expect(component.center.lng).toBeCloseTo(139.6503, 3);
  });

  it('zoom が 12 に設定される', () => {
    expect(component.zoom).toBe(12);
  });

  it('ngOnInit で per_page: 500 で getSentos を呼ぶ', async () => {
    component.ngOnInit();
    expect(sentoServiceMock.getSentos).toHaveBeenCalledWith({ per_page: 500 });
    expect(component.sentos()).toEqual([mockSento]);
    expect(component.loading()).toBe(false);
  });

  it('getSentos がエラーの場合 error シグナルにメッセージが入る', () => {
    sentoServiceMock.getSentos.mockReturnValue(throwError(() => new Error('network error')));
    component.ngOnInit();
    expect(component.error()).toBe('銭湯情報の取得に失敗しました');
    expect(component.loading()).toBe(false);
  });

  it('searchQuery でフィルタリングされる', () => {
    component.sentos.set([mockSento]);
    component.searchQuery.set('テスト');
    expect(component.filteredSentos().length).toBe(1);
    component.searchQuery.set('存在しない銭湯名');
    expect(component.filteredSentos().length).toBe(0);
  });

  it('selectedArea でフィルタリングされる', () => {
    component.sentos.set([mockSento]);
    component.selectedArea.set('新宿区');
    expect(component.filteredSentos().length).toBe(1);
    component.selectedArea.set('渋谷区');
    expect(component.filteredSentos().length).toBe(0);
  });

  it('areas が住所から区を抽出してユニーク配列を返す', () => {
    component.sentos.set([mockSento]);
    expect(component.areas()).toContain('新宿区');
  });

  it('markerPositions は filteredSentos の lat/lng を返す computed', () => {
    component.sentos.set([mockSento]);
    const positions = component.markerPositions();
    expect(positions).toEqual([{ lat: mockSento.lat, lng: mockSento.lng }]);
  });

  it('onMarkerClick で /sentos/:id にナビゲートする', async () => {
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate').mockResolvedValue(true);
    component.onMarkerClick(mockSento);
    expect(navigateSpy).toHaveBeenCalledWith(['/sentos', 1]);
  });

  it('onCardClick で /sentos/:id にナビゲートする', async () => {
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate').mockResolvedValue(true);
    component.onCardClick(mockSento);
    expect(navigateSpy).toHaveBeenCalledWith(['/sentos', 1]);
  });

  it('ngOnDestroy でサブスクリプションをクリーンアップする', () => {
    expect(() => component.ngOnDestroy()).not.toThrow();
  });
});
