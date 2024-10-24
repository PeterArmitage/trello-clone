import { z } from 'zod';

// Base schemas without refinements for field validation
export const loginFieldSchema = {
  email: z.string().min(1, 'Email is required').email('Invalid email format'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .max(100, 'Password is too long'),
};

export const registrationFieldSchema = {
  ...loginFieldSchema,
  confirmPassword: z.string().min(1, 'Please confirm your password'),
};

// Full schemas for form validation
export const loginSchema = z.object(loginFieldSchema);

export const registrationSchema = z
  .object(registrationFieldSchema)
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  });

// Types
export type LoginFormType = z.infer<typeof loginSchema>;
export type RegistrationFormType = z.infer<typeof registrationSchema>;
