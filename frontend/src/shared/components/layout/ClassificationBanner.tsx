import React, { useEffect, useState } from 'react';
import { useAuthStore } from '../../../stores/authStore';
import { Shield, ShieldAlert, Clock } from 'lucide-react';

export const ClassificationBanner: React.FC = () => {
  const user = useAuthStore((state) => state.user);
  const [timeLeft, setTimeLeft] = useState('08h 00m');

  // Simple visual countdown simulator for session expiration
  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      const endOfDay = new Date();
      endOfDay.setHours(18, 0, 0, 0); // Operational shift ends at 18:00
      
      const diffMs = endOfDay.getTime() - now.getTime();
      if (diffMs > 0) {
        const hours = Math.floor(diffMs / (1000 * 60 * 60));
        const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
        setTimeLeft(`${hours.toString().padStart(2, '0')}h ${minutes.toString().padStart(2, '0')}m`);
      } else {
        setTimeLeft('Shift Over');
      }
    }, 60000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="classification-banner shadow-md">
      <div className="classification-label text-white font-bold flex items-center gap-1.5">
        <ShieldAlert size={14} className="animate-pulse" />
        <span>// SECRET //</span>
        <span className="hidden sm:inline text-[10px] bg-white/20 px-1.5 py-0.5 rounded text-white font-medium ml-2">
          RESTRICTED USE ONLY
        </span>
      </div>
      
      <div className="text-[11px] font-medium hidden md:block">
        KERALA POLICE — STATE SPECIAL BRANCH, IS DIVISION
      </div>
      
      {user && (
        <div className="flex items-center gap-4 text-[11px]">
          <div className="flex items-center gap-1">
            <Shield size={12} />
            <span className="font-semibold">{user.fullName}</span>
            <span className="opacity-75">({user.role.toUpperCase()})</span>
          </div>
          <div className="flex items-center gap-1 text-white/95">
            <Clock size={12} />
            <span>{timeLeft}</span>
          </div>
        </div>
      )}
    </div>
  );
};
