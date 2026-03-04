import { TestBed } from '@angular/core/testing';
import { ComponentFixture } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { provideRouter, Router, ActivatedRoute } from '@angular/router';
import { of, throwError } from 'rxjs';
import { SentoDetailComponent } from './sento-detail.component';
import { SentoService } from '../../services/sento.service';
import { ReviewService } from '../../services/review.service';
import { AuthService } from '../../services/auth.service';
import { GoogleMapsLoaderService } from '../../services/google-maps-loader.service';
import { Sento, Review } from '../../models';

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

const mockReviews: Review[] = [
  {
    id: 1,
    sentoId: 1,
    userId: 1,
    username: 'user1',
    rating: 4,
    comment: 'good',
    createdAt: '2024-01-01T00:00:00Z'
  }
];

describe('SentoDetailComponent', () => {
  let fixture: ComponentFixture<SentoDetailComponent>;
  let component: SentoDetailComponent;
  let sentoServiceMock: { getSento: ReturnType<typeof vi.fn> };
  let reviewServiceMock: {
    getReviews: ReturnType<typeof vi.fn>;
    createReview: ReturnType<typeof vi.fn>;
  };
  let authServiceMock: { isLoggedIn: ReturnType<typeof vi.fn> };
  let googleMapsLoaderMock: { load: ReturnType<typeof vi.fn> };

  beforeEach(async () => {
    sentoServiceMock = { getSento: vi.fn().mockReturnValue(of(mockSento)) };
    reviewServiceMock = {
      getReviews: vi.fn().mockReturnValue(of(mockReviews)),
      createReview: vi.fn()
    };
    authServiceMock = { isLoggedIn: vi.fn().mockReturnValue(false) };
    googleMapsLoaderMock = { load: vi.fn().mockResolvedValue(undefined) };

    await TestBed.configureTestingModule({
      imports: [SentoDetailComponent],
      providers: [
        { provide: SentoService, useValue: sentoServiceMock },
        { provide: ReviewService, useValue: reviewServiceMock },
        { provide: AuthService, useValue: authServiceMock },
        { provide: GoogleMapsLoaderService, useValue: googleMapsLoaderMock },
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: { paramMap: { get: (_k: string) => '1' } }
          }
        }
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(SentoDetailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('コンポーネントが生成される', () => {
    expect(component).toBeTruthy();
  });

  it('銭湯情報を取得して表示する', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('テスト銭湯');
  });

  it('口コミ一覧を表示する', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('user1');
  });

  it('未ログインの場合はログインプロンプトを表示', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('ログイン');
  });

  it('404エラー時に /map にリダイレクト', () => {
    sentoServiceMock.getSento.mockReturnValue(throwError(() => ({ status: 404 })));
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate').mockResolvedValue(true);
    component.ngOnInit();
    expect(navigateSpy).toHaveBeenCalledWith(['/map']);
  });

  it('口コミ投稿後に口コミ一覧を更新する', () => {
    const newReview: Review = {
      id: 2,
      sentoId: 1,
      userId: 1,
      username: 'user1',
      rating: 5,
      comment: '最高',
      createdAt: '2024-02-01T00:00:00Z'
    };
    reviewServiceMock.createReview.mockReturnValue(of(newReview));
    component.onSubmitReview({ rating: 5, comment: '最高' });
    expect(reviewServiceMock.getReviews).toHaveBeenCalledTimes(2);
  });

  it('GoogleMapsLoaderService の load が呼ばれる', () => {
    expect(googleMapsLoaderMock.load).toHaveBeenCalled();
  });
});
