'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import AuthFormContainer from '../components/auth/AuthFormContainer';
import { authService } from '../src/services/auth-service';
import FormInput from '../ui/FormInput';

export default function LoginPage() {
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
      };

      const response = await authService.login(data);
      localStorage.setItem('token', response.access_token);
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const footer = (
    <div className="text-center text-sm">
      <span className="text-gray-600 dark:text-gray-400">Don&apos;t have an account? </span>
      <Link
        href="/register"
        className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
      >
        Sign up
      </Link>
    </div>
  );

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <AuthFormContainer
        onSubmit={handleSubmit}
        submitText="Sign In"
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
      </AuthFormContainer>
    </div>
  );
}
