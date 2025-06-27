import React from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Clock, AlertTriangle } from 'lucide-react';

interface SessionWarningDialogProps {
  open: boolean;
  timeRemaining: number | null;
  onExtend: () => void;
  onEndNow: () => void;
}

export const SessionWarningDialog: React.FC<SessionWarningDialogProps> = ({
  open,
  timeRemaining,
  onExtend,
  onEndNow,
}) => {
  return (
    <AlertDialog open={open}>
      <AlertDialogContent className="max-w-md">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2 text-amber-600">
            <AlertTriangle className="w-5 h-5" />
            Session Expiring Soon
          </AlertDialogTitle>
          <AlertDialogDescription className="space-y-2">
            <div className="flex items-center gap-2 text-gray-700">
              <Clock className="w-4 h-4" />
              <span>
                Your session will expire in{' '}
                <span className="font-semibold text-amber-600">
                  {timeRemaining} minute{timeRemaining !== 1 ? 's' : ''}
                </span>
                {' '}due to inactivity.
              </span>
            </div>
            <p className="text-sm text-gray-600">
              Would you like to extend your session or end the interview now?
            </p>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter className="flex gap-2">
          <AlertDialogCancel onClick={onEndNow} className="flex-1">
            End Interview
          </AlertDialogCancel>
          <AlertDialogAction 
            onClick={onExtend} 
            className="flex-1 bg-blue-600 hover:bg-blue-700"
          >
            Extend Session
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}; 