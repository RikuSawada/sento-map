import { TestBed } from '@angular/core/testing';
import { ComponentFixture } from '@angular/core/testing';
import { ReviewListComponent } from './review-list.component';
import { Review } from '../../models';

const mockReviews: Review[] = [
  {
    id: 1,
    sentoId: 1,
    userId: 1,
    username: 'user1',
    rating: 4,
    comment: '良かったです',
    createdAt: '2024-01-01T00:00:00Z'
  },
  {
    id: 2,
    sentoId: 1,
    userId: 2,
    username: 'user2',
    rating: 5,
    comment: null,
    createdAt: '2024-02-01T00:00:00Z'
  }
];

describe('ReviewListComponent (空)', () => {
  let fixture: ComponentFixture<ReviewListComponent>;
  let component: ReviewListComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReviewListComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(ReviewListComponent);
    component = fixture.componentInstance;
    component.reviews = [];
    fixture.detectChanges();
  });

  it('コンポーネントが生成される', () => {
    expect(component).toBeTruthy();
  });

  it('口コミが空の場合に「まだ口コミはありません」を表示', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('まだ口コミはありません');
  });
});

describe('ReviewListComponent (口コミあり)', () => {
  let fixture: ComponentFixture<ReviewListComponent>;
  let component: ReviewListComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReviewListComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(ReviewListComponent);
    component = fixture.componentInstance;
    component.reviews = mockReviews;
    fixture.detectChanges();
  });

  it('口コミ一覧を表示する', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('user1');
    expect(el.textContent).toContain('良かったです');
    expect(el.textContent).toContain('user2');
  });

  it('stars メソッドが正しい文字列を返す', () => {
    expect(component.stars(4)).toBe('★★★★☆');
    expect(component.stars(5)).toBe('★★★★★');
  });

  it('formatDate が日本語表記の日付を返す', () => {
    const result = component.formatDate('2024-01-01T00:00:00Z');
    expect(result).toContain('2024');
  });
});
