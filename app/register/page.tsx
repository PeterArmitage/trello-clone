'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import AuthFormContainer from '../components/auth/AuthFormContainer';
import { authService } from '../src/services/auth-service';
import FormInput from '../ui/FormInput';

export default function RegisterPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const formData = new FormData(e.currentTarget);
      const data = {
        email: formData.get('email') as string,
        password: formData.get('password') as string,
        confirmPassword: formData.get('confirmPassword') as string,
      };

      if (data.password !== data.confirmPassword) {
        throw new Error("Passwords don't match");
      }

      // Register user
      await authService.register(data);

      // Log them in
      const loginResponse = await authService.login({
        email: data.email,
        password: data.password,
      });

      // Store token
      localStorage.setItem('token', loginResponse.access_token);

      // Redirect to dashboard
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  const footer = (
    <div className="text-center text-sm">
      <span className="text-gray-600 dark:text-gray-400">Already have an account? </span>
      <Link
        href="/login"
        className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
      >
        Sign in
      </Link>
    </div>
  );

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <AuthFormContainer
        onSubmit={handleSubmit}
        submitText="Create Account"
        isLoading={isLoading}
        error={error}
        footer={footer}
      >
        <FormInput
          name="email"
          label="Email"
          type="email"
          placeholder="Enter your email"
          required
        />
        <FormInput
          name="password"
          label="Password"
          type="password"
          placeholder="Enter your password"
          required
        />
        <FormInput
          name="confirmPassword"
          label="Confirm Password"
          type="password"
          placeholder="Confirm your password"
          required
        />
      </AuthFormContainer>
    </div>
  );
}
