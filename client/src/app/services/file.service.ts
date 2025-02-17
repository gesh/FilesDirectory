import { Injectable } from '@angular/core';
import { HttpClient, HttpParams, HttpResponse } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface FileResponse {
  file: {
    data: string; // base64 encoded string
    mimeType: string;
    filename: string;
  };
  revision: {
    current: number;
    newest: number;
  };
}

@Injectable({
  providedIn: 'root'
})
export class FileService {
  private apiUrl = 'http://localhost:5555/api';

  constructor(private http: HttpClient) { }

  uploadFile(formData: FormData): Observable<any> {
    return this.http.post(`${this.apiUrl}/upload`, formData);
  }

  getFile(path: string, revision?: number): Observable<FileResponse> {
    let params = new HttpParams();

    if (revision !== undefined) {
      params = params.set('revision', revision.toString());
    }

    return this.http.get<FileResponse>(`${this.apiUrl}${path}`, { params });
  }
} 