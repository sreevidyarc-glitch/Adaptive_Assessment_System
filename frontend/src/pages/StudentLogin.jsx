import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../api/auth';
import { GraduationCap, KeyRound, User, AlertCircle, ArrowRight } from 'lucide-react';

export const StudentLogin = () => {
  const [identifier, setIdentifier] = useState('ROLL2026001');
  const [password, setPassword] = useState('StudentPass123!');
  const [errorMessage, setErrorMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { setAuthSession } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setIsLoading(true);

    try {
      const tokenData = await authApi.studentLogin(identifier, password);
      setAuthSession(tokenData);
      navigate('/student/dashboard');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Invalid Roll Number / Email or password.';
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4 bg-slate-100">
      <div className="max-w-md w-full bg-white rounded-2xl border border-slate-200/90 shadow-xl overflow-hidden">
        {/* Header Banner */}
        <div className="student-gradient p-6 text-white text-center">
          <div className="inline-flex p-3 bg-white/10 rounded-xl mb-3 backdrop-blur-sm">
            <GraduationCap className="w-6 h-6 text-sky-200" />
          </div>
          <h2 className="text-xl font-bold tracking-tight">Student Assessment Gateway</h2>
          <p className="text-xs text-sky-200 mt-1 font-mono">
            INSTITUTIONAL ROLL-NUMBER CREDENTIALS
          </p>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="mx-6 mt-6 p-3.5 bg-rose-50 border border-rose-200 rounded-xl flex items-start gap-2.5 text-xs text-rose-700">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Form Body */}
        <div className="p-6">
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Roll Number or University Email
              </label>
              <div className="relative">
                <User className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
                <input
                  type="text"
                  required
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  placeholder="e.g. ROLL2026001 or student@university.edu"
                  className="w-full pl-10 pr-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white font-mono"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative">
                <KeyRound className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-10 pr-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 bg-sky-600 hover:bg-sky-700 text-white font-semibold py-2.5 rounded-xl text-sm transition-all shadow-md flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isLoading ? 'Verifying...' : 'Sign In to Assessment Portal (60 Min)'}
              <ArrowRight className="w-4 h-4" />
            </button>

            <div className="mt-4 p-3 bg-sky-50 rounded-xl border border-sky-100 text-[11px] text-sky-800 leading-relaxed">
              <strong>Student Demo Credentials:</strong>
              <div className="font-mono mt-0.5">Roll Number: ROLL2026001</div>
              <div className="font-mono">Password: StudentPass123!</div>
            </div>
          </form>

          <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <Link to="/faculty-login" className="text-purple-700 hover:underline">
              Faculty OTP portal login
            </Link>
            <Link to="/" className="text-slate-400 hover:text-slate-600">
              Return Home
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

