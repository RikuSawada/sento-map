import { Component, Input } from '@angular/core';
import { Review } from '../../models';

@Component({
  selector: 'app-review-list',
  standalone: true,
  imports: [],
  templateUrl: './review-list.component.html',
  styleUrl: './review-list.component.css'
})
export class ReviewListComponent {
  @Input({ required: true }) reviews!: Review[];

  stars(rating: number): string {
    return '★'.repeat(rating) + '☆'.repeat(5 - rating);
  }

  formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }
}
