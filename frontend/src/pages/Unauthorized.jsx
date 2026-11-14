import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, ArrowLeft } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Unauthorized = () => {
  const { role, isFaculty } = useAuth();

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4 bg-slate-100">
      <div className="max-w-md w-full bg-white rounded-2xl border border-slate-200 p-8 text-center shadow-lg space-y-4">
        <div className="w-14 h-14 bg-rose-100 text-rose-600 rounded-2xl flex items-center justify-center mx-auto">
          <ShieldAlert className="w-8 h-8" />
        </div>

        <h1 className="text-2xl font-bold text-slate-900">403 - Access Denied</h1>
        
        <p className="text-xs text-slate-600 leading-relaxed">
          You do not have the required institutional authorization role to access this protected academic resource.
        </p>

        <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs font-mono text-slate-600">
          Current Role: <strong className="text-slate-900">{role || 'ANONYMOUS'}</strong>
        </div>

        <div className="pt-2 flex flex-col gap-2">
          <Link
            to={isFaculty ? '/faculty/dashboard' : '/student/dashboard'}
            className="w-full bg-slate-900 hover:bg-slate-800 text-white font-semibold py-2.5 rounded-xl text-xs transition-colors flex items-center justify-center gap-1.5"
          >
            <ArrowLeft className="w-4 h-4" /> Go to Your Role Dashboard
          </Link>
          <Link
            to="/"
            className="w-full bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold py-2.5 rounded-xl text-xs transition-colors"
          >
            Return to Academic Portal Home
          </Link>
        </div>
      </div>
    </div>
  );
};

