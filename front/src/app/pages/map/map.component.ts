import {
  Component,
  OnInit,
  OnDestroy,
  inject,
  signal,
  computed
} from '@angular/core';
import { Router } from '@angular/router';
import { GoogleMap, MapMarker } from '@angular/google-maps';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { SentoService } from '../../services/sento.service';
import { GoogleMapsLoaderService } from '../../services/google-maps-loader.service';
import { SentoCardComponent } from '../../components/sento-card/sento-card.component';
import { Sento } from '../../models';

@Component({
  selector: 'app-map',
  standalone: true,
  imports: [GoogleMap, MapMarker, FormsModule, SentoCardComponent],
  templateUrl: './map.component.html',
  styleUrl: './map.component.css'
})
export class MapComponent implements OnInit, OnDestroy {
  private readonly sentoService = inject(SentoService);
  private readonly googleMapsLoader = inject(GoogleMapsLoaderService);
  private readonly router = inject(Router);

  readonly center: google.maps.LatLngLiteral = { lat: 35.6762, lng: 139.6503 };
  readonly zoom = 12;
  readonly mapOptions: google.maps.MapOptions = {
    mapTypeControl: false,
    streetViewControl: false,
    fullscreenControl: false
  };

  readonly sentos = signal<Sento[]>([]);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly mapsLoaded = signal(false);
  readonly searchQuery = signal('');
  readonly selectedArea = signal('');

  readonly areas = computed(() => {
    const result = new Set<string>();
    for (const s of this.sentos()) {
      const match = s.address.match(/[^\s都道府県]+区/);
      if (match) result.add(match[0]);
    }
    return Array.from(result).sort();
  });

  readonly filteredSentos = computed(() => {
    const query = this.searchQuery().trim().toLowerCase();
    const area = this.selectedArea();
    return this.sentos().filter(s => {
      const matchesQuery = !query || s.name.toLowerCase().includes(query) || s.address.toLowerCase().includes(query);
      const matchesArea = !area || s.address.includes(area);
      return matchesQuery && matchesArea;
    });
  });

  // markerPositions は後方互換のために残す（テスト用）
  readonly markerPositions = computed(() =>
    this.filteredSentos().map(s => ({ lat: s.lat, lng: s.lng }))
  );

  private readonly subscriptions = new Subscription();

  ngOnInit(): void {
    this.googleMapsLoader.load().then(() => {
      this.mapsLoaded.set(true);
    }).catch(() => {
      this.error.set('Google Maps の読み込みに失敗しました');
    });

    this.loadSentos();
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  private loadSentos(): void {
    this.loading.set(true);
    this.error.set(null);

    this.subscriptions.add(
      this.sentoService.getSentos({ per_page: 500 }).subscribe({
        next: (res) => {
          this.sentos.set(res.items);
          this.loading.set(false);
        },
        error: () => {
          this.error.set('銭湯情報の取得に失敗しました');
          this.loading.set(false);
        }
      })
    );
  }

  onCardClick(sento: Sento): void {
    void this.router.navigate(['/sentos', sento.id]);
  }

  onMarkerClick(sento: Sento): void {
    void this.router.navigate(['/sentos', sento.id]);
  }

  // 旧 API との互換性のために残す（テスト用）
  onMapInitialized(_map: google.maps.Map): void {}
  onBoundsChanged(): void {}
}
