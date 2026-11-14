import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  HelpCircle, 
  CheckCircle2, 
  AlertCircle, 
  Send, 
  ChevronRight, 
  ChevronLeft, 
  Lightbulb, 
  Award,
  Sparkles,
  ArrowRight,
  RotateCcw
} from 'lucide-react';
import { authApi } from '../../api/auth';

export default function AssessmentTaker({ courseId, courseTitle, isPost = false, onComplete, onCancel }) {
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [sessionData, setSessionData] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({}); // { [qId]: string }
  const [hintsUnlocked, setHintsUnlocked] = useState({}); // { [qId]: { hint1: bool, hint2: bool } }
  const [error, setError] = useState(null);
  const [submissionResult, setSubmissionResult] = useState(null);

  useEffect(() => {
    loadAssessment();
  }, [courseId, isPost]);

  const loadAssessment = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = isPost 
        ? await authApi.startPostAssessment(courseId)
        : await authApi.startAssessmentSession(courseId);
      setSessionData(data);
      // Initialize answer map
      const initialAnswers = {};
      const initialHints = {};
      (data.questions || []).forEach(q => {
        initialAnswers[q.id] = '';
        initialHints[q.id] = { hint1: false, hint2: false };
      });
      setAnswers(initialAnswers);
      setHintsUnlocked(initialHints);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start assessment session.');
    } finally {
      setLoading(false);
    }
  };

  const handleTextChange = (qId, text) => {
    setAnswers(prev => ({ ...prev, [qId]: text }));
  };

  const unlockHint = (qId, hintNumber) => {
    setHintsUnlocked(prev => ({
      ...prev,
      [qId]: {
        ...prev[qId],
        [`hint${hintNumber}`]: true
      }
    }));
  };

  const handleSubmit = async () => {
    if (!sessionData) return;
    
    // Check if at least one question is answered
    const questions = sessionData.questions || [];
    const answeredCount = questions.filter(q => (answers[q.id] || '').trim().length > 0).length;
    if (answeredCount === 0) {
      alert('Please answer at least one question before submitting.');
      return;
    }

    if (answeredCount < questions.length) {
      const confirmIncomplete = window.confirm(
        `You have answered ${answeredCount} of ${questions.length} questions. Unanswered questions will receive 0 points. Do you want to submit anyway?`
      );
      if (!confirmIncomplete) return;
    }

    setSubmitting(true);
    setError(null);

    const payload = questions.map(q => {
      const hintState = hintsUnlocked[q.id] || {};
      const hintsCount = (hintState.hint1 ? 1 : 0) + (hintState.hint2 ? 1 : 0);
      return {
        question_id: q.id,
        response_text: (answers[q.id] || '').trim(),
        hints_used: hintsCount
      };
    });

    try {
      const result = isPost
        ? await authApi.submitPostAssessment(sessionData.session_id, payload)
        : await authApi.submitAssessmentSession(sessionData.session_id, payload);
      setSubmissionResult(result);
      if (onComplete) onComplete(result);
    } catch (err) {
      setError(err.response?.data?.detail || 'Submission failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-indigo-600 border-t-transparent mb-4"></div>
        <p className="text-slate-600 font-medium">Preparing your adaptive assessment...</p>
      </div>
    );
  }

  if (error && !sessionData) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
        <AlertCircle className="w-8 h-8 text-red-600 mx-auto mb-2" />
        <h3 className="text-lg font-semibold text-red-900">Assessment Unavailable</h3>
        <p className="text-sm text-red-700 mt-1">{error}</p>
        <button
          onClick={onCancel}
          className="mt-4 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  const questions = sessionData?.questions || [];
  if (questions.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
        <BookOpen className="w-10 h-10 text-slate-400 mx-auto mb-3" />
        <h3 className="text-lg font-semibold text-slate-800">No Questions Published Yet</h3>
        <p className="text-sm text-slate-500 mt-1 max-w-md mx-auto">
          The instructor has not published any approved questions for this course yet. Please check back later.
        </p>
        <button
          onClick={onCancel}
          className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  // Post-submission summary view
  if (submissionResult) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="bg-gradient-to-r from-emerald-600 to-teal-700 px-6 py-8 text-white text-center">
          <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-3 backdrop-blur-sm">
            <Award className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold">Assessment Completed!</h2>
          <p className="text-emerald-100 text-sm mt-1">
            Your responses have been evaluated against verified rubrics and your mastery matrix has been updated.
          </p>
          <div className="mt-6 flex justify-center gap-6">
            <div className="bg-white/10 px-4 py-2 rounded-lg backdrop-blur-sm">
              <div className="text-xs uppercase tracking-wider text-emerald-200">Earned Score</div>
              <div className="text-2xl font-bold">{submissionResult.earned_points} / {submissionResult.total_possible_points}</div>
            </div>
            <div className="bg-white/10 px-4 py-2 rounded-lg backdrop-blur-sm">
              <div className="text-xs uppercase tracking-wider text-emerald-200">Achievement</div>
              <div className="text-2xl font-bold">{submissionResult.overall_percentage}%</div>
            </div>
          </div>

          {submissionResult.session_type === 'POST' && (
            <div className="mt-4 p-3 bg-white/20 rounded-xl max-w-md mx-auto backdrop-blur-sm text-center">
              <span className="text-xs uppercase tracking-wider text-emerald-200 block">Normalized Learning Gain (g)</span>
              <div className="text-2xl font-bold font-mono">
                {submissionResult.normalized_gain !== null && submissionResult.normalized_gain !== undefined
                  ? submissionResult.normalized_gain.toFixed(2)
                  : 'N/A'}
              </div>
              <span className="text-[11px] text-emerald-100 font-semibold">
                {submissionResult.gain_category ? `${submissionResult.gain_category} GAIN` : ''}
              </span>
            </div>
          )}
        </div>

        <div className="p-6">
          <h3 className="text-md font-bold text-slate-800 mb-4 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            Evaluation Breakdown
          </h3>
          <div className="space-y-3">
            {submissionResult.results?.map((res, i) => (
              <div key={res.question_id || i} className="p-4 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold uppercase px-2 py-0.5 bg-slate-200 text-slate-700 rounded mr-2">
                    Question {i + 1}
                  </span>
                  <span className="text-xs text-slate-500">
                    Hints Used: {res.hints_used}
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <span className="text-sm font-bold text-slate-800">{res.earned_points} pts</span>
                    <span className="text-xs text-slate-500 block">
                      Fraction f = {(res.fraction_achieved * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className={`w-3 h-3 rounded-full ${res.fraction_achieved >= 0.75 ? 'bg-emerald-500' : res.fraction_achieved >= 0.4 ? 'bg-amber-500' : 'bg-red-500'}`} />
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 pt-6 border-t border-slate-200 flex justify-end">
            <button
              onClick={onCancel}
              className="px-6 py-2.5 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 flex items-center gap-2 shadow-sm"
            >
              View Updated Mastery Matrix
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  const currentQ = questions[currentIndex];
  const currentHints = hintsUnlocked[currentQ.id] || { hint1: false, hint2: false };
  const currentAnswer = answers[currentQ.id] || '';

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Top Banner & Progress */}
      <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
        <div>
          <span className="text-xs font-medium text-indigo-400 uppercase tracking-wider">
            {sessionData.course_code} - {courseTitle}
          </span>
          <h2 className="text-lg font-bold">Adaptive Assessment Session</h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-slate-300">
            Question {currentIndex + 1} of {questions.length}
          </span>
        </div>
      </div>

      {/* Question Progress Dots */}
      <div className="bg-slate-100 px-6 py-2.5 flex items-center gap-1.5 border-b border-slate-200 overflow-x-auto">
        {questions.map((q, idx) => {
          const isAnswered = (answers[q.id] || '').trim().length > 0;
          const isCurrent = idx === currentIndex;
          return (
            <button
              key={q.id}
              onClick={() => setCurrentIndex(idx)}
              className={`w-7 h-7 rounded-full text-xs font-semibold flex items-center justify-center transition-all ${
                isCurrent 
                  ? 'bg-indigo-600 text-white ring-2 ring-indigo-300' 
                  : isAnswered 
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' 
                    : 'bg-white text-slate-600 border border-slate-300 hover:bg-slate-50'
              }`}
            >
              {idx + 1}
            </button>
          );
        })}
      </div>

      {/* Main Question Body */}
      <div className="p-6">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-100 text-indigo-800">
              {currentQ.objective_code}
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700">
              {currentQ.trait_name || 'General Trait'}
            </span>
          </div>
        </div>

        <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 mb-6">
          <p className="text-slate-900 font-medium text-base leading-relaxed whitespace-pre-wrap">
            {currentQ.prompt}
          </p>
        </div>

        {/* Hints Section */}
        <div className="mb-6 space-y-2">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
            <Lightbulb className="w-3.5 h-3.5 text-amber-500" />
            Adaptive Scaffolding & Hints
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* Hint 1 */}
            <div className="p-3.5 rounded-lg border border-slate-200 bg-white">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-semibold text-slate-700">Hint 1 (Low Scaffold)</span>
                {!currentHints.hint1 ? (
                  <button
                    onClick={() => unlockHint(currentQ.id, 1)}
                    className="text-xs text-indigo-600 hover:text-indigo-800 font-medium hover:underline"
                  >
                    Unlock Hint 1
                  </button>
                ) : (
                  <span className="text-xs text-emerald-600 font-medium">Unlocked</span>
                )}
              </div>
              {currentHints.hint1 ? (
                <p className="text-xs text-slate-600 italic bg-amber-50/60 p-2 rounded border border-amber-200/50">
                  {currentQ.hint1 || 'Focus on the foundational properties and definitions of this objective.'}
                </p>
              ) : (
                <p className="text-xs text-slate-400">Locked. Click unlock to view targeted conceptual hint.</p>
              )}
            </div>

            {/* Hint 2 */}
            <div className="p-3.5 rounded-lg border border-slate-200 bg-white">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-semibold text-slate-700">Hint 2 (High Scaffold)</span>
                {!currentHints.hint2 ? (
                  <button
                    onClick={() => unlockHint(currentQ.id, 2)}
                    className="text-xs text-indigo-600 hover:text-indigo-800 font-medium hover:underline"
                  >
                    Unlock Hint 2
                  </button>
                ) : (
                  <span className="text-xs text-emerald-600 font-medium">Unlocked</span>
                )}
              </div>
              {currentHints.hint2 ? (
                <p className="text-xs text-slate-600 italic bg-amber-50/60 p-2 rounded border border-amber-200/50">
                  {currentQ.hint2 || 'Deconstruct into subproblems and evaluate boundary conditions.'}
                </p>
              ) : (
                <p className="text-xs text-slate-400">Locked. Click unlock for step-by-step structural guidance.</p>
              )}
            </div>
          </div>
        </div>

        {/* Answer Input */}
        <div>
          <label className="block text-sm font-semibold text-slate-800 mb-2">
            Your Response & Analysis:
          </label>
          <textarea
            value={currentAnswer}
            onChange={(e) => handleTextChange(currentQ.id, e.target.value)}
            rows={6}
            placeholder="Write your detailed academic response here. State mathematical assumptions, step-by-step reasoning, and final conclusions..."
            className="w-full px-4 py-3 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm font-mono"
          />
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Navigation & Submission Controls */}
        <div className="mt-6 pt-4 border-t border-slate-200 flex items-center justify-between">
          <button
            onClick={() => setCurrentIndex(prev => Math.max(0, prev - 1))}
            disabled={currentIndex === 0}
            className="px-4 py-2 border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
          >
            <ChevronLeft className="w-4 h-4" />
            Previous
          </button>

          <div className="flex items-center gap-3">
            {currentIndex < questions.length - 1 ? (
              <button
                onClick={() => setCurrentIndex(prev => Math.min(questions.length - 1, prev + 1))}
                className="px-5 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 flex items-center gap-1.5 shadow-sm"
              >
                Next
                <ChevronRight className="w-4 h-4" />
              </button>
            ) : null}

            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="px-6 py-2 bg-emerald-600 text-white rounded-lg text-sm font-bold hover:bg-emerald-700 disabled:opacity-50 flex items-center gap-2 shadow-sm"
            >
              {submitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Evaluating...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Submit Assessment
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

