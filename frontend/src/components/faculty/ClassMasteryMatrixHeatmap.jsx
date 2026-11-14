import React, { useState, useEffect } from 'react';
import { 
  Grid, 
  Sliders, 
  Users, 
  AlertTriangle, 
  CheckCircle2, 
  HelpCircle, 
  Layers,
  ChevronDown,
  Info
} from 'lucide-react';
import { authApi } from '../../api/auth';

export default function ClassMasteryMatrixHeatmap({ courseId, courseCode, courseTitle }) {
  const [loading, setLoading] = useState(true);
  const [matrixData, setMatrixData] = useState(null);
  const [tau, setTau] = useState(0.75);
  const [error, setError] = useState(null);
  const [selectedCell, setSelectedCell] = useState(null);

  useEffect(() => {
    if (courseId) {
      loadMatrix();
    }
  }, [courseId, tau]);

  const loadMatrix = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await authApi.getClassMasteryMatrix(courseId, tau);
      setMatrixData(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch class mastery matrix.');
    } finally {
      setLoading(false);
    }
  };

  const getCellColor = (meanMastery) => {
    if (meanMastery >= tau) {
      return 'bg-emerald-100 text-emerald-900 border-emerald-300 hover:bg-emerald-200';
    }
    if (meanMastery >= 0.30) {
      return 'bg-amber-100 text-amber-900 border-amber-300 hover:bg-amber-200';
    }
    return 'bg-rose-100 text-rose-900 border-rose-300 hover:bg-rose-200';
  };

  const getBadgeColor = (meanMastery) => {
    if (meanMastery >= tau) return 'bg-emerald-600 text-white';
    if (meanMastery >= 0.30) return 'bg-amber-600 text-white';
    return 'bg-rose-600 text-white';
  };

  if (loading && !matrixData) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-indigo-600 border-t-transparent mb-4"></div>
        <p className="text-slate-600 font-medium">Aggregating cohort mastery scores...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-50 border border-rose-200 rounded-xl p-6 text-center">
        <p className="text-rose-700 font-medium">{error}</p>
        <button
          onClick={loadMatrix}
          className="mt-3 px-4 py-1.5 bg-rose-600 text-white rounded-lg text-xs font-semibold hover:bg-rose-700"
        >
          Retry
        </button>
      </div>
    );
  }

  const rows = matrixData?.matrix || [];
  const traitsList = rows.length > 0 ? (rows[0].traits || []) : [];

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header and Controls */}
      <div className="p-6 border-b border-slate-200">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded text-xs font-bold uppercase tracking-wider bg-indigo-50 text-indigo-700 border border-indigo-200">
                Authorized Class Analytics
              </span>
              <span className="text-xs text-slate-500 font-medium flex items-center gap-1">
                <Users className="w-3.5 h-3.5" />
                {matrixData?.total_enrolled_students || 0} Enrolled Students
              </span>
            </div>
            <h2 className="text-xl font-bold text-slate-900 mt-1">
              Class-Level Mastery Matrix <span className="font-mono text-indigo-600 font-normal">|O| × |T|</span>
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Aggregated Bayesian smoothed mastery scores across learning objectives and assessment traits.
            </p>
          </div>

          {/* Configurable Tau Threshold */}
          <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 flex items-center gap-4">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700">
              <Sliders className="w-4 h-4 text-indigo-600" />
              Target Mastery Threshold (τ):
            </div>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min="0.50"
                max="0.95"
                step="0.05"
                value={tau}
                onChange={(e) => setTau(parseFloat(e.target.value))}
                className="w-24 accent-indigo-600"
              />
              <span className="text-xs font-mono font-bold bg-white px-2 py-0.5 rounded border border-slate-300 text-slate-800">
                {(tau * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="mt-4 pt-4 border-t border-slate-100 flex flex-wrap items-center gap-4 text-xs">
          <span className="font-semibold text-slate-500 uppercase tracking-wider text-[10px]">Cohort Status:</span>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-emerald-500" />
            <span className="text-slate-700">Target Achieved (M ≥ {(tau * 100).toFixed(0)}%)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-amber-500" />
            <span className="text-slate-700">Reinforcement Zone (30% ≤ M &lt; {(tau * 100).toFixed(0)}%)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-rose-500" />
            <span className="text-slate-700">Foundational Alert (M &lt; 30%)</span>
          </div>
        </div>
      </div>

      {/* Heatmap Grid */}
      <div className="p-6 overflow-x-auto">
        {rows.length === 0 ? (
          <div className="text-center py-12 text-slate-500 text-sm">
            No assessment data recorded yet for this course.
          </div>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="py-3 px-4 text-xs font-bold text-slate-500 uppercase tracking-wider w-64 bg-slate-50 rounded-tl-lg">
                  Course Objective
                </th>
                {traitsList.map((tr) => (
                  <th key={tr.trait_id} className="py-3 px-4 text-xs font-bold text-slate-600 uppercase tracking-wider text-center bg-slate-50">
                    <div>{tr.trait_name}</div>
                    <span className="text-[10px] text-slate-400 font-mono font-normal">{tr.trait_code}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {rows.map((row) => (
                <tr key={row.objective_id} className="hover:bg-slate-50/50 transition-colors">
                  {/* Objective Column */}
                  <td className="py-4 px-4 align-top">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-bold text-slate-900 font-mono text-xs px-2 py-0.5 bg-slate-100 rounded">
                        {row.objective_code}
                      </span>
                      <span className="text-[10px] text-slate-500 font-semibold uppercase">
                        Weight: {row.priority_weight}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 line-clamp-2">
                      {row.objective_description}
                    </p>
                  </td>

                  {/* Trait Matrix Cells */}
                  {row.traits.map((cell) => {
                    const colorClass = getCellColor(cell.mean_mastery);
                    const isSelected = selectedCell?.objective_code === row.objective_code && selectedCell?.trait_code === cell.trait_code;
                    return (
                      <td key={cell.trait_id} className="py-3 px-3 text-center align-middle">
                        <button
                          onClick={() => setSelectedCell({
                            objective_code: row.objective_code,
                            objective_desc: row.objective_description,
                            priority_weight: row.priority_weight,
                            trait_name: cell.trait_name,
                            trait_code: cell.trait_code,
                            ...cell
                          })}
                          className={`w-full py-3 px-2 rounded-lg border text-center transition-all shadow-sm ${colorClass} ${
                            isSelected ? 'ring-2 ring-indigo-600 scale-105' : ''
                          }`}
                        >
                          <div className="text-base font-bold font-mono">
                            {(cell.mean_mastery * 100).toFixed(1)}%
                          </div>
                          <div className="text-[10px] opacity-80 mt-0.5">
                            {cell.students_with_gaps > 0 ? (
                              <span className="font-semibold text-rose-700">
                                {cell.students_with_gaps} gaps
                              </span>
                            ) : (
                              <span>Optimal</span>
                            )}
                          </div>
                        </button>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Selected Cell Drill-Down Drawer */}
      {selectedCell && (
        <div className="border-t border-slate-200 bg-slate-50 p-6">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 bg-indigo-100 text-indigo-800 text-xs font-bold rounded">
                  {selectedCell.objective_code}
                </span>
                <span className="text-xs font-semibold text-slate-500">×</span>
                <span className="px-2 py-0.5 bg-slate-200 text-slate-800 text-xs font-bold rounded">
                  {selectedCell.trait_name}
                </span>
              </div>
              <p className="text-xs text-slate-600 mt-1 max-w-xl">
                {selectedCell.objective_desc}
              </p>
            </div>
            <button
              onClick={() => setSelectedCell(null)}
              className="text-xs font-semibold text-slate-500 hover:text-slate-800"
            >
              Close Details ✕
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-4">
            <div className="bg-white p-3 rounded-lg border border-slate-200">
              <span className="text-[10px] text-slate-500 uppercase font-bold">Cohort Mean</span>
              <div className="text-lg font-bold font-mono text-slate-900 mt-0.5">
                {(selectedCell.mean_mastery * 100).toFixed(1)}%
              </div>
            </div>

            <div className="bg-white p-3 rounded-lg border border-slate-200">
              <span className="text-[10px] text-slate-500 uppercase font-bold">Min Mastery</span>
              <div className="text-lg font-bold font-mono text-slate-900 mt-0.5">
                {(selectedCell.min_mastery * 100).toFixed(1)}%
              </div>
            </div>

            <div className="bg-white p-3 rounded-lg border border-slate-200">
              <span className="text-[10px] text-slate-500 uppercase font-bold">Max Mastery</span>
              <div className="text-lg font-bold font-mono text-slate-900 mt-0.5">
                {(selectedCell.max_mastery * 100).toFixed(1)}%
              </div>
            </div>

            <div className="bg-white p-3 rounded-lg border border-slate-200">
              <span className="text-[10px] text-slate-500 uppercase font-bold">Students with Gaps</span>
              <div className="text-lg font-bold font-mono text-amber-600 mt-0.5">
                {selectedCell.students_with_gaps}
              </div>
            </div>

            <div className="bg-white p-3 rounded-lg border border-slate-200">
              <span className="text-[10px] text-slate-500 uppercase font-bold">Foundational Alerts</span>
              <div className="text-lg font-bold font-mono text-rose-600 mt-0.5">
                {selectedCell.foundational_remedial_count}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

