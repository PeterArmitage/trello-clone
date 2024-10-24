import React from 'react';
import Link from 'next/link';
import { useForm, type FieldValidateFn } from '@tanstack/react-form';
import { z } from 'zod';
import { useAuth } from '@/app/src/context/auth-context';
import { loginSchema, type LoginFormType } from '../../shared/schemas/schemas';
import FormInput from '../../ui/FormInput';
import AuthFormContainer from './AuthFormContainer';

const LoginForm: React.FC = () => {
  const { login, error: authError, isLoading, clearError } = useAuth();

  const validateField =
    <TName extends keyof LoginFormType>(
      schema: z.ZodString
    ): FieldValidateFn<LoginFormType, TName> =>
    ({ value }) => {
      try {
        schema.parse(value);
        return false; // No error
      } catch (err) {
        if (err instanceof z.ZodError) {
          return err.errors[0].message;
        }
        return 'Validation failed';
      }
    };

  const form = useForm<LoginFormType>({
    defaultValues: {
      email: '',
      password: '',
    },
    onSubmit: async ({ value }) => {
      try {
        clearError();
        await login(value.email, value.password);
      } catch (err) {
        // Auth context already handles the error state
        console.error('Login failed:', err);
      }
    },
  });

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
    <AuthFormContainer
      onSubmit={form.handleSubmit}
      submitText="Sign In"
      isLoading={isLoading}
      error={authError || ''}
      footer={footer}
    >
      <form.Field
        name="email"
        validators={{
          onChange: validateField<'email'>(loginSchema.shape.email),
          onBlur: validateField<'email'>(loginSchema.shape.email),
        }}
      >
        {(field) => (
          <FormInput
            label="Email"
            type="email"
            placeholder="Enter your email"
            value={field.state.value}
            onBlur={field.handleBlur}
            onChange={(e) => field.handleChange(e.target.value)}
            error={field.state.meta.errors?.[0] || undefined}
            required
          />
        )}
      </form.Field>

      <form.Field
        name="password"
        validators={{
          onChange: validateField<'password'>(loginSchema.shape.password),
          onBlur: validateField<'password'>(loginSchema.shape.password),
        }}
      >
        {(field) => (
          <FormInput
            label="Password"
            type="password"
            placeholder="Enter your password"
            value={field.state.value}
            onBlur={field.handleBlur}
            onChange={(e) => field.handleChange(e.target.value)}
            error={field.state.meta.errors?.[0] || undefined}
            required
          />
        )}
      </form.Field>
    </AuthFormContainer>
  );
};

export default LoginForm;
