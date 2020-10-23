import { Component, Inject, LOCALE_ID, OnDestroy, OnInit } from '@angular/core';
import { Router } from '@angular/router';

import { Subscription } from 'rxjs';

import { AuthFacade, StorageService } from '@noc/auth';
import { LoggingService } from '@noc/log';

@Component({
  selector: 'noc-root',
  template: `
    <div>Application Component</div>
    <button *ngIf="isAuthenticated$ | async" (click)="logout()">Logout</button>
    <router-outlet></router-outlet>
  `
})
export class AppComponent implements OnInit, OnDestroy {
  private authSubscription: Subscription;
  private refreshSubscription: Subscription;
  isAuthenticated$ = this.authFacade.isAuthenticated$;

  constructor(
    @Inject(LOCALE_ID) protected locale: string,
    private loggerService: LoggingService,
    private storageService: StorageService,
    private authFacade: AuthFacade,
    private router: Router
  ) {
    this.loggerService.logDebug(`LOCALE_ID is ${locale}`);
  }

  ngOnInit(): void {
    this.authSubscription = this.authFacade
      .checkAuth()
      .subscribe(isAuthenticated => {
        this.loggerService.logDebug(`is authenticated ${isAuthenticated}`);
        if (!isAuthenticated) {
          if ('/login' !== window.location.pathname) {
            this.storageService.set('redirect', window.location.pathname);
            this.loggerService.logDebug('Save redirect url : ' + this.storageService.get('redirect'));
            this.router.navigate(['/login']).then(this.navigateHandler('login page'));
          }
        }
        if (isAuthenticated) {
          this.loggerService.logDebug('Starting refresh timer');
          this.refreshSubscription = this.authFacade.startRefreshTimer().subscribe(() => {
            this.authFacade.startRefresh();
          });
          this.navigateToStoredUrl();
        }
      });
  }

  ngOnDestroy(): void {
    this.authSubscription.unsubscribe();
    this.refreshSubscription.unsubscribe();
  }

  logout() {
    this.authFacade.logout();
    this.refreshSubscription.unsubscribe();
  }

  private navigateHandler(path: string) {
    return result => {
      if (!result) {
        this.loggerService.logError(`Navigate to ${path} failed!`);
      }
    };
  }

  private navigateToStoredUrl() {
    const path = this.storageService.get('redirect') || '/';

    if (path === 'none') {
      return;
    }

    if (this.router.url === path) {
      return;
    }

    if (path.toString().includes('/unauthorized')) {
      this.router.navigate(['/']).then(this.navigateHandler('home'));
    } else {
      this.router.navigate([path]).then(result => {
        if (result) {
          this.storageService.set('redirect', 'none');
        }
      });
    }
  }
}
