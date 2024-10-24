import React from 'react';
import { Button } from '../common/Button/Button';

interface AuthFormContainerProps {
  children: React.ReactNode;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
  submitText?: string;
  isLoading?: boolean;
  error?: string;
  footer?: React.ReactNode; // Changed from null to React.ReactNode
}

const AuthFormContainer: React.FC<AuthFormContainerProps> = ({
  children,
  onSubmit,
  submitText = 'Submit',
  isLoading = false,
  error = '',
  footer,
}) => {
  return (
    <div className="w-full max-w-md p-8 space-y-6 bg-white dark:bg-gray-800 rounded-xl shadow-lg">
      {error && (
        <div className="p-3 text-sm text-red-500 bg-red-100 dark:bg-red-900/30 dark:text-red-400 rounded-lg">
          {error}
        </div>
      )}

      <form onSubmit={onSubmit} className="space-y-4">
        {children}

        <Button type="submit" variant="primary" size="lg" loading={isLoading} className="w-full">
          {submitText}
        </Button>
      </form>

      {footer && <div className="pt-4 border-t border-gray-200 dark:border-gray-700">{footer}</div>}
    </div>
  );
};

export default AuthFormContainer;
