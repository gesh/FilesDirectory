import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthService } from '../services/auth.service';
import { ToastrService } from 'ngx-toastr';
import { Router } from '@angular/router';

@Component({
  selector: 'app-register',
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.scss'],
  standalone: true
})
export class RegisterComponent {
  registerForm: FormGroup;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private toastr: ToastrService,
    private router: Router
  ) {
    this.registerForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]]
    });
  }

  onSubmit(): void {
    if (this.registerForm.valid) {
      const { email, password } = this.registerForm.value;
      
      this.authService.register(email, password).subscribe({
        next: () => {
          this.authService.login(email, password).subscribe({
            next: () => {
              this.toastr.success('Registration successful');
              this.router.navigate(['/upload']);
            },
            error: (error) => {
              this.toastr.error('Auto-login failed');
              this.router.navigate(['/login']);
            }
          });
        },
        error: (error) => {
          this.toastr.error(error.error.message || 'Registration failed');
        }
      });
    }
  }
}
