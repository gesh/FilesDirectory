import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { FileService } from '../services/file.service';
import { ToastrService } from 'ngx-toastr';
import { Router } from '@angular/router';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-upload',
  templateUrl: './upload.component.html',
  styleUrls: ['./upload.component.scss'],
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule]
})
export class UploadComponent {
  urlPath: string = '/';
  selectedFile: File | null = null;
  uploadedFileUrl: string | null = null;

  constructor(
    private fileService: FileService,
    private toastr: ToastrService,
    private router: Router
  ) {}

  onFileSelected(event: any): void {
    this.selectedFile = event.target.files[0];
  }

  onSubmit(): void {
    if (!this.selectedFile) {
      this.toastr.warning('Please select a file');
      return;
    }

    if (!this.urlPath) {
      this.toastr.warning('Please enter a URL path');
      return;
    }

    const path = this.urlPath.startsWith('/') ? this.urlPath : `/${this.urlPath}`;
    
    const formData = new FormData();
    formData.append('file', this.selectedFile);
    formData.append('url_path', path);

    this.fileService.uploadFile(formData).subscribe({
      next: (response) => {
        this.toastr.success('File uploaded successfully');
        this.uploadedFileUrl = path;
        
        this.selectedFile = null;
        const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
        if (fileInput) fileInput.value = '';
      },
      error: (error) => {
        this.toastr.error(error.error.message || 'Upload failed');
        this.uploadedFileUrl = null;
      }
    });
  }

  previewFile(): void {
    if (this.urlPath) {
      window.open(this.urlPath, '_blank');
    }
  }
} 