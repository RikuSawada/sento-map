import { TestBed } from '@angular/core/testing';
import { ComponentFixture } from '@angular/core/testing';
import { ReviewFormComponent } from './review-form.component';
import { ReviewCreate } from '../../models';

describe('ReviewFormComponent', () => {
  let fixture: ComponentFixture<ReviewFormComponent>;
  let component: ReviewFormComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReviewFormComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(ReviewFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('コンポーネントが生成される', () => {
    expect(component).toBeTruthy();
  });

  it('rating が 0 の場合は送信しない', () => {
    const emitSpy = vi.spyOn(component.submitReview, 'emit');
    component.form.controls.comment.setValue('テスト');
    component.submit();
    expect(emitSpy).not.toHaveBeenCalled();
  });

  it('rating が 1-5 の場合は submitReview を emit する', () => {
    const emitSpy = vi.spyOn(component.submitReview, 'emit');
    component.form.controls.rating.setValue(4);
    component.form.controls.comment.setValue('良い銭湯でした');
    component.submit();
    const expected: ReviewCreate = { rating: 4, comment: '良い銭湯でした' };
    expect(emitSpy).toHaveBeenCalledWith(expected);
  });

  it('コメントが空の場合は comment が undefined になる', () => {
    const emitSpy = vi.spyOn(component.submitReview, 'emit');
    component.form.controls.rating.setValue(3);
    component.form.controls.comment.setValue('');
    component.submit();
    expect(emitSpy).toHaveBeenCalledWith({ rating: 3, comment: undefined });
  });

  it('送信後にフォームがリセットされる', () => {
    component.form.controls.rating.setValue(5);
    component.form.controls.comment.setValue('最高');
    component.submit();
    expect(component.ratingControl.value).toBe(0);
  });

  it('stars メソッドが正しい文字列を返す', () => {
    expect(component.stars(3)).toBe('★★★☆☆');
    expect(component.stars(5)).toBe('★★★★★');
    expect(component.stars(1)).toBe('★☆☆☆☆');
  });
});
