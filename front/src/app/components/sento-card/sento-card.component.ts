import { Component, Input, Output, EventEmitter, computed, signal } from '@angular/core';
import { Sento } from '../../models';

@Component({
  selector: 'app-sento-card',
  standalone: true,
  imports: [],
  templateUrl: './sento-card.component.html',
  styleUrl: './sento-card.component.css'
})
export class SentoCardComponent {
  @Input({ required: true }) sento!: Sento;
  @Output() cardClick = new EventEmitter<Sento>();

  get ward(): string {
    return this.sento.address.match(/[^\s都道府県]+区/)?.[0] ?? '';
  }
}
