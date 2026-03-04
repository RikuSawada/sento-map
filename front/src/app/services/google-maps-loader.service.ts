import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class GoogleMapsLoaderService {
  private loadPromise: Promise<void> | null = null;

  load(): Promise<void> {
    if (this.loadPromise) {
      return this.loadPromise;
    }
    if (typeof google !== 'undefined' && typeof google.maps !== 'undefined') {
      this.loadPromise = Promise.resolve();
      return this.loadPromise;
    }
    this.loadPromise = new Promise<void>((resolve, reject) => {
      const existing = document.getElementById('google-maps-script');
      if (existing) {
        existing.addEventListener('load', () => resolve());
        existing.addEventListener('error', () => reject(new Error('Failed to load Google Maps')));
        return;
      }
      const script = document.createElement('script');
      script.id = 'google-maps-script';
      script.src = `https://maps.googleapis.com/maps/api/js?key=${environment.googleMapsApiKey}`;
      script.async = true;
      script.defer = true;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error('Failed to load Google Maps'));
      document.head.appendChild(script);
    });
    return this.loadPromise;
  }
}
