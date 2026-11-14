import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../api/auth';
import { StatCard } from '../components/common/StatCard';
import { MasteryRadarChart } from '../components/student/MasteryRadarChart';
import AssessmentTaker from '../components/student/AssessmentTaker';
import RemedialPackViewer from '../components/student/RemedialPackViewer';
import AssessmentReportView from '../components/common/AssessmentReportView';
import { 
  BookOpen, 
  GraduationCap, 
  Target, 
  AlertTriangle, 
  CheckCircle, 
  RefreshCw, 
  HelpCircle, 
  ShieldCheck,
  PlayCircle,
  Table,
  ArrowRight,
  Sparkles,
  Award,
  Layers
} from 'lucide-react';

export const StudentDashboard = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [activeTab, setActiveTab] = useState('OVERVIEW'); // 'OVERVIEW' | 'MATRIX' | 'REMEDIAL' | 'REPORT'
  const [selectedCourseQuestions, setSelectedCourseQuestions] = useState(null);
  const [selectedCourseTitle, setSelectedCourseTitle] = useState('');
  const [activeAssessmentCourse, setActiveAssessmentCourse] = useState(null); // { id, title, isPost: bool }
  const [selectedCourseId, setSelectedCourseId] = useState(null);
  const [studentMatrix, setStudentMatrix] = useState(null);
  const [studentReport, setStudentReport] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  const fetchDashboard = async () => {
    setIsLoading(true);
    setErrorMessage('');
    try {
      const data = await authApi.getStudentDashboard();
      setDashboardData(data);
      if (data.enrolled_courses?.length > 0 && !selectedCourseId) {
        setSelectedCourseId(data.enrolled_courses[0].id);
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Failed to load student assessment data.');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchPersonalMatrix = async (courseId) => {
    if (!courseId) return;
    try {
      const data = await authApi.getStudentMasteryMatrix(courseId);
      setStudentMatrix(data);
    } catch (err) {
      console.error('Failed to fetch personal mastery matrix', err);
    }
  };

  const fetchReport = async (courseId) => {
    if (!courseId) return;
    try {
      const data = await authApi.getStudentAssessmentReport(courseId);
      setStudentReport(data);
    } catch (err) {
      console.error('Failed to fetch assessment report', err);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  useEffect(() => {
    if (selectedCourseId) {
      fetchPersonalMatrix(selectedCourseId);
      fetchReport(selectedCourseId);
    }
  }, [selectedCourseId]);

  const handleInspectCourseQuestions = async (courseId, courseTitle) => {
    try {
      const questions = await authApi.getStudentCourseQuestions(courseId);
      setSelectedCourseQuestions(questions);
      setSelectedCourseTitle(courseTitle);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to fetch course questions.');
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mb-3" />
        <p className="text-sm font-medium text-slate-600">Retrieving Student Academic Profile...</p>
      </div>
    );
  }

  const selectedCourse = dashboardData?.enrolled_courses?.find(c => c.id === selectedCourseId) || dashboardData?.enrolled_courses?.[0];
  const foundationalCount = dashboardData?.mastery_breakdown?.filter(
    (m) => m.recommendation_type === 'FOUNDATIONAL'
  ).length || 0;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Student Profile Header */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 mb-2">
            <span className="w-2 h-2 rounded-full bg-indigo-600 animate-ping" />
            Active Student Session (60-Min Protected Lifetime)
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Hello, {dashboardData?.student_name || user?.full_name}
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Roll Number: <strong className="text-slate-700 font-mono">{dashboardData?.roll_number || 'N/A'}</strong> • {dashboardData?.department || 'Academic Department'}
          </p>
        </div>

        <button
          onClick={fetchDashboard}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors self-start md:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Profile
        </button>
      </div>

      {/* Active Assessment Execution Modal / View */}
      {activeAssessmentCourse && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <PlayCircle className="w-5 h-5 text-indigo-600" />
              {activeAssessmentCourse.isPost ? 'Taking Post-Assessment' : 'Taking Baseline Assessment'}: {activeAssessmentCourse.title}
            </h2>
            <button
              onClick={() => setActiveAssessmentCourse(null)}
              className="text-xs font-semibold text-slate-600 hover:text-slate-900 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 rounded-lg"
            >
              Exit Assessment
            </button>
          </div>
          <AssessmentTaker
            courseId={activeAssessmentCourse.id}
            courseTitle={activeAssessmentCourse.title}
            isPost={activeAssessmentCourse.isPost}
            onComplete={() => {
              fetchDashboard();
              if (selectedCourseId) {
                fetchPersonalMatrix(selectedCourseId);
                fetchReport(selectedCourseId);
              }
            }}
            onCancel={() => {
              setActiveAssessmentCourse(null);
              fetchDashboard();
              if (selectedCourseId) {
                fetchPersonalMatrix(selectedCourseId);
                fetchReport(selectedCourseId);
              }
            }}
          />
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          title="Overall Mastery Level"
          value={`${Math.round((dashboardData?.overall_mastery_average || 0) * 100)}%`}
          subtitle="Competency across all objectives"
          badge={dashboardData?.overall_mastery_average >= 0.75 ? 'Target Met (τ)' : 'In Progress'}
          icon={Target}
          color="blue"
        />
        <StatCard
          title="Enrolled Courses"
          value={dashboardData?.enrolled_courses?.length || 0}
          subtitle="Active academic modules"
          icon={BookOpen}
          color="purple"
        />
        <StatCard
          title="Foundational Gaps"
          value={foundationalCount}
          subtitle="Areas with Mastery < 30%"
          badge={foundationalCount > 0 ? 'Review Needed' : 'None'}
          icon={AlertTriangle}
          color={foundationalCount > 0 ? 'amber' : 'emerald'}
        />
        <StatCard
          title="Data Isolation"
          value="Enforced"
          subtitle="Model answers & rubrics protected"
          icon={ShieldCheck}
          color="emerald"
        />
      </div>

      {/* Course Context Selector */}
      {dashboardData?.enrolled_courses && dashboardData.enrolled_courses.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-3 shadow-sm flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider pl-2">
            Selected Course Context:
          </span>
          <select
            value={selectedCourseId || ''}
            onChange={(e) => setSelectedCourseId(e.target.value)}
            className="py-1.5 px-3 text-xs bg-slate-50 border border-slate-300 rounded-lg text-slate-800 font-semibold focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {dashboardData.enrolled_courses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.course_code}: {c.title}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Primary Navigation Tabs */}
      <div className="flex border-b border-slate-200 text-sm font-semibold gap-2">
        <button
          onClick={() => setActiveTab('OVERVIEW')}
          className={`pb-3 px-4 border-b-2 transition-all flex items-center gap-2 ${
            activeTab === 'OVERVIEW'
              ? 'border-indigo-600 text-indigo-700 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          Curriculum & Actions
        </button>

        <button
          onClick={() => setActiveTab('MATRIX')}
          className={`pb-3 px-4 border-b-2 transition-all flex items-center gap-2 ${
            activeTab === 'MATRIX'
              ? 'border-indigo-600 text-indigo-700 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Table className="w-4 h-4" />
          Mastery Matrix |O| × |T|
        </button>

        <button
          onClick={() => setActiveTab('REMEDIAL')}
          className={`pb-3 px-4 border-b-2 transition-all flex items-center gap-2 ${
            activeTab === 'REMEDIAL'
              ? 'border-indigo-600 text-indigo-700 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          Remedial Learning Packs
        </button>

        <button
          onClick={() => setActiveTab('REPORT')}
          className={`pb-3 px-4 border-b-2 transition-all flex items-center gap-2 ${
            activeTab === 'REPORT'
              ? 'border-indigo-600 text-indigo-700 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Award className="w-4 h-4" />
          Assessment & Gain Report
        </button>
      </div>

      {/* Tab 1: Curriculum & Actions */}
      {activeTab === 'OVERVIEW' && (
        <div className="space-y-8">
          {/* Radar Chart Section */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">
              Competency Radar Profile
            </h2>
            <MasteryRadarChart masteryItems={dashboardData?.mastery_breakdown} />
          </div>

          {/* Enrolled Courses & Quick Actions */}
          <div className="space-y-4">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-indigo-600" /> Enrolled Courses & Adaptive Progression
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {dashboardData?.enrolled_courses?.map((course) => (
                <div
                  key={course.id}
                  className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:border-indigo-300 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-mono font-bold text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded">
                        {course.course_code}
                      </span>
                      <span className="text-[11px] text-slate-400">Enrolled</span>
                    </div>
                    <h4 className="text-sm font-bold text-slate-900">
                      {course.title}
                    </h4>
                    <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                      {course.description}
                    </p>
                  </div>

                  <div className="mt-5 pt-3 border-t border-slate-100 flex flex-col gap-2">
                    <button
                      onClick={() => setActiveAssessmentCourse({ id: course.id, title: course.title, isPost: false })}
                      className="w-full text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white py-2 rounded-lg transition-colors flex items-center justify-center gap-1.5 shadow-sm"
                    >
                      <PlayCircle className="w-4 h-4" /> Attempt Baseline Assessment
                    </button>
                    <button
                      onClick={() => {
                        setSelectedCourseId(course.id);
                        setActiveTab('REMEDIAL');
                      }}
                      className="w-full text-xs font-semibold bg-amber-50 hover:bg-amber-100 text-amber-800 py-1.5 rounded-lg transition-colors flex items-center justify-center gap-1.5"
                    >
                      <Sparkles className="w-3.5 h-3.5 text-amber-600" /> View Remedial Learning Packs
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Mastery Matrix */}
      {activeTab === 'MATRIX' && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded text-xs font-bold uppercase tracking-wider bg-indigo-50 text-indigo-700">
                  Personal Mastery Matrix |O| × |T|
                </span>
                <span className="text-xs text-slate-500 font-mono">
                  M(o,t) = (1 + Σ wᵢ fᵢ) / (2 + Σ wᵢ)
                </span>
              </div>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight mt-1">
                Your Objective-Trait Mastery Breakdown
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Private and personalized to you. Demonstrates competencies across learning objectives and traits.
              </p>
            </div>
          </div>

          {studentMatrix?.matrix && studentMatrix.matrix.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200">
                    <th className="py-3 px-4 font-bold text-slate-600 uppercase tracking-wider w-64">
                      Course Objective
                    </th>
                    {(studentMatrix.matrix[0]?.traits || []).map((tr) => (
                      <th key={tr.trait_id} className="py-3 px-4 font-bold text-slate-600 uppercase tracking-wider text-center">
                        <div>{tr.trait_name}</div>
                        <span className="text-[10px] text-slate-400 font-mono">{tr.trait_code}</span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {studentMatrix.matrix.map((row) => (
                    <tr key={row.objective_id} className="hover:bg-slate-50/50">
                      <td className="py-3.5 px-4">
                        <span className="font-bold font-mono text-slate-900 mr-1.5">{row.objective_code}:</span>
                        <span className="text-slate-600">{row.objective_description}</span>
                      </td>
                      {row.traits.map((cell) => {
                        const m = cell.mastery_value;
                        let color = 'bg-rose-50 text-rose-800 border-rose-200';
                        if (m >= studentMatrix.tau_threshold) {
                          color = 'bg-emerald-50 text-emerald-800 border-emerald-200';
                        } else if (m >= 0.30) {
                          color = 'bg-amber-50 text-amber-800 border-amber-200';
                        }
                        return (
                          <td key={cell.trait_id} className="py-3 px-3 text-center align-middle">
                            <div className={`p-2 rounded-lg border font-mono font-bold ${color}`}>
                              <div>{(m * 100).toFixed(1)}%</div>
                              <span className="text-[9px] font-sans font-medium uppercase opacity-75 block mt-0.5">
                                {cell.recommendation_type}
                              </span>
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-xs text-slate-500 text-center py-6">
              No mastery records recorded yet for this course. Attempt the assessment to generate your matrix!
            </p>
          )}
        </div>
      )}

      {/* Tab 3: Remedial Learning Packs */}
      {activeTab === 'REMEDIAL' && (
        <RemedialPackViewer
          courseId={selectedCourse?.id || ''}
          courseTitle={`${selectedCourse?.course_code}: ${selectedCourse?.title}`}
          onStartPostAssessment={() => {
            setActiveAssessmentCourse({
              id: selectedCourse?.id,
              title: selectedCourse?.title,
              isPost: true
            });
          }}
        />
      )}

      {/* Tab 4: Assessment & Gain Report */}
      {activeTab === 'REPORT' && (
        <AssessmentReportView report={studentReport} isFaculty={false} />
      )}

      {/* Published Questions Preview Modal */}
      {selectedCourseQuestions && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[85vh] overflow-hidden flex flex-col shadow-2xl">
            <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div>
                <h4 className="text-base font-bold text-slate-900">{selectedCourseTitle}</h4>
                <p className="text-xs text-emerald-700 font-medium flex items-center gap-1 mt-0.5">
                  <ShieldCheck className="w-3.5 h-3.5" /> Student Privacy Shield Active: Rubrics and Model Answers Stripped
                </p>
              </div>
              <button
                onClick={() => setSelectedCourseQuestions(null)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold px-2 py-1"
              >
                ✕
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4">
              {selectedCourseQuestions.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-6">No published questions yet for this course.</p>
              ) : (
                selectedCourseQuestions.map((q) => (
                  <div key={q.id} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-indigo-100 text-indigo-800">
                        {q.objective_code}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-slate-900">{q.prompt}</p>
                    {q.hint1 && (
                      <div className="text-xs text-slate-600 bg-white p-2.5 rounded-lg border border-slate-200">
                        <strong>Available Hint 1:</strong> {q.hint1}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>

            <div className="p-4 border-t border-slate-200 bg-slate-50 text-right">
              <button
                onClick={() => setSelectedCourseQuestions(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold rounded-xl"
              >
                Close View
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
