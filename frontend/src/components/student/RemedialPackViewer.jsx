import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  CheckCircle2, 
  AlertTriangle, 
  HelpCircle, 
  Sparkles, 
  ChevronRight, 
  Lightbulb, 
  FileText, 
  ArrowRight,
  ShieldCheck,
  Check,
  Clock
} from 'lucide-react';
import { authApi } from '../../api/auth';

export default function RemedialPackViewer({ courseId, courseTitle, onStartPostAssessment }) {
  const [loading, setLoading] = useState(true);
  const [packs, setPacks] = useState([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [revealedHints, setRevealedHints] = useState({}); // { [itemIndex]: bool }
  const [error, setError] = useState(null);
  const [completingId, setCompletingId] = useState(null);

  useEffect(() => {
    if (courseId) {
      loadPacks();
    }
  }, [courseId]);

  const loadPacks = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await authApi.getRemedialPacks(courseId);
      setPacks(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load remedial learning packs.');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkComplete = async (packId) => {
    setCompletingId(packId);
    try {
      await authApi.completeRemedialPack(packId);
      setPacks(prev => prev.map(p => p.id === packId ? { ...p, is_completed: true } : p));
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update pack completion status.');
    } finally {
      setCompletingId(null);
    }
  };

  const toggleHint = (itemIndex) => {
    setRevealedHints(prev => ({
      ...prev,
      [itemIndex]: !prev[itemIndex]
    }));
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-indigo-600 border-t-transparent mb-4"></div>
        <p className="text-slate-600 font-medium">Curating personalized remedial packs...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-50 border border-rose-200 rounded-xl p-6 text-center">
        <p className="text-rose-700 font-medium">{error}</p>
        <button
          onClick={loadPacks}
          className="mt-3 px-4 py-1.5 bg-rose-600 text-white rounded-lg text-xs font-semibold hover:bg-rose-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (packs.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
        <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-3" />
        <h3 className="text-lg font-bold text-slate-800">No Learning Gaps Identified!</h3>
        <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
          All your objective competencies currently meet or exceed the target threshold. You are ready to take the post-assessment!
        </p>
        {onStartPostAssessment && (
          <button
            onClick={onStartPostAssessment}
            className="mt-4 px-5 py-2.5 bg-indigo-600 text-white font-medium text-xs rounded-lg hover:bg-indigo-700 inline-flex items-center gap-2 shadow-sm"
          >
            Launch Post-Assessment
            <ArrowRight className="w-4 h-4" />
          </button>
        )}
      </div>
    );
  }

  const currentPack = packs[selectedIndex] || packs[0];
  const allCompleted = packs.every(p => p.is_completed);

  return (
    <div className="space-y-6">
      {/* Top Banner & Launch CTA */}
      <div className="bg-gradient-to-r from-indigo-900 to-slate-900 text-white rounded-2xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider bg-indigo-500/30 text-indigo-200 border border-indigo-400/30">
              Personalized Remedial Learning
            </span>
            <span className="text-xs text-slate-300 font-mono">
              {packs.length} Identified Gap Modules
            </span>
          </div>
          <h2 className="text-xl font-bold">Targeted Concept Remediation Packs</h2>
          <p className="text-xs text-slate-300 mt-1 max-w-xl">
            Ranked in descending priority (G_o,t). Review fundamental concepts and self-check practice items to close learning gaps before post-assessment.
          </p>
        </div>

        {onStartPostAssessment && (
          <button
            onClick={onStartPostAssessment}
            className="px-5 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold inline-flex items-center gap-2 shadow-sm transition-all shrink-0 self-start md:self-auto"
          >
            <Sparkles className="w-4 h-4" />
            Proceed to Post-Assessment
            <ArrowRight className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Main Layout: Left Sidebar Gap Selector + Right Pack Content */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Gap Selector List */}
        <div className="lg:col-span-4 space-y-3">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">
            Ranked Learning Gaps (Priority Order)
          </span>

          <div className="space-y-2">
            {packs.map((pack, idx) => {
              const isSelected = idx === selectedIndex;
              const isFoundational = pack.recommendation_type === 'FOUNDATIONAL';
              return (
                <button
                  key={pack.id}
                  onClick={() => {
                    setSelectedIndex(idx);
                    setRevealedHints({});
                  }}
                  className={`w-full text-left p-3.5 rounded-xl border transition-all flex flex-col justify-between ${
                    isSelected
                      ? 'bg-indigo-50/70 border-indigo-300 ring-2 ring-indigo-500/20'
                      : 'bg-white border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-mono font-bold text-slate-900">
                      {pack.objective_code} • {pack.trait_name}
                    </span>
                    <span className="text-[11px] font-mono font-bold text-slate-600">
                      Gap G = {pack.gap_score.toFixed(2)}
                    </span>
                  </div>

                  <p className="text-xs text-slate-600 line-clamp-1 mb-2 font-medium">
                    {pack.title}
                  </p>

                  <div className="flex items-center justify-between text-[10px]">
                    <span className={`px-2 py-0.5 rounded font-bold uppercase ${
                      isFoundational 
                        ? 'bg-rose-100 text-rose-800' 
                        : 'bg-amber-100 text-amber-800'
                    }`}>
                      {pack.recommendation_type}
                    </span>

                    {pack.is_completed ? (
                      <span className="text-emerald-700 font-semibold flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Completed
                      </span>
                    ) : (
                      <span className="text-slate-400 font-medium">To Review</span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected Pack Details */}
        <div className="lg:col-span-8 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-6">
          {/* Pack Header */}
          <div className="border-b border-slate-100 pb-4 flex flex-col sm:flex-row sm:items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-indigo-100 text-indigo-800">
                  {currentPack.objective_code}
                </span>
                <span className={`px-2.5 py-0.5 rounded text-xs font-bold uppercase ${
                  currentPack.recommendation_type === 'FOUNDATIONAL' 
                    ? 'bg-rose-100 text-rose-800' 
                    : 'bg-amber-100 text-amber-800'
                }`}>
                  {currentPack.recommendation_type} Learning
                </span>
                <span className="text-xs font-medium text-slate-500">
                  Trait: <strong>{currentPack.trait_name}</strong>
                </span>
              </div>
              <h3 className="text-lg font-bold text-slate-900 mt-1">
                {currentPack.title}
              </h3>
              <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                {currentPack.summary}
              </p>
            </div>

            <button
              onClick={() => handleMarkComplete(currentPack.id)}
              disabled={currentPack.is_completed || completingId === currentPack.id}
              className={`px-4 py-2 rounded-xl text-xs font-bold inline-flex items-center gap-1.5 transition-all shrink-0 ${
                currentPack.is_completed
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200 cursor-default'
                  : 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm'
              }`}
            >
              {currentPack.is_completed ? (
                <>
                  <Check className="w-3.5 h-3.5" /> Completed
                </>
              ) : (
                <>
                  <Check className="w-3.5 h-3.5" /> Mark Completed
                </>
              )}
            </button>
          </div>

          {/* Key Conceptual Principles */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              Core Theoretical Concepts & Pitfall Alerts
            </h4>
            <ul className="space-y-1.5">
              {(currentPack.key_concepts || []).map((concept, idx) => (
                <li key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-800 flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 mt-1.5 shrink-0" />
                  <span>{concept}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Reading Chunks from Course Material */}
          {currentPack.reading_chunks && currentPack.reading_chunks.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <BookOpen className="w-3.5 h-3.5 text-purple-600" />
                Curriculum Material Chunks
              </h4>
              <div className="space-y-2">
                {currentPack.reading_chunks.map((chunk, idx) => (
                  <div key={idx} className="p-3.5 bg-purple-50/40 rounded-xl border border-purple-100">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-purple-700 block mb-1">
                      {chunk.module_name}
                    </span>
                    <p className="text-xs text-slate-700 leading-relaxed font-sans">
                      {chunk.content_snippet}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Practice Checkpoints with Progressive Conceptual Guidance */}
          {currentPack.practice_items && currentPack.practice_items.length > 0 && (
            <div className="space-y-3 pt-2">
              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <HelpCircle className="w-3.5 h-3.5 text-amber-600" />
                Targeted Practice Checkpoints
              </h4>
              <div className="space-y-3">
                {currentPack.practice_items.map((item, idx) => {
                  const isRevealed = revealedHints[idx];
                  return (
                    <div key={idx} className="p-4 rounded-xl border border-slate-200 bg-white space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-xs font-semibold text-slate-900 leading-relaxed">
                          <strong className="text-indigo-600 mr-1.5">Q{idx + 1}.</strong> {item.question}
                        </p>
                        <button
                          onClick={() => toggleHint(idx)}
                          className="text-[11px] font-semibold text-amber-700 hover:text-amber-800 bg-amber-50 px-2.5 py-1 rounded-md shrink-0 flex items-center gap-1"
                        >
                          <Lightbulb className="w-3 h-3 text-amber-500" />
                          {isRevealed ? 'Hide Hint' : 'Show Hint'}
                        </button>
                      </div>

                      {isRevealed && (
                        <div className="p-2.5 bg-amber-50/70 rounded-lg border border-amber-200 text-xs text-amber-900 italic">
                          <strong>Conceptual Guidance:</strong> {item.conceptual_hint}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

