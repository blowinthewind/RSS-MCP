import { toast as sonnerToast } from 'sonner';

interface ToastOptions {
  title: string;
  description?: string;
  variant?: 'default' | 'destructive';
}

export function useToast() {
  const toast = (options: ToastOptions) => {
    if (options.variant === 'destructive') {
      sonnerToast.error(options.title, {
        description: options.description,
        duration: 3000, // Error messages show longer
      });
    } else {
      sonnerToast.success(options.title, {
        description: options.description,
        duration: 1500, // Success messages disappear quickly
      });
    }
  };

  return { toast };
}
