import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { GraduationCap, ShieldCheck, LogOut, UserCheck, BookOpen } from 'lucide-react';

export const Navbar = () => {
  const { user, role, isFaculty, isStudent, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-50 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="p-2 bg-gradient-to-tr from-sky-500 to-indigo-600 rounded-lg group-hover:scale-105 transition-transform">
              <GraduationCap className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight block leading-tight text-white">
                Adaptive Assessment
              </span>
              <span className="text-xs text-sky-400 font-mono tracking-wider">
                AI ACADEMIC PORTAL
              </span>
            </div>
          </Link>

          {/* Navigation & User Section */}
          <div className="flex items-center gap-4">
            {isAuthenticated && user ? (
              <>
                <div className="flex items-center gap-3 bg-slate-800/80 border border-slate-700/60 rounded-full py-1.5 px-4 text-sm">
                  <div className={`w-2.5 h-2.5 rounded-full animate-pulse ${isFaculty ? 'bg-purple-400' : 'bg-emerald-400'}`} />
                  <div className="text-left">
                    <p className="font-medium text-slate-200 leading-tight">
                      {user.full_name}
                    </p>
                    <p className="text-[11px] text-slate-400 leading-tight font-mono">
                      {isFaculty ? 'FACULTY' : `ROLL: ${user.roll_number || 'STUDENT'}`}
                    </p>
                  </div>
                </div>

                <button
                  onClick={handleLogout}
                  className="inline-flex items-center gap-2 bg-slate-800 hover:bg-rose-900/40 text-slate-300 hover:text-rose-200 border border-slate-700 hover:border-rose-700/50 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all"
                  title="Logout and revoke active session"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="hidden sm:inline">Logout</span>
                </button>
              </>
            ) : (
              <div className="flex items-center gap-3 text-sm">
                <Link
                  to="/faculty-login"
                  className="text-purple-300 hover:text-white px-3 py-1.5 rounded-md hover:bg-purple-950/50 transition-colors font-medium"
                >
                  Faculty Login
                </Link>
                <Link
                  to="/student-login"
                  className="bg-sky-600 hover:bg-sky-500 text-white px-4 py-1.5 rounded-lg font-medium shadow-sm transition-all"
                >
                  Student Portal
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

