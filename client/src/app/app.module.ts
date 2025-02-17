import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { RouterModule } from '@angular/router';

import { AppComponent } from './app.component';
import { RegisterComponent } from './register/register.component';
import { LoginComponent } from './login/login.component';
import { FileUploadComponent } from './file-upload/file-upload.component';
import { PreviewComponent } from './preview/preview.component';

@NgModule({
  declarations: [		
    AppComponent,
    RegisterComponent,
    LoginComponent,
    FileUploadComponent,
    PreviewComponent
   ],
  imports: [
    BrowserModule,
    RouterModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { } 