import { Component, EventEmitter, Output, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ReviewCreate } from '../../models';

@Component({
  selector: 'app-review-form',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './review-form.component.html',
  styleUrl: './review-form.component.css'
})
export class ReviewFormComponent {
  @Output() readonly submitReview = new EventEmitter<ReviewCreate>();

  private readonly fb = inject(FormBuilder);

  readonly form = this.fb.nonNullable.group({
    rating: [0, [Validators.required, Validators.min(1), Validators.max(5)]],
    comment: ['']
  });

  readonly ratingOptions = [1, 2, 3, 4, 5] as const;

  stars(n: number): string {
    return '★'.repeat(n) + '☆'.repeat(5 - n);
  }

  get ratingControl() {
    return this.form.controls.rating;
  }

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const { rating, comment } = this.form.getRawValue();
    const payload: ReviewCreate = { rating, comment: comment || undefined };
    this.submitReview.emit(payload);
    this.form.reset({ rating: 0, comment: '' });
  }
}
