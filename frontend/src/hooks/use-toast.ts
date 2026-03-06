import { useCallback } from 'react';

interface ToastOptions {
  title: string;
  description?: string;
  variant?: 'default' | 'destructive';
}

export function useToast() {
  const toast = useCallback((options: ToastOptions) => {
    // Simple implementation - just log to console for now
    // In a full implementation, this would show a toast notification
    if (options.variant === 'destructive') {
      console.error(`[Toast] ${options.title}: ${options.description}`);
    } else {
      console.log(`[Toast] ${options.title}: ${options.description}`);
    }
    
    // Also show browser alert for destructive messages
    if (options.variant === 'destructive') {
      // alert(`${options.title}: ${options.description}`);
    }
  }, []);

  return { toast };
}
