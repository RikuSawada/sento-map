import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { GoogleMap, MapMarker } from '@angular/google-maps';
import { SentoService } from '../../services/sento.service';
import { ReviewService } from '../../services/review.service';
import { AuthService } from '../../services/auth.service';
import { GoogleMapsLoaderService } from '../../services/google-maps-loader.service';
import { Sento, Review, ReviewCreate } from '../../models';
import { ReviewListComponent } from '../../components/review-list/review-list.component';
import { ReviewFormComponent } from '../../components/review-form/review-form.component';

@Component({
  selector: 'app-sento-detail',
  standalone: true,
  imports: [RouterLink, ReviewListComponent, ReviewFormComponent, GoogleMap, MapMarker],
  templateUrl: './sento-detail.component.html',
  styleUrl: './sento-detail.component.css'
})
export class SentoDetailComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly sentoService = inject(SentoService);
  private readonly reviewService = inject(ReviewService);
  private readonly authService = inject(AuthService);
  private readonly googleMapsLoader = inject(GoogleMapsLoaderService);

  readonly sento = signal<Sento | null>(null);
  readonly reviews = signal<Review[]>([]);
  readonly loading = signal(true);
  readonly reviewsLoading = signal(false);
  readonly submitError = signal<string | null>(null);
  readonly submitSuccess = signal(false);
  readonly mapsLoaded = signal(false);

  readonly isLoggedIn = this.authService.isLoggedIn();

  readonly detailMapOptions: google.maps.MapOptions = {
    mapTypeControl: false,
    streetViewControl: false,
    fullscreenControl: false,
    zoomControl: true
  };

  private sentoId = 0;

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    this.sentoId = idParam ? parseInt(idParam, 10) : 0;

    if (!this.sentoId || isNaN(this.sentoId)) {
      void this.router.navigate(['/map']);
      return;
    }

    this.loadSento();
    this.loadReviews();

    this.googleMapsLoader.load().then(() => {
      this.mapsLoaded.set(true);
    }).catch(() => {
      // 地図が読み込めなくても詳細ページ自体は表示する
    });
  }

  private loadSento(): void {
    this.loading.set(true);
    this.sentoService.getSento(this.sentoId).subscribe({
      next: (s) => {
        this.sento.set(s);
        this.loading.set(false);
      },
      error: (err: { status?: number }) => {
        this.loading.set(false);
        if (err.status === 404) {
          void this.router.navigate(['/map']);
        }
      }
    });
  }

  private loadReviews(): void {
    this.reviewsLoading.set(true);
    this.reviewService.getReviews(this.sentoId).subscribe({
      next: (list) => {
        this.reviews.set(list);
        this.reviewsLoading.set(false);
      },
      error: () => {
        this.reviewsLoading.set(false);
      }
    });
  }

  onSubmitReview(data: ReviewCreate): void {
    this.submitError.set(null);
    this.submitSuccess.set(false);

    this.reviewService.createReview(this.sentoId, data).subscribe({
      next: () => {
        this.submitSuccess.set(true);
        this.loadReviews();
      },
      error: () => {
        this.submitError.set('口コミの投稿に失敗しました。しばらく後でお試しください');
      }
    });
  }
}
