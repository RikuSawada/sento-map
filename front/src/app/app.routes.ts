import { Routes } from '@angular/router';
import { authGuard, guestGuard } from './guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'map', pathMatch: 'full' },
  {
    path: 'map',
    loadComponent: () => import('./pages/map/map.component').then(m => m.MapComponent)
  },
  {
    path: 'login',
    loadComponent: () => import('./pages/login/login.component').then(m => m.LoginComponent),
    canActivate: [guestGuard]
  },
  {
    path: 'register',
    loadComponent: () => import('./pages/register/register.component').then(m => m.RegisterComponent),
    canActivate: [guestGuard]
  },
  {
    path: 'sentos/:id',
    loadComponent: () => import('./pages/sento-detail/sento-detail.component').then(m => m.SentoDetailComponent)
  },
  { path: '**', redirectTo: 'map' }
];

export { authGuard };
