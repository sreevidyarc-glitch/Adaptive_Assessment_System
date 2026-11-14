import React from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';

export const MasteryRadarChart = ({ masteryItems }) => {
  if (!masteryItems || masteryItems.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-slate-400 text-sm">
        No assessment mastery data recorded yet.
      </div>
    );
  }

  // Format data for Radar Chart
  const radarData = masteryItems.map((item) => ({
    subject: `${item.objective_code}`,
    mastery: Math.round(item.mastery_value * 100),
    gap: Math.round(item.gap_score * 100),
    fullMark: 100,
  }));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-center">
      {/* Radar Chart */}
      <div className="h-72 w-full">
        <h4 className="text-xs font-semibold uppercase text-slate-500 mb-2 tracking-wider text-center">
          Objective Competency Radar (0 - 100%)
        </h4>
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
            <PolarGrid stroke="#e2e8f0" />
            <PolarAngleAxis dataKey="subject" tick={{ fill: '#475569', fontSize: 12 }} />
            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 10 }} />
            <Radar
              name="Mastery Level"
              dataKey="mastery"
              stroke="#0284c7"
              fill="#0284c7"
              fillOpacity={0.4}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Bar Chart */}
      <div className="h-72 w-full">
        <h4 className="text-xs font-semibold uppercase text-slate-500 mb-2 tracking-wider text-center">
          Objective vs Target Mastery Threshold (τ = 75%)
        </h4>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={radarData} margin={{ top: 10, right: 20, left: -10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis dataKey="subject" tick={{ fill: '#64748b', fontSize: 12 }} />
            <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 12 }} />
            <Tooltip
              formatter={(value) => [`${value}%`, 'Score']}
              contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
            />
            <Bar dataKey="mastery" fill="#0284c7" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

