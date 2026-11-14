import React from 'react';
import { Link } from 'react-router-dom';
import { GraduationCap, ShieldCheck, Cpu, BarChart3, Lock, ArrowRight, CheckCircle2 } from 'lucide-react';

export const Home = () => {
  return (
    <div className="min-h-[calc(100vh-4rem)] flex flex-col justify-between">
      {/* Hero Header */}
      <section className="academic-gradient text-white py-16 px-4 sm:px-6 lg:px-8 shadow-inner">
        <div className="max-w-5xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center gap-2 bg-sky-500/20 border border-sky-400/30 px-3 py-1 rounded-full text-xs font-mono text-sky-200">
            <ShieldCheck className="w-4 h-4 text-sky-400" />
            <span>ALGORITHM-DRIVEN & PRIVACY-AWARE ARCHITECTURE</span>
          </div>
          
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">
            AI-Powered Adaptive Assessment System
          </h1>
          
          <p className="text-base sm:text-lg text-slate-300 max-w-3xl mx-auto font-normal leading-relaxed">
            Multi-tier assessment platform delivering objective-level mapping, AI-scaffolded question generation,
            role-based authentication, and personalized mastery analytics with strict student privacy.
          </p>

          <div className="pt-4 flex flex-wrap justify-center gap-4">
            <Link
              to="/student-login"
              className="inline-flex items-center gap-2 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold px-6 py-3 rounded-xl shadow-lg hover:shadow-sky-500/20 transition-all text-sm"
            >
              Student Portal Access
              <ArrowRight className="w-4 h-4" />
            </Link>

            <Link
              to="/faculty-login"
              className="inline-flex items-center gap-2 bg-purple-600 hover:bg-purple-500 text-white font-semibold px-6 py-3 rounded-xl shadow-lg hover:shadow-purple-500/20 transition-all text-sm border border-purple-400/30"
            >
              Faculty Workspace (OTP Secured)
              <Lock className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Role Access Cards */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8 w-full">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Faculty Card */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-md hover:shadow-lg transition-all flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="p-3 bg-purple-100 text-purple-700 rounded-xl inline-block">
                  <Lock className="w-6 h-6" />
                </span>
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-purple-700 bg-purple-50 px-2.5 py-1 rounded-full border border-purple-200">
                  30-Min Session Token
                </span>
              </div>
              <div>
                <h3 className="text-xl font-bold text-slate-900">Faculty Gateway</h3>
                <p className="text-slate-600 text-sm mt-1">
                  Email/Password authentication fortified by mandatory one-time verification (OTP).
                </p>
              </div>
              <ul className="space-y-2 text-xs text-slate-600">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-purple-600 shrink-0" />
                  Course-objective curriculum mapping & allocation
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-purple-600 shrink-0" />
                  Review & approve AI questions with rubrics & model answers
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-purple-600 shrink-0" />
                  Class-level mastery aggregation matrix inspection
                </li>
              </ul>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs text-slate-500 font-mono">Demo: faculty@university.edu</span>
              <Link
                to="/faculty-login"
                className="text-xs font-bold text-purple-700 hover:text-purple-900 inline-flex items-center gap-1"
              >
                Enter Portal &rarr;
              </Link>
            </div>
          </div>

          {/* Student Card */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-md hover:shadow-lg transition-all flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="p-3 bg-sky-100 text-sky-700 rounded-xl inline-block">
                  <GraduationCap className="w-6 h-6" />
                </span>
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-sky-700 bg-sky-50 px-2.5 py-1 rounded-full border border-sky-200">
                  60-Min Session Token
                </span>
              </div>
              <div>
                <h3 className="text-xl font-bold text-slate-900">Student Portal</h3>
                <p className="text-slate-600 text-sm mt-1">
                  Enrolled candidate sign-in via Institutional Roll Number credentials.
                </p>
              </div>
              <ul className="space-y-2 text-xs text-slate-600">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-sky-600 shrink-0" />
                  Privacy-first: personal mastery score isolation
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-sky-600 shrink-0" />
                  Zero rubric/model answer leakage in client responses
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-sky-600 shrink-0" />
                  Objective Radar charts & personalized remedial roadmaps
                </li>
              </ul>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs text-slate-500 font-mono">Demo: ROLL2026001</span>
              <Link
                to="/student-login"
                className="text-xs font-bold text-sky-700 hover:text-sky-900 inline-flex items-center gap-1"
              >
                Enter Portal &rarr;
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 text-center text-xs text-slate-400 border-t border-slate-200 mt-12 bg-white">
        <p>AI-Powered Adaptive Assessment System • Built strictly to Section 3 & 4 Algorithm & Security Specifications</p>
      </footer>
    </div>
  );
};

