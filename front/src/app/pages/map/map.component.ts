import {
  Component,
  OnInit,
  OnDestroy,
  inject,
  signal,
  computed
} from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { GoogleMap, MapMarker } from '@angular/google-maps';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { SentoService } from '../../services/sento.service';
import { GoogleMapsLoaderService } from '../../services/google-maps-loader.service';
import { SentoCardComponent } from '../../components/sento-card/sento-card.component';
import { Sento } from '../../models';

/** 都道府県ごとの地図中心座標とズームレベル */
const PREFECTURE_CENTERS: Record<string, { lat: number; lng: number; zoom: number }> = {
  '北海道': { lat: 43.0646, lng: 141.3468, zoom: 8 },
  '青森県': { lat: 40.8244, lng: 140.7400, zoom: 9 },
  '岩手県': { lat: 39.7036, lng: 141.1527, zoom: 9 },
  '宮城県': { lat: 38.2688, lng: 140.8721, zoom: 9 },
  '秋田県': { lat: 39.7186, lng: 140.1023, zoom: 9 },
  '山形県': { lat: 38.2404, lng: 140.3633, zoom: 9 },
  '福島県': { lat: 37.7500, lng: 140.4677, zoom: 9 },
  '茨城県': { lat: 36.3418, lng: 140.4468, zoom: 9 },
  '栃木県': { lat: 36.5658, lng: 139.8836, zoom: 9 },
  '群馬県': { lat: 36.3911, lng: 139.0608, zoom: 9 },
  '埼玉県': { lat: 35.8569, lng: 139.6489, zoom: 9 },
  '千葉県': { lat: 35.6050, lng: 140.1233, zoom: 9 },
  '東京都': { lat: 35.6762, lng: 139.6503, zoom: 12 },
  '神奈川県': { lat: 35.4478, lng: 139.6425, zoom: 10 },
  '新潟県': { lat: 37.9026, lng: 139.0232, zoom: 9 },
  '富山県': { lat: 36.6953, lng: 137.2115, zoom: 10 },
  '石川県': { lat: 36.5947, lng: 136.6256, zoom: 10 },
  '福井県': { lat: 36.0652, lng: 136.2216, zoom: 10 },
  '山梨県': { lat: 35.6635, lng: 138.5685, zoom: 10 },
  '長野県': { lat: 36.6513, lng: 138.1810, zoom: 9 },
  '岐阜県': { lat: 35.3912, lng: 136.7223, zoom: 9 },
  '静岡県': { lat: 34.9769, lng: 138.3831, zoom: 9 },
  '愛知県': { lat: 35.1802, lng: 136.9066, zoom: 10 },
  '三重県': { lat: 34.7303, lng: 136.5086, zoom: 9 },
  '滋賀県': { lat: 35.0045, lng: 135.8686, zoom: 10 },
  '京都府': { lat: 35.0211, lng: 135.7556, zoom: 11 },
  '大阪府': { lat: 34.6937, lng: 135.5022, zoom: 11 },
  '兵庫県': { lat: 34.8899, lng: 134.9405, zoom: 10 },
  '奈良県': { lat: 34.6851, lng: 135.8325, zoom: 10 },
  '和歌山県': { lat: 34.2261, lng: 135.1675, zoom: 10 },
  '鳥取県': { lat: 35.5036, lng: 134.2383, zoom: 10 },
  '島根県': { lat: 35.4723, lng: 133.0505, zoom: 10 },
  '岡山県': { lat: 34.6617, lng: 133.9350, zoom: 10 },
  '広島県': { lat: 34.3963, lng: 132.4596, zoom: 10 },
  '山口県': { lat: 34.1860, lng: 131.4706, zoom: 10 },
  '徳島県': { lat: 34.0658, lng: 134.5594, zoom: 10 },
  '香川県': { lat: 34.3401, lng: 134.0434, zoom: 11 },
  '愛媛県': { lat: 33.8417, lng: 132.7657, zoom: 10 },
  '高知県': { lat: 33.5597, lng: 133.5311, zoom: 10 },
  '福岡県': { lat: 33.6063, lng: 130.4183, zoom: 10 },
  '佐賀県': { lat: 33.2494, lng: 130.2988, zoom: 10 },
  '長崎県': { lat: 32.7447, lng: 129.8737, zoom: 10 },
  '熊本県': { lat: 32.7898, lng: 130.7417, zoom: 10 },
  '大分県': { lat: 33.2382, lng: 131.6126, zoom: 10 },
  '宮崎県': { lat: 31.9077, lng: 131.4202, zoom: 10 },
  '鹿児島県': { lat: 31.5602, lng: 130.5580, zoom: 10 },
  '沖縄県': { lat: 26.2124, lng: 127.6809, zoom: 10 },
};

export const PREFECTURE_LIST = Object.keys(PREFECTURE_CENTERS);

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
  private readonly route = inject(ActivatedRoute);

  readonly prefectureList = PREFECTURE_LIST;

  // 地図の表示状態（都道府県選択に応じて変更）
  readonly mapCenter = signal<google.maps.LatLngLiteral>({ lat: 36.2048, lng: 138.2529 });
  readonly mapZoom = signal(6);
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
  readonly selectedPrefecture = signal('');

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

  // lat/lng が null の銭湯はマーカー非表示（型述語で Sento & {lat: number; lng: number} に絞る）
  readonly markableSentos = computed(() =>
    this.filteredSentos().filter(
      (s): s is Sento & { lat: number; lng: number } => s.lat !== null && s.lng !== null
    )
  );

  // 後方互換（テスト用）
  readonly markerPositions = computed(() =>
    this.markableSentos().map(s => ({ lat: s.lat as number, lng: s.lng as number }))
  );

  private readonly subscriptions = new Subscription();

  ngOnInit(): void {
    this.googleMapsLoader.load().then(() => {
      this.mapsLoaded.set(true);
    }).catch(() => {
      this.error.set('Google Maps の読み込みに失敗しました');
    });

    // URL クエリパラメータから初期値を復元
    const qp = this.route.snapshot.queryParams;
    if (qp['prefecture']) this.selectedPrefecture.set(qp['prefecture'] as string);
    if (qp['area']) this.selectedArea.set(qp['area'] as string);

    this.loadSentos(this.selectedPrefecture());
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  private loadSentos(prefecture?: string): void {
    this.loading.set(true);
    this.error.set(null);
    this.selectedArea.set('');

    const params = prefecture
      ? { per_page: 500, prefecture }
      : { per_page: 500 };

    this.subscriptions.add(
      this.sentoService.getSentos(params).subscribe({
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

  onPrefectureChange(prefecture: string): void {
    this.selectedPrefecture.set(prefecture);
    this.loadSentos(prefecture || undefined);

    // 地図を選択都道府県にズーム
    if (prefecture && PREFECTURE_CENTERS[prefecture]) {
      const { lat, lng, zoom } = PREFECTURE_CENTERS[prefecture];
      this.mapCenter.set({ lat, lng });
      this.mapZoom.set(zoom);
    } else {
      this.mapCenter.set({ lat: 36.2048, lng: 138.2529 });
      this.mapZoom.set(6);
    }

    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { prefecture: prefecture || null, area: null },
      queryParamsHandling: 'merge',
    });
  }

  onAreaChange(area: string): void {
    this.selectedArea.set(area);
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { area: area || null },
      queryParamsHandling: 'merge',
    });
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
