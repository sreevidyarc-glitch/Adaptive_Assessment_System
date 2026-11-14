import React, { useState } from 'react';
import { authApi } from '../../api/auth';
import {
  Sparkles,
  Sliders,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  BookOpen,
  ArrowRight,
  Layers,
  ChevronDown,
  ChevronUp,
  RotateCw,
  Send,
  Eye,
  Lock
} from 'lucide-react';

export const QuestionGeneratorStudio = ({ courseId, courseTitle, onQuestionsGenerated }) => {
  const [totalQuestions, setTotalQuestions] = useState(5);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationResult, setGenerationResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [expandedQuestionId, setExpandedQuestionId] = useState(null);

  const handleGenerate = async (e) => {
    e.preventDefault();
    setIsGenerating(true);
    setErrorMessage('');
    setSuccessMessage('');

    try {
      const data = await authApi.generateQuestions(courseId, totalQuestions);
      setGenerationResult(data);
      setSuccessMessage(
        `Successfully generated and validated ${data.total_generated} adaptive questions across ${data.allocations.length} learning objectives!`
      );
      if (onQuestionsGenerated) {
        onQuestionsGenerated();
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Question generation failed. Ensure course has objectives and materials.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleBatchPublish = async () => {
    if (!generationResult?.questions) return;
    const qIds = generationResult.questions.map((q) => q.id);

    try {
      await authApi.batchApproveQuestions(courseId, qIds, true, true);
      setSuccessMessage(`Approved and published all ${qIds.length} generated questions to enrolled students!`);
      if (onQuestionsGenerated) {
        onQuestionsGenerated();
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Batch approval failed.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Configuration & Launch Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4 mb-5">
          <div>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-600" />
              Adaptive Question Generation Studio
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Course: <strong className="text-slate-800">{courseTitle}</strong> • Largest Remainder Allocation & 4-Stage Validation
            </p>
          </div>

          <div className="flex items-center gap-2 bg-purple-50 text-purple-800 border border-purple-200 px-3 py-1 rounded-xl text-xs font-mono font-semibold">
            <Lock className="w-3.5 h-3.5 text-purple-600" />
            <span>Strict Student Privacy Protected</span>
          </div>
        </div>

        {errorMessage && (
          <div className="mb-4 p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
            <span>{errorMessage}</span>
          </div>
        )}

        {successMessage && (
          <div className="mb-4 p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
            <span>{successMessage}</span>
          </div>
        )}

        <form onSubmit={handleGenerate} className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-end">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                Total Questions to Allocate (N)
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={totalQuestions}
                  onChange={(e) => setTotalQuestions(Math.max(1, parseInt(e.target.value) || 1))}
                  className="w-24 py-2 px-3 text-center text-base font-mono font-bold bg-slate-50 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                <span className="text-xs text-slate-500">
                  Questions apportioned by priority weights
                </span>
              </div>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200/80 text-xs text-slate-600 space-y-1 md:col-span-2">
              <span className="font-bold text-slate-800 block">Algorithmic Safeguards Applied:</span>
              <ul className="grid grid-cols-1 sm:grid-cols-2 gap-1 text-[11px] list-disc list-inside text-slate-500">
                <li>Hamilton-Hare Largest Remainder Method</li>
                <li>Quota Deficit Trait Balancing</li>
                <li>Hint Leakage Detection & Rubric Sanity</li>
                <li>3-Retry Backoff & Duplicate Detection</li>
              </ul>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="submit"
              disabled={isGenerating}
              className="inline-flex items-center gap-2 bg-purple-700 hover:bg-purple-800 text-white font-semibold px-6 py-2.5 rounded-xl text-xs transition-all shadow-md disabled:opacity-50"
            >
              {isGenerating ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Generating & Running 4 Validation Checks...
                </>
              ) : (
                <>
                  Generate Adaptive Question Set
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Validation Badges Ribbon */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-wrap items-center justify-between gap-3 text-xs">
        <span className="font-semibold text-slate-700 flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          Active Multi-Stage Validation Pipeline:
        </span>
        <div className="flex flex-wrap items-center gap-2 font-mono text-[11px]">
          <span className="bg-emerald-50 text-emerald-800 border border-emerald-200 px-2.5 py-0.5 rounded-full">
            ✓ 1. Schema Integrity
          </span>
          <span className="bg-emerald-50 text-emerald-800 border border-emerald-200 px-2.5 py-0.5 rounded-full">
            ✓ 2. Hint Leakage Guard
          </span>
          <span className="bg-emerald-50 text-emerald-800 border border-emerald-200 px-2.5 py-0.5 rounded-full">
            ✓ 3. Rubric Sanity (Denominator &gt; 0)
          </span>
          <span className="bg-emerald-50 text-emerald-800 border border-emerald-200 px-2.5 py-0.5 rounded-full">
            ✓ 4. Duplicate Check (&le; 0.85)
          </span>
        </div>
      </div>

      {/* Generated Questions Review Section */}
      {generationResult && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Layers className="w-4 h-4 text-purple-600" />
                Generated Questions Review ({generationResult.total_generated} Items)
              </h3>
              <p className="text-xs text-slate-500">
                Largest Remainder Apportionment: {generationResult.allocations.map((a) => `${a.objective_code}: ${a.question_count}`).join(' • ')}
              </p>
            </div>

            <button
              onClick={handleBatchPublish}
              className="inline-flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-4 py-2 rounded-xl text-xs transition-colors shadow-sm self-start sm:self-auto"
            >
              <Send className="w-3.5 h-3.5" />
              Approve & Publish All to Students
            </button>
          </div>

          <div className="space-y-4">
            {generationResult.questions.map((q, idx) => {
              const isExpanded = expandedQuestionId === q.id;
              return (
                <div
                  key={q.id}
                  className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3 hover:border-purple-300 transition-all"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-purple-100 text-purple-800">
                        {q.objective_code}
                      </span>
                      <span className="px-2.5 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700">
                        {q.trait_name}
                      </span>
                      <span className="text-slate-400 text-xs font-mono">
                        Question #{idx + 1}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-100 text-emerald-800">
                        <CheckCircle2 className="w-3 h-3" />
                        {q.validation_status} ({q.generation_retries} attempts)
                      </span>
                    </div>
                  </div>

                  <p className="text-sm font-medium text-slate-900 leading-relaxed">
                    {q.prompt}
                  </p>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
                    <button
                      type="button"
                      onClick={() => setExpandedQuestionId(isExpanded ? null : q.id)}
                      className="inline-flex items-center gap-1 text-purple-700 font-semibold hover:text-purple-900"
                    >
                      {isExpanded ? (
                        <>Hide Privileged Rubric & Model Answer <ChevronUp className="w-4 h-4" /></>
                      ) : (
                        <>Inspect Privileged Rubric & Model Answer <ChevronDown className="w-4 h-4" /></>
                      )}
                    </button>

                    <span className="text-[11px] text-slate-400 italic">
                      Never exposed to students
                    </span>
                  </div>

                  {/* Privileged Details (Faculty Only) */}
                  {isExpanded && (
                    <div className="mt-3 pt-3 border-t border-dashed border-slate-200 bg-slate-50/70 -mx-5 -mb-5 p-5 rounded-b-xl space-y-4">
                      {/* Rubric */}
                      {q.rubric && (
                        <div>
                          <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                            <Lock className="w-3.5 h-3.5 text-purple-600" />
                            Scoring Rubric ({q.rubric.total_points} Total Points)
                          </div>
                          <div className="space-y-1.5">
                            {q.rubric.criteria.map((c, cIdx) => (
                              <div
                                key={cIdx}
                                className="bg-white p-2.5 rounded-lg border border-slate-200 text-xs flex justify-between items-center"
                              >
                                <span className="font-medium text-slate-700">{c.criterion}</span>
                                <span className="font-mono text-purple-700 font-bold shrink-0 ml-3">
                                  {c.max_points} pts (w={c.weight})
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Model Answer */}
                      {q.model_answer && (
                        <div>
                          <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 uppercase tracking-wider mb-1">
                            <BookOpen className="w-3.5 h-3.5 text-purple-600" />
                            Canonical Model Answer
                          </div>
                          <p className="bg-white p-3 rounded-lg border border-slate-200 text-xs text-slate-700 font-mono leading-relaxed">
                            {q.model_answer.content}
                          </p>
                        </div>
                      )}

                      {/* Progressive Hints */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                        <div className="bg-white p-3 rounded-lg border border-slate-200">
                          <span className="font-bold text-slate-800 block mb-1">Hint 1 (Low Scaffold):</span>
                          <span className="text-slate-600">{q.hint1 || 'None'}</span>
                        </div>
                        <div className="bg-white p-3 rounded-lg border border-slate-200">
                          <span className="font-bold text-slate-800 block mb-1">Hint 2 (High Scaffold):</span>
                          <span className="text-slate-600">{q.hint2 || 'None'}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

