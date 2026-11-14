import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../api/auth';
import { ShieldCheck, Lock, Mail, KeyRound, AlertCircle, ArrowLeft, ArrowRight, CheckCircle2 } from 'lucide-react';

export const FacultyLogin = () => {
  const [step, setStep] = useState(1); // 1: Credentials, 2: OTP
  const [email, setEmail] = useState('faculty@university.edu');
  const [password, setPassword] = useState('FacultyPass123!');
  const [sessionTicket, setSessionTicket] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [devOtpHint, setDevOtpHint] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { setAuthSession } = useAuth();
  const navigate = useNavigate();

  const handleCredentialsSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setIsLoading(true);

    try {
      const data = await authApi.facultyLoginInit(email, password);
      setSessionTicket(data.session_ticket);
      if (data.dev_otp) {
        setDevOtpHint(data.dev_otp);
        setOtpCode(data.dev_otp); // Pre-fill in dev mode for ease of evaluation
      }
      setStep(2);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to authenticate credentials. Check email and password.';
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOtpSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setIsLoading(true);

    try {
      const tokenData = await authApi.facultyVerifyOTP(sessionTicket, otpCode);
      setAuthSession(tokenData);
      navigate('/faculty/dashboard');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Invalid OTP code. Please try again.';
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4 bg-slate-100">
      <div className="max-w-md w-full bg-white rounded-2xl border border-slate-200/90 shadow-xl overflow-hidden">
        {/* Header Banner */}
        <div className="faculty-gradient p-6 text-white text-center">
          <div className="inline-flex p-3 bg-white/10 rounded-xl mb-3 backdrop-blur-sm">
            <Lock className="w-6 h-6 text-purple-200" />
          </div>
          <h2 className="text-xl font-bold tracking-tight">Faculty Workspace</h2>
          <p className="text-xs text-purple-200 mt-1 font-mono">
            {step === 1 ? 'STEP 1 OF 2: ACADEMIC CREDENTIALS' : 'STEP 2 OF 2: ONE-TIME PASSCODE (OTP)'}
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
          {step === 1 ? (
            <form onSubmit={handleCredentialsSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Institutional Email
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="faculty@university.edu"
                    className="w-full pl-10 pr-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:bg-white"
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
                    className="w-full pl-10 pr-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:bg-white"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full mt-2 bg-purple-700 hover:bg-purple-800 text-white font-semibold py-2.5 rounded-xl text-sm transition-all shadow-md flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isLoading ? 'Verifying...' : 'Request Verification OTP'}
                <ArrowRight className="w-4 h-4" />
              </button>

              <div className="mt-4 p-3 bg-purple-50 rounded-xl border border-purple-100 text-[11px] text-purple-800 leading-relaxed">
                <strong>Faculty Demo Credentials:</strong>
                <div className="font-mono mt-0.5">Email: faculty@university.edu</div>
                <div className="font-mono">Password: FacultyPass123!</div>
              </div>
            </form>
          ) : (
            <form onSubmit={handleOtpSubmit} className="space-y-4">
              <div className="text-center space-y-1">
                <p className="text-xs text-slate-600">
                  Verification code dispatched for <strong className="text-slate-900">{email}</strong>
                </p>
                {devOtpHint && (
                  <div className="inline-flex items-center gap-1.5 bg-emerald-50 text-emerald-800 border border-emerald-200 px-3 py-1 rounded-full text-xs font-mono font-bold mt-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    Dev Auto-Code: {devOtpHint}
                  </div>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5 text-center">
                  Enter 6-Digit OTP Code
                </label>
                <input
                  type="text"
                  maxLength={6}
                  required
                  autoFocus
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                  placeholder="000000"
                  className="w-full tracking-widest text-center py-3 text-2xl font-mono font-bold bg-slate-50 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:bg-white"
                />
              </div>

              <button
                type="submit"
                disabled={isLoading || otpCode.length < 6}
                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2.5 rounded-xl text-sm transition-all shadow-md flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isLoading ? 'Authenticating...' : 'Authorize Faculty Session (30 Min)'}
                <ShieldCheck className="w-4 h-4" />
              </button>

              <button
                type="button"
                onClick={() => setStep(1)}
                className="w-full text-xs text-slate-500 hover:text-slate-800 flex items-center justify-center gap-1 py-1"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Back to credentials
              </button>
            </form>
          )}

          <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <Link to="/student-login" className="text-sky-600 hover:underline">
              Student portal login
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

