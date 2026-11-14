import React from 'react';
import { 
  Award, 
  TrendingUp, 
  CheckCircle2, 
  AlertTriangle, 
  ArrowUpRight, 
  ArrowDownRight, 
  BarChart2, 
  Users, 
  Sparkles,
  BookOpen,
  Calendar,
  ShieldCheck
} from 'lucide-react';

export default function AssessmentReportView({ report, isFaculty = false }) {
  if (!report) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-500 text-sm">
        No assessment report available yet. Complete both pre-assessment and post-assessment to view full analytics.
      </div>
    );
  }

  const getGainBadge = (category) => {
    switch (category) {
      case 'HIGH':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'MEDIUM':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'LOW':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      case 'PERFECT_BASELINE':
        return 'bg-indigo-100 text-indigo-800 border-indigo-300';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-300';
    }
  };

  // Student Assessment Report View
  if (!isFaculty) {
    const gain = report.gain;
    return (
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden space-y-6">
        {/* Header */}
        <div className="bg-gradient-to-r from-slate-900 to-indigo-950 text-white p-6 md:p-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider bg-indigo-500/30 text-indigo-200 border border-indigo-400/30">
                Official Academic Assessment Report
              </span>
              <span className="text-xs text-slate-400 font-mono">
                {report.report_id}
              </span>
            </div>
            <h2 className="text-2xl font-bold">{report.student_name}</h2>
            <p className="text-xs text-slate-300 mt-1">
              Roll No: <span className="font-mono font-semibold">{report.roll_number || 'N/A'}</span> • {report.course_code}: {report.course_title}
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs text-emerald-400 font-medium bg-white/10 px-3 py-1.5 rounded-lg backdrop-blur-sm self-start md:self-auto">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Verified Authenticity & Privacy Shield
          </div>
        </div>

        {/* Normalized Learning Gain Banner */}
        <div className="px-6 md:px-8">
          <div className="p-6 bg-slate-50 rounded-2xl border border-slate-200 grid grid-cols-1 md:grid-cols-4 gap-6 items-center">
            {/* Pre Score */}
            <div className="text-center md:text-left">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                Baseline Pre-Score
              </span>
              <div className="text-2xl font-bold font-mono text-slate-800 mt-1">
                {(report.pre_score * 100).toFixed(1)}%
              </div>
              <span className="text-[11px] text-slate-400">Prior Assessment</span>
            </div>

            {/* Post Score */}
            <div className="text-center md:text-left">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                Remediated Post-Score
              </span>
              <div className="text-2xl font-bold font-mono text-emerald-700 mt-1">
                {report.post_score !== null ? `${(report.post_score * 100).toFixed(1)}%` : 'Pending'}
              </div>
              <span className="text-[11px] text-slate-400">Post-Scaffolding</span>
            </div>

            {/* Normalized Gain g */}
            <div className="text-center md:text-left">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                Normalized Gain (g)
              </span>
              <div className="text-2xl font-bold font-mono text-indigo-700 mt-1">
                {gain?.normalized_gain !== null && gain?.normalized_gain !== undefined
                  ? gain.normalized_gain.toFixed(2)
                  : 'N/A'}
              </div>
              <span className="text-[10px] font-mono text-slate-400">g = (Post - Pre)/(1 - Pre)</span>
            </div>

            {/* Gain Category Badge */}
            <div className="text-center md:text-right">
              {gain ? (
                <div className="inline-block text-left">
                  <span className={`px-3 py-1 rounded-full text-xs font-bold border uppercase inline-block ${getGainBadge(gain.gain_category)}`}>
                    {gain.gain_category} GAIN
                  </span>
                  <p className="text-[11px] text-slate-500 mt-1 max-w-xs">
                    {gain.interpretation}
                  </p>
                </div>
              ) : (
                <span className="text-xs text-slate-400 italic">Complete post-assessment to compute gain</span>
              )}
            </div>
          </div>
        </div>

        {/* Gap Resolution Summary */}
        <div className="px-6 md:px-8 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-200 flex items-center justify-between">
            <div>
              <span className="text-xs font-bold uppercase text-emerald-800">Resolved Objectives</span>
              <div className="text-2xl font-bold font-mono text-emerald-900 mt-0.5">
                {report.resolved_gaps_count}
              </div>
            </div>
            <CheckCircle2 className="w-8 h-8 text-emerald-600 opacity-80" />
          </div>

          <div className="p-4 bg-indigo-50 rounded-xl border border-indigo-200 flex items-center justify-between">
            <div>
              <span className="text-xs font-bold uppercase text-indigo-800">Remedial Packs Completed</span>
              <div className="text-2xl font-bold font-mono text-indigo-900 mt-0.5">
                {report.remedial_packs_completed} / {report.total_remedial_packs}
              </div>
            </div>
            <BookOpen className="w-8 h-8 text-indigo-600 opacity-80" />
          </div>
        </div>

        {/* Mastery Progression Table */}
        <div className="px-6 md:px-8 pb-8">
          <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-indigo-600" />
            Objective Mastery Progression (Pre vs Post Remediation)
          </h3>

          <div className="overflow-x-auto border border-slate-200 rounded-xl">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
                  <th className="py-3 px-4">Objective</th>
                  <th className="py-3 px-4">Trait</th>
                  <th className="py-3 px-4 text-center">Baseline M(o,t)</th>
                  <th className="py-3 px-4 text-center">Remediated M(o,t)</th>
                  <th className="py-3 px-4 text-center">Progression (Δ)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {report.mastery_progression?.map((item, idx) => {
                  const isPositive = item.delta >= 0;
                  return (
                    <tr key={idx} className="hover:bg-slate-50/60">
                      <td className="py-3 px-4">
                        <span className="font-bold font-mono text-slate-900 mr-1.5">{item.objective_code}</span>
                        <span className="text-slate-600">{item.objective_description}</span>
                      </td>
                      <td className="py-3 px-4 font-medium text-slate-700">
                        {item.trait_name}
                      </td>
                      <td className="py-3 px-4 text-center font-mono">
                        {(item.pre_mastery * 100).toFixed(1)}%
                      </td>
                      <td className="py-3 px-4 text-center font-mono font-bold text-slate-900">
                        {(item.post_mastery * 100).toFixed(1)}%
                      </td>
                      <td className="py-3 px-4 text-center font-mono">
                        <span className={`inline-flex items-center gap-0.5 font-bold ${
                          isPositive ? 'text-emerald-600' : 'text-rose-600'
                        }`}>
                          {isPositive ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                          {(item.delta * 100).toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }

  // Faculty Assessment Report View
  const dist = report.gain_distribution || {};
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden space-y-6">
      {/* Faculty Report Header */}
      <div className="bg-gradient-to-r from-purple-900 to-slate-900 text-white p-6 md:p-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2.5 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider bg-purple-500/30 text-purple-200 border border-purple-400/30">
              Class-Level Cohort Report
            </span>
            <span className="text-xs text-slate-400 font-mono">
              {report.course_code}
            </span>
          </div>
          <h2 className="text-2xl font-bold">{report.course_title}</h2>
          <p className="text-xs text-slate-300 mt-1">
            Enrolled Students: <strong>{report.total_enrolled_students}</strong> • Pre-Completed: {report.completed_pre_count} • Post-Completed: {report.completed_post_count}
          </p>
        </div>

        <div className="text-right">
          <span className="text-[10px] text-purple-200 uppercase font-bold tracking-wider block">Cohort Average Gain</span>
          <div className="text-3xl font-bold font-mono text-emerald-400 mt-0.5">
            {report.cohort_normalized_gain_average !== null && report.cohort_normalized_gain_average !== undefined
              ? report.cohort_normalized_gain_average.toFixed(2)
              : 'N/A'}
          </div>
        </div>
      </div>

      {/* Cohort Averages */}
      <div className="px-6 md:px-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Cohort Pre-Average</span>
          <div className="text-2xl font-bold font-mono text-slate-900 mt-1">
            {(report.cohort_pre_average * 100).toFixed(1)}%
          </div>
        </div>

        <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Cohort Post-Average</span>
          <div className="text-2xl font-bold font-mono text-emerald-700 mt-1">
            {(report.cohort_post_average * 100).toFixed(1)}%
          </div>
        </div>

        <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Gap Resolution Rate</span>
          <div className="text-2xl font-bold font-mono text-indigo-700 mt-1">
            {report.gap_resolution_percentage}%
          </div>
        </div>

        <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Resolved Competencies</span>
          <div className="text-2xl font-bold font-mono text-slate-900 mt-1">
            {report.total_resolved_gaps} / {report.total_initial_gaps + report.total_resolved_gaps}
          </div>
        </div>
      </div>

      {/* Normalized Gain Distribution */}
      <div className="px-6 md:px-8 pb-8 space-y-3">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <BarChart2 className="w-4 h-4 text-purple-600" />
          Normalized Learning Gain Distribution (Cohort Categorization)
        </h3>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-200 text-center">
            <span className="text-[10px] font-bold uppercase text-emerald-800">High Gain (g ≥ 0.70)</span>
            <div className="text-2xl font-bold font-mono text-emerald-900 mt-1">
              {dist.high_gain_count || 0}
            </div>
            <span className="text-[11px] text-emerald-700">Students</span>
          </div>

          <div className="p-4 bg-amber-50 rounded-xl border border-amber-200 text-center">
            <span className="text-[10px] font-bold uppercase text-amber-800">Medium Gain (0.3 - 0.7)</span>
            <div className="text-2xl font-bold font-mono text-amber-900 mt-1">
              {dist.medium_gain_count || 0}
            </div>
            <span className="text-[11px] text-amber-700">Students</span>
          </div>

          <div className="p-4 bg-rose-50 rounded-xl border border-rose-200 text-center">
            <span className="text-[10px] font-bold uppercase text-rose-800">Low Gain (g &lt; 0.30)</span>
            <div className="text-2xl font-bold font-mono text-rose-900 mt-1">
              {dist.low_gain_count || 0}
            </div>
            <span className="text-[11px] text-rose-700">Students</span>
          </div>

          <div className="p-4 bg-indigo-50 rounded-xl border border-indigo-200 text-center">
            <span className="text-[10px] font-bold uppercase text-indigo-800">Perfect Baseline (Pre=1)</span>
            <div className="text-2xl font-bold font-mono text-indigo-900 mt-1">
              {dist.perfect_baseline_count || 0}
            </div>
            <span className="text-[11px] text-indigo-700">Students</span>
          </div>
        </div>
      </div>
    </div>
  );
}

