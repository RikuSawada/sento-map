import { TestBed } from '@angular/core/testing';
import { ComponentFixture } from '@angular/core/testing';
import { SentoCardComponent } from './sento-card.component';
import { Sento } from '../../models';

const mockSento: Sento = {
  id: 1,
  name: 'テスト銭湯',
  address: '東京都新宿区1-1-1',
  lat: 35.6762,
  lng: 139.6503,
  phone: '03-1234-5678',
  url: 'https://example.com',
  openHours: '15:00-23:00',
  holiday: '月曜日',
  prefecture: '東京都',
  region: '関東',
  sourceUrl: null,
  geocodedBy: 'batch',
  facilityType: null,
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z'
};

describe('SentoCardComponent', () => {
  let fixture: ComponentFixture<SentoCardComponent>;
  let component: SentoCardComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SentoCardComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(SentoCardComponent);
    component = fixture.componentInstance;
    component.sento = mockSento;
    fixture.detectChanges();
  });

  it('コンポーネントが生成される', () => {
    expect(component).toBeTruthy();
  });

  it('銭湯名を表示する', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('テスト銭湯');
  });

  it('住所を表示する', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('東京都新宿区1-1-1');
  });

  it('区名バッジを表示する', () => {
    const el = fixture.nativeElement as HTMLElement;
    const badge = el.querySelector('.card__ward');
    expect(badge?.textContent?.trim()).toBe('新宿区');
  });

  it('営業時間を表示する', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('15:00-23:00');
  });

  it('定休日を表示する', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('月曜日');
  });

  it('カードクリック時に cardClick イベントを emit する', () => {
    const emitSpy = vi.spyOn(component.cardClick, 'emit');
    const card = fixture.nativeElement.querySelector('.card') as HTMLElement;
    card.click();
    expect(emitSpy).toHaveBeenCalledWith(mockSento);
  });

  it('ward getter が住所から区を抽出する', () => {
    expect(component.ward).toBe('新宿区');
  });

  it('住所に区がない場合 ward は空文字を返す', () => {
    component.sento = { ...mockSento, address: '東京都1-1-1' };
    expect(component.ward).toBe('');
  });
});
