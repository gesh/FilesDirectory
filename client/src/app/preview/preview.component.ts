import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';
import { FileService } from '../services/file.service';
import { DomSanitizer, SafeResourceUrl, SafeUrl } from '@angular/platform-browser';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-preview',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './preview.component.html',
  styleUrls: ['./preview.component.scss']
})
export class PreviewComponent implements OnInit {
  fileUrl: SafeUrl | null = null;
  fileType: 'image' | 'pdf' | 'word' | 'excel' | 'other' = 'other';
  filename: string | null = null;
  currentRevision: number | null = null;
  newestRevision: number | null = null;

  get canGoOlder(): boolean {
    if (this.newestRevision === null) return false;
    return this.currentRevision === null || this.currentRevision > 0;
  }

  get canGoNewer(): boolean {
    if (this.newestRevision === null || this.currentRevision === null) return false;
    return this.currentRevision < this.newestRevision;
  }

  get canGoLatest(): boolean {
    return this.canGoNewer;
  }

  constructor(
    private router: Router,
    private route: ActivatedRoute,
    private fileService: FileService,
    private sanitizer: DomSanitizer,
    private toastr: ToastrService
  ) {}

  ngOnInit() {
    const path = window.location.pathname;
    if (path && path !== '/upload') {
      this.route.queryParams.subscribe(params => {
        const revision = params['revision'] ? Number(params['revision']) : undefined;
        this.loadFile(path, revision);
      });
    } else {
      this.router.navigate(['/upload']);
    }
  }

  loadFile(path: string, revision?: number) {
    this.fileService.getFile(path, revision).subscribe({
      next: (response) => {
        const byteCharacters = atob(response.file.data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: response.file.mimeType });
        
        const url = URL.createObjectURL(blob);
        this.fileUrl = this.sanitizer.bypassSecurityTrustResourceUrl(url);
        this.filename = response.file.filename;
        this.determineFileType(response.file.mimeType);
        
        this.currentRevision = response.revision.current;
        this.newestRevision = response.revision.newest;
      },
      error: (error) => {
        console.error('Error loading file:', error);
        this.toastr.error('Failed to load file');
        if (error.status === 404) {
          this.router.navigate(['/upload']);
        }
      }
    });
  }

  loadLatestRevision() {
    if (this.newestRevision === null) return;
    
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { revision: this.newestRevision },
      queryParamsHandling: 'merge'
    });
  }

  loadOlderRevision() {
    if (this.currentRevision === null || this.newestRevision === null) return;
    
    if (this.currentRevision > 0) {
      this.router.navigate([], {
        relativeTo: this.route,
        queryParams: { revision: this.currentRevision - 1 },
        queryParamsHandling: 'merge'
      });
    }
  }

  loadNewerRevision() {
    if (this.currentRevision === null || this.newestRevision === null) return;
    
    if (this.currentRevision < this.newestRevision) {
      this.router.navigate([], {
        relativeTo: this.route,
        queryParams: { revision: this.currentRevision + 1 },
        queryParamsHandling: 'merge'
      });
    }
  }

  private determineFileType(mimeType: string) {
    if (mimeType.startsWith('image/')) {
      this.fileType = 'image';
    } else if (mimeType === 'application/pdf') {
      this.fileType = 'pdf';
    } else if (
      mimeType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
      mimeType === 'application/msword' 
    ) {
      this.fileType = 'word';
    } else if (
      mimeType === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
      mimeType === 'application/vnd.ms-excel' 
    ) {
      this.fileType = 'excel';
    } else {
      this.fileType = 'other';
    }
  }
} 