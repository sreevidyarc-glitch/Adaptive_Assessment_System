import React, { useState } from 'react';
import { CheckCircle2, Clock, ShieldAlert, BookOpen, ChevronDown, ChevronUp, Sparkles } from 'lucide-react';

export const QuestionApprovalCard = ({ question, onApprove }) => {
  const [expanded, setExpanded] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);

  const handleToggleApproval = async () => {
    setIsUpdating(true);
    try {
      await onApprove(question.id, !question.is_approved, !question.is_approved);
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className={`bg-white rounded-xl border transition-all ${question.is_approved ? 'border-emerald-200 shadow-sm' : 'border-amber-200/80 shadow-sm'}`}>
      <div className="p-5">
        {/* Header tags */}
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-md text-xs font-semibold bg-purple-100 text-purple-800">
              {question.objective_code}
            </span>
            <span className="px-2.5 py-0.5 rounded-md text-xs font-medium bg-slate-100 text-slate-700">
              {question.trait_name || 'General Trait'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {question.is_approved ? (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                <CheckCircle2 className="w-3.5 h-3.5" /> Approved
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">
                <Clock className="w-3.5 h-3.5" /> Pending Faculty Review
              </span>
            )}
          </div>
        </div>

        {/* Prompt */}
        <p className="text-slate-900 font-medium leading-relaxed mb-4">
          {question.prompt}
        </p>

        {/* Toggle details */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
          <button
            onClick={() => setExpanded(!expanded)}
            className="inline-flex items-center gap-1 text-purple-700 font-semibold hover:text-purple-900"
          >
            {expanded ? (
              <>Hide Rubric & Model Answer <ChevronUp className="w-4 h-4" /></>
            ) : (
              <>Inspect Rubric & Model Answer (Faculty Only) <ChevronDown className="w-4 h-4" /></>
            )}
          </button>

          <button
            onClick={handleToggleApproval}
            disabled={isUpdating}
            className={`px-3 py-1.5 rounded-lg font-medium text-xs transition-colors ${
              question.is_approved
                ? 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                : 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm'
            }`}
          >
            {isUpdating ? 'Saving...' : question.is_approved ? 'Revoke Approval' : 'Approve & Publish'}
          </button>
        </div>

        {/* Privileged Faculty-Only Details */}
        {expanded && (
          <div className="mt-4 pt-4 border-t border-dashed border-slate-200 space-y-4 bg-slate-50/70 -mx-5 -mb-5 p-5 rounded-b-xl">
            {/* Rubric View */}
            {question.rubric && (
              <div>
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                  <ShieldAlert className="w-3.5 h-3.5 text-purple-600" />
                  Privileged Assessment Rubric ({question.rubric.total_points} Points)
                </div>
                <div className="space-y-2">
                  {question.rubric.criteria.map((c, idx) => (
                    <div key={idx} className="bg-white p-2.5 rounded-lg border border-slate-200 text-xs flex justify-between items-start">
                      <span className="font-medium text-slate-700">{c.criterion}</span>
                      <span className="font-mono text-purple-700 font-semibold shrink-0 ml-3">{c.max_points} pts (w={c.weight})</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Model Answer */}
            {question.model_answer && (
              <div>
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 uppercase tracking-wider mb-1">
                  <BookOpen className="w-3.5 h-3.5 text-purple-600" />
                  Canonical Model Answer
                </div>
                <p className="bg-white p-3 rounded-lg border border-slate-200 text-xs text-slate-700 leading-relaxed font-mono">
                  {question.model_answer.content}
                </p>
              </div>
            )}

            {/* Hints */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="bg-white p-2.5 rounded-lg border border-slate-200">
                <span className="font-semibold text-slate-800 block mb-1">Hint 1 (Low Scaffold):</span>
                <span className="text-slate-600">{question.hint1 || 'None'}</span>
              </div>
              <div className="bg-white p-2.5 rounded-lg border border-slate-200">
                <span className="font-semibold text-slate-800 block mb-1">Hint 2 (High Scaffold):</span>
                <span className="text-slate-600">{question.hint2 || 'None'}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

